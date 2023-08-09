# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Flaky
# Copyright (C) 2023 Bob Swift (rdswift)
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

PLUGIN_NAME = "Submit Folksonomy Tags"
PLUGIN_AUTHOR = "Flaky"
PLUGIN_DESCRIPTION = """
A plugin allowing submission of specific tags on tracks you own (defaults to <i>genre</i> and <i>mood</i>) as folksonomy tags on MusicBrainz. Supports submitting to recording, release, release group and release artist entities.

A MusicBrainz login is required to use this plugin. Log in first by going to the General options. Then, to use, right click on a track or release then go to <i>Plugins</i> and depending on what you want to submit, choose the option you want.

Uses code from rdswift's "Submit ISRC" plugin (specifically, the handling of the network response)
"""
PLUGIN_VERSION = '0.4'
PLUGIN_API_VERSIONS = ['2.2', '2.9']
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.txt"

from picard import config, log
from picard.ui.itemviews import (BaseAction,
                                 register_album_action,
                                 register_track_action
                                 )
from picard.ui.options import OptionsPage, register_options_page
from PyQt5.QtWidgets import QMessageBox
from .ui_config import TagSubmitPluginOptionsUI
from .submit_handler import handle_submit_process, process_objs_to_track_list

# Some internal settings.
# Don't change these unless you know what you're doing.
# You can change the tags you want to submit in the settings.

client_params = {
    "client": f"picard_plugin_{PLUGIN_NAME.replace(' ', '_')}-v{PLUGIN_VERSION}"
}
default_tags_to_submit = ['genre', 'mood']

# The options as saved in Picard.ini
config.BoolOption("setting", 'tag_submit_plugin_destructive', False)
config.BoolOption("setting", 'tag_submit_plugin_destructive_alert_acknowledged', False)
config.BoolOption("setting", 'tag_submit_plugin_aliases_enabled', False)
config.ListOption("setting", 'tag_submit_plugin_alias_list', [])
config.ListOption("setting", 'tag_submit_plugin_tags_to_submit', default_tags_to_submit)


class TagSubmitPlugin_OptionsPage(OptionsPage):
    NAME = "tag_submit_plugin"
    TITLE = "Tag Submission Plugin"
    PARENT = "plugins"
    HELP_URL = ""

    def __init__(self, parent=None):
        super().__init__()
        self.ui = TagSubmitPluginOptionsUI(self)
        self.destructive_acknowledgement = config.setting['tag_submit_plugin_destructive_alert_acknowledged']
        self.ui.overwrite_radio_button.clicked.connect(self.on_destructive_selected)

    def on_destructive_selected(self):
        if not config.setting['tag_submit_plugin_destructive_alert_acknowledged']:
            warning = QMessageBox()
            warning.setStandardButtons(QMessageBox.Ok)
            warning.setDefaultButton(QMessageBox.Ok)
            warning.setIcon(QMessageBox.Warning)
            warning.setText("""
                <p><b>WARNING: BY SELECTING TO OVERWRITE ALL TAGS, THIS MEANS <i>ALL</i> TAGS.</b></p>
                <p>By enabling this option, you acknowledge that you may lose the tags already saved online from the tracks you process via this plugin. This alert will only be displayed once before you save.</p>
                <p>If you do not want this behaviour, select the maintain option.</p>"""
                            )
            warning.exec_()
            config.setting['tag_submit_plugin_destructive_alert_acknowledged'] = True

    def load(self):
        # Destructive option
        if config.setting['tag_submit_plugin_destructive']:
            self.ui.overwrite_radio_button.setChecked(True)
        else:
            self.ui.keep_radio_button.setChecked(True)

        self.ui.tags_to_save_textbox.setText(
            '; '.join(config.setting['tag_submit_plugin_tags_to_submit'])
        )

        # Aliases enabled option
        self.ui.tag_alias_groupbox.setChecked(
            config.setting['tag_submit_plugin_aliases_enabled']
        )

        # Alias list
        if 'tag_submit_plugin_alias_list' in config.setting:
            log.info("Alias list exists! Let's populate the table.")
            for alias_tuple in config.setting['tag_submit_plugin_alias_list']:
                self.ui.add_row(alias_tuple[0], alias_tuple[1])
            self.ui.tag_alias_table.resizeColumnsToContents()

        config.setting['tag_submit_plugin_destructive_alert_acknowledged'] = self.destructive_acknowledgement

    def save(self):
        config.setting['tag_submit_plugin_destructive'] = self.ui.overwrite_radio_button.isChecked()
        config.setting['tag_submit_plugin_aliases_enabled'] = self.ui.tag_alias_groupbox.isChecked()

        tag_textbox_text = self.ui.tags_to_save_textbox.text()
        if tag_textbox_text:
            config.setting['tag_submit_plugin_tags_to_submit'] = [
                tag.strip() for tag in tag_textbox_text.split(';')
            ]
        else:
            config.setting['tag_submit_plugin_tags_to_submit'] = default_tags_to_submit

        if config.setting['tag_submit_plugin_aliases_enabled']:
            new_alias_list = self.ui.rows_to_tuple_list()
            log.info(new_alias_list)
            config.setting['tag_submit_plugin_alias_list'] = new_alias_list


class SubmitTrackTagsMenuAction(BaseAction):
    NAME = 'Submit tags to MusicBrainz (recording)'

    def callback(self, objs):
        handle_submit_process(
            objs[0].tagger,
            process_objs_to_track_list(objs),
            "musicbrainz_recordingid",
            client_params
        )


class SubmitReleaseTagsMenuAction(BaseAction):
    NAME = 'Submit tags to MusicBrainz (release)'

    def callback(self, objs):
        handle_submit_process(
            objs[0].tagger,
            process_objs_to_track_list(objs),
            "musicbrainz_albumid",
            client_params
        )


class SubmitRGTagsMenuAction(BaseAction):
    NAME = 'Submit tags to MusicBrainz (release group)'

    def callback(self, objs):
        handle_submit_process(
            objs[0].tagger,
            process_objs_to_track_list(objs),
            "musicbrainz_releasegroupid",
            client_params
        )


class SubmitRATagsMenuAction(BaseAction):
    NAME = 'Submit tags to MusicBrainz (release artist)'

    def callback(self, objs):
        handle_submit_process(
            objs[0].tagger,
            process_objs_to_track_list(objs),
            "musicbrainz_albumartistid",
            client_params
        )


register_options_page(TagSubmitPlugin_OptionsPage)
register_album_action(SubmitTrackTagsMenuAction())
register_track_action(SubmitTrackTagsMenuAction())
register_album_action(SubmitReleaseTagsMenuAction())
register_track_action(SubmitReleaseTagsMenuAction())
register_album_action(SubmitRGTagsMenuAction())
register_track_action(SubmitRGTagsMenuAction())
register_album_action(SubmitRATagsMenuAction())
register_track_action(SubmitRATagsMenuAction())
