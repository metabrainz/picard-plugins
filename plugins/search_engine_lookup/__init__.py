# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Bob Swift (rdswift)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

PLUGIN_NAME = 'Search Engine Lookup'
PLUGIN_AUTHOR = 'Bob Swift'
PLUGIN_DESCRIPTION = '''Adds a right click option on a cluster to look up album information using a search engine in a browser window.'''
PLUGIN_VERSION = '2.0.1'
PLUGIN_API_VERSIONS = ['2.0', '2.1', '2.2', '2.3']
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.txt"

import re
from urllib.parse import quote_plus
from uuid import uuid4

from PyQt5 import QtCore, QtWidgets

from picard import config, log
from picard.cluster import Cluster
from picard.plugins.search_engine_lookup.ui_options_search_engine_editor import Ui_SearchEngineEditorDialog
from picard.plugins.search_engine_lookup.ui_options_search_engine_lookup import Ui_SearchEngineLookupOptionsPage
from picard.ui.itemviews import BaseAction, register_cluster_action
from picard.ui.options import OptionsPage, register_options_page
from picard.util.webbrowser2 import open as _open

DEFAULT_PROVIDERS = {
    'ea520f49-36bc-4821-a16a-38bf0340d1f3': {'name': _('Google'), 'url': r'https://www.google.com/search?q=%search%'},
    '7b93d4b5-34d9-49a7-901c-ed0914f07aee': {'name': _('Bing'), 'url': r'https://www.bing.com/search?q=%search%'},
    '37be75d9-5fc5-4858-87fc-b5db0896a163': {'name': _('DuckDuckGo'), 'url': r'https://duckduckgo.com/?q=%search%'},
}

DEFAULT_PROVIDER = 'ea520f49-36bc-4821-a16a-38bf0340d1f3'
DEFAULT_EXTRA_WORDS = 'album'

RE_VALIDATE_TITLE = re.compile(r'^[^\s"|][^"|]*[^\s"|]$')
RE_VALIDATE_URL = re.compile(r'^[^\s"]*%search%[^\s"]*$')

KEY_PROVIDER = 'search_engine_lookup_provider'
KEY_PROVIDERS = 'search_engine_lookup_providers'
KEY_EXTRA = 'search_engine_lookup_extra_words'


class SearchEngineLookupTest(BaseAction):
    NAME = 'Search engine lookup'

    def callback(self, cluster_list):
        extra = config.setting[KEY_EXTRA].split()
        provider = config.setting[KEY_PROVIDER]
        providers = config.setting[KEY_PROVIDERS]
        base_url = providers[provider]['url'] if provider in providers else DEFAULT_PROVIDERS[DEFAULT_PROVIDER]['url']
        for cluster in cluster_list:
            if isinstance(cluster, Cluster):
                parts = []
                if 'albumartist' in cluster.metadata and cluster.metadata['albumartist']:
                    parts.extend(cluster.metadata['albumartist'].split())
                if 'album' in cluster.metadata and cluster.metadata['albumartist']:
                    parts.extend(cluster.metadata['album'].split())
                if parts:
                    if extra:
                        parts.extend(extra)
                    url = base_url.replace(r'%search%', quote_plus(' '.join(parts)))
                    log.debug("{0}: Looking up {1}".format(PLUGIN_NAME, url,))
                    _open(url)
                else:
                    log.error("{0}: No existing metadata to lookup.".format(PLUGIN_NAME,))
                    show_popup(_('Lookup Error'), _('There is no existing data to use for a search.'))
            else:
                log.error("{0}: Argument is not a cluster. {1}".format(PLUGIN_NAME, cluster,))
                show_popup(_('Lookup Error'), _('There was a problem with the information provided for the cluster.'))


def show_popup(title='', content='', window=None):
    QtWidgets.QMessageBox.information(
        window,
        title,
        content,
        QtWidgets.QMessageBox.Ok,
        QtWidgets.QMessageBox.Ok
    )


class SearchEngineEditDialog(QtWidgets.QDialog):

    def __init__(self, parent=None, edit_provider='', edit_url='', titles=None):
        super().__init__(parent)
        self.parent = parent
        self.output = None
        self.edit_provider = edit_provider
        self.edit_url = edit_url
        self.providers = titles if titles else []

        self.valid_no = QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.SP_DialogCancelButton).pixmap(16, 16)
        self.valid_yes = QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.SP_DialogApplyButton).pixmap(16, 16)

        self.ui = Ui_SearchEngineEditorDialog()
        self.ui.setupUi(self)
        self.ui.le_title.setText(self.edit_provider)
        self.ui.le_url.setText(self.edit_url)

        self.setup_actions()
        self.check_validation()

    def setup_actions(self):
        self.ui.le_title.textChanged.connect(self.title_text_changed)
        self.ui.le_url.textChanged.connect(self.url_text_changed)
        self.ui.pb_save.clicked.connect(self.accept)
        self.ui.pb_cancel.clicked.connect(self.reject)

    def check_validation(self):
        valid_title = re.match(RE_VALIDATE_TITLE, self.edit_provider) and self.edit_provider not in self.providers
        self.ui.img_valid_title.setPixmap(self.valid_yes if valid_title else self.valid_no)

        valid_url = re.match(RE_VALIDATE_URL, self.edit_url)
        self.ui.img_valid_url.setPixmap(self.valid_yes if valid_url else self.valid_no)

        # Note that this needs to be forced to a bool to avoid Qt crashing Picard
        self.ui.pb_save.setEnabled(bool(valid_title and valid_url))

    def get_output(self):
        return self.output

    def accept(self):
        self.output = (self.edit_provider.strip(), self.edit_url.strip())
        super().accept()

    def title_text_changed(self, text):
        self.edit_provider = text
        self.check_validation()

    def url_text_changed(self, text):
        self.edit_url = text
        self.check_validation()


class SearchEngineLookupOptionsPage(OptionsPage):

    NAME = "search_engine_lookup_options"
    TITLE = "Search Engine Lookup"
    PARENT = "plugins"
    HELP_URL = "https://github.com/metabrainz/picard-plugins/blob/2.0/plugins/search_engine_lookup/README.md"

    options = [
        config.Option("setting", KEY_PROVIDERS, DEFAULT_PROVIDERS.copy()),
        config.TextOption("setting", KEY_PROVIDER, DEFAULT_PROVIDER),
        config.TextOption("setting", KEY_EXTRA, DEFAULT_EXTRA_WORDS),
    ]

    def __init__(self, parent=None):
        super(SearchEngineLookupOptionsPage, self).__init__(parent)
        self.ui = Ui_SearchEngineLookupOptionsPage()
        self.ui.setupUi(self)
        self.setup_actions()
        self.provider = ''
        self.providers = {}
        self.additional_words = ''

    def setup_actions(self):
        self.ui.list_providers.itemChanged.connect(self.select_provider)
        self.ui.pb_add.clicked.connect(self.add_provider)
        self.ui.pb_edit.clicked.connect(self.edit_provider)
        self.ui.pb_delete.clicked.connect(self.delete_provider)
        self.ui.pb_test.clicked.connect(self.test_provider)

    def load(self):
        # Settings for search engine providers
        self.providers = config.setting[KEY_PROVIDERS] or DEFAULT_PROVIDERS.copy()

        # Settings for search engine provider
        self.provider = config.setting[KEY_PROVIDER]
        if self.provider not in self.providers:
            # Assign an arbitrary valid value to self.provider
            self.provider = list(self.providers)[0]

        # Settings for search extra words
        self.additional_words = config.setting[KEY_EXTRA]
        self.ui.le_additional_words.setText(self.additional_words)

        # Display list of providers
        self.update_list()

    def select_provider(self, list_item):
        if list_item.checkState() == QtCore.Qt.Checked:
            # New provider selected
            self.provider = list_item.data(QtCore.Qt.UserRole)
            self.update_list(current_item=self.provider)
        else:
            # Attempt to deselect the current provider leaving none selected
            list_item.setCheckState(QtCore.Qt.Checked)

    def add_provider(self):
        provider_id = uuid4()
        self.edit_provider_dialog(provider_id)

    def edit_provider(self):
        current_item = self.ui.list_providers.currentItem()
        provider = current_item.text()
        provider_id = current_item.data(QtCore.Qt.UserRole)
        url = self.providers[provider_id]['url']
        self.edit_provider_dialog(provider_id, provider, url)

    def edit_provider_dialog(self, provider_id='', provider='', url=''):
        # List of titles currently used and not allowed.  Omit current title from the list when editing.
        titles = [x['name'] for x in self.providers.values() if x['name'] != provider]
        dialog = SearchEngineEditDialog(self, provider, url, titles)
        temp = dialog.exec_()
        if temp == QtWidgets.QDialog.Accepted:
            data = dialog.get_output()
            if data:
                new_provider, new_url = data
                self.providers[provider_id] = {'name': new_provider, 'url': new_url}
                self.update_list(provider_id)

    def delete_provider(self):
        current_item = self.ui.list_providers.currentItem()
        provider = current_item.text()
        provider_id = current_item.data(QtCore.Qt.UserRole)
        if current_item.checkState() or provider_id == self.provider:
            QtWidgets.QMessageBox.critical(
                self,
                _('Deletion Error'),
                _('You cannot delete the currently selected search provider.'),
                QtWidgets.QMessageBox.Ok,
                QtWidgets.QMessageBox.Ok
            )
        else:
            if QtWidgets.QMessageBox.warning(
                self,
                _('Confirm Deletion'),
                _('You are about to permanently delete the search provider "{provider_name}".  Continue?').format(provider_name=provider),
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel,
                QtWidgets.QMessageBox.Cancel
            ) == QtWidgets.QMessageBox.Ok:
                self.providers.pop(provider_id, None)
                self.update_list()

    def test_provider(self):
        current_item = self.ui.list_providers.currentItem()
        parts = ('The Beatles Abby Road ' + self.additional_words).strip().split()
        url = self.providers[current_item.data(QtCore.Qt.UserRole)]['url'].replace(r'%search%', quote_plus(' '.join(parts)))
        _open(url)

    def update_list(self, current_item=None):
        current_row = -1
        self.ui.list_providers.clear()
        for counter, provider_id in enumerate(self.providers):
            item = QtWidgets.QListWidgetItem()
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setText(self.providers[provider_id]['name'])
            item.setCheckState(QtCore.Qt.Checked if provider_id == self.provider else QtCore.Qt.Unchecked)
            item.setData(QtCore.Qt.UserRole, provider_id)
            self.ui.list_providers.addItem(item)
            if current_item and provider_id == current_item:
                current_row = counter
        current_row = max(current_row, 0)
        self.ui.list_providers.setCurrentRow(current_row)
        self.ui.list_providers.sortItems()

    def save(self):
        self._set_settings(config.setting)

    def _set_settings(self, settings):
        settings[KEY_PROVIDER] = self.provider.strip()
        settings[KEY_EXTRA] = self.additional_words.strip()
        settings[KEY_PROVIDERS] = self.providers or DEFAULT_PROVIDERS.copy()


register_cluster_action(SearchEngineLookupTest())
register_options_page(SearchEngineLookupOptionsPage)
