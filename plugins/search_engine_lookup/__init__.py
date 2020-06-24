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
PLUGIN_VERSION = '1.0.0'
PLUGIN_API_VERSIONS = ['2.0', '2.1', '2.2', '2.3']
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.txt"

from urllib.parse import quote_plus

from PyQt5.QtWidgets import QMessageBox

from picard import config, log
from picard.cluster import Cluster
from picard.plugins.search_engine_lookup.ui_options_search_engine_lookup import Ui_SearchEngineLookupOptionsPage
from picard.ui.itemviews import BaseAction, register_cluster_action
from picard.ui.mainwindow import MainWindow
from picard.ui.options import OptionsPage, register_options_page
from picard.util.webbrowser2 import open

ENGINES = {
    'Google': r'https://www.google.com/search?q=',
    'Bing': r'https://www.bing.com/search?q=',
    'DuckDuckGo': r'https://duckduckgo.com/?q=',
}


class SearchEngineLookup(BaseAction):
    NAME = 'Search engine lookup'

    def callback(self, cluster_list):
        for cluster in cluster_list:
            if isinstance(cluster, Cluster):
                parts = []
                if 'albumartist' in cluster.metadata and cluster.metadata['albumartist']:
                    parts.extend(str(cluster.metadata['albumartist']).split())
                if 'album' in cluster.metadata and cluster.metadata['albumartist']:
                    parts.extend(str(cluster.metadata['album']).split())
                if parts:
                    if config.setting["search_engine_lookup_extra_words"]:
                        parts.extend(str(config.setting["search_engine_lookup_extra_words"]).split())
                    url = ENGINES[config.setting["search_engine_lookup_provider"]] + quote_plus(' '.join(parts))
                    log.debug("{0}: Looking up {1}".format(PLUGIN_NAME, url,))
                    open(url)
                else:
                    log.error("{0}: No existing metadata to lookup.".format(PLUGIN_NAME,))
                    self._show_popup('There is no existing data to use for a search.')
            else:
                log.error("{0}: Argument is not a cluster. {1}".format(PLUGIN_NAME, cluster,))
                self._show_popup('There was a problem with the information provided for the cluster.')

    def _show_popup(self, content):
        window = MainWindow()
        QMessageBox.information(
            window,
            "Lookup Error",
            content,
            QMessageBox.Ok,
            QMessageBox.Ok
        )


class SearchEngineLookupOptionsPage(OptionsPage):

    NAME = "search_engine_lookup_options"
    TITLE = "Search Engine Lookup"
    PARENT = "plugins"

    options = [
        config.TextOption("setting", "search_engine_lookup_provider", 'Google'),
        config.TextOption("setting", "search_engine_lookup_extra_words", 'album'),
    ]

    def __init__(self, parent=None):
        super(SearchEngineLookupOptionsPage, self).__init__(parent)
        self.ui = Ui_SearchEngineLookupOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        # Enable external link
        self.ui.format_description.setOpenExternalLinks(True)

        # Settings for search engine provider
        temp = config.setting["search_engine_lookup_provider"]
        if temp not in ENGINES:
            temp = 'Google'
        if temp == 'Bing':
            self.ui.rb_bing.setChecked(True)
        elif temp == 'DuckDuckGo':
            self.ui.rb_duckduckgo.setChecked(True)
        else:
            self.ui.rb_google.setChecked(True)

        # Settings for search extra words
        self.ui.le_additional_words.setText(config.setting["search_engine_lookup_extra_words"])

    def save(self):
        self._set_settings(config.setting)

    def _set_settings(self, settings):

        # Process search engine provider settings
        if self.ui.rb_bing.isChecked():
            settings["search_engine_lookup_provider"] = 'Bing'
        elif self.ui.rb_duckduckgo.isChecked():
            settings["search_engine_lookup_provider"] = 'DuckDuckGo'
        else:
            settings["search_engine_lookup_provider"] = 'Google'

        # Process searc extra words setting
        settings["search_engine_lookup_extra_words"] = self.ui.le_additional_words.text().strip()


register_cluster_action(SearchEngineLookup())
register_options_page(SearchEngineLookupOptionsPage)
