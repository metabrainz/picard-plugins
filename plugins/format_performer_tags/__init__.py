# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Bob Swift (rdswift)
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

PLUGIN_NAME = 'Format Performer Tags'
PLUGIN_AUTHOR = 'Bob Swift, Philipp Wolfer'
PLUGIN_DESCRIPTION = '''
This plugin provides options with respect to the formatting of performer
tags.  It has been developed using the 'Standardise Performers' plugin by
Sophist as the basis for retrieving and processing the performer data for
each of the tracks.  The format of the resulting tags can be customized
in the option settings page.
'''

PLUGIN_VERSION = "0.7"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

PLUGIN_USER_GUIDE_URL = "https://github.com/rdswift/picard-plugins/blob/2.0_RDS_Plugins/plugins/format_performer_tags/docs/README.md"

DEV_TESTING = False

import re
from picard import config, log
from picard.metadata import Metadata, register_track_metadata_processor
from picard.plugin import PluginPriority
from picard.ui.options import register_options_page, OptionsPage
from picard.plugins.format_performer_tags.ui_options_format_performer_tags import Ui_FormatPerformerTagsOptionsPage

performers_split = re.compile(r", | and ").split

WORD_LIST = ['guest', 'solo', 'additional']


def get_word_dict(settings):
    word_dict = {}
    for word in WORD_LIST:
        word_dict[word] = settings['format_group_' + word]
    return word_dict


def rewrite_tag(key, values, metadata, word_dict, settings):
    mainkey, subkey = key.split(':', 1)
    if not subkey:
        return
    if subkey in WORD_LIST:
        subkey = 'unspecified'
    log.debug("%s: Formatting Performer [%s: %s]", PLUGIN_NAME, subkey, values,)
    instruments = performers_split(subkey)
    for instrument in instruments:
        if DEV_TESTING:
            log.debug("%s: instrument (first pass): '%s'", PLUGIN_NAME, instrument,)
        if instrument in WORD_LIST:
            instruments[0] = "{0} {1}".format(instruments[0], instrument,)
            if instrument and instrument in instruments:
                instruments.remove(instrument)
    groups = { 1: [], 2: [], 3: [], 4: [], }
    words = instruments[0].split()
    for word in words[:]:
        if word in WORD_LIST:
            groups[word_dict[word]].append(word)
            words.remove(word)
    instruments[0] = " ".join(words)
    display_group = {}
    for group_number in range(1, 5):
        if groups[group_number]:
            if DEV_TESTING:
                log.debug("%s: groups[%s]: %s", PLUGIN_NAME, group_number, groups[group_number],)
            group_separator = settings["format_group_{0}_sep_char".format(group_number)]
            if not group_separator:
                group_separator = " "
            display_group[group_number] = settings["format_group_{0}_start_char".format(group_number)] \
                + group_separator.join(groups[group_number]) \
                + settings["format_group_{0}_end_char".format(group_number)]
        else:
            display_group[group_number] = ""
    if DEV_TESTING:
        log.debug("%s: display_group: %s", PLUGIN_NAME, display_group,)
    metadata.delete(key)
    for instrument in instruments:
        if DEV_TESTING:
            log.debug("%s: instrument (second pass): '%s'", PLUGIN_NAME, instrument,)
        words = instrument.split()
        if (len(words) > 1) and (words[-1] in ["vocal", "vocals",]):
            vocals = " ".join(words[:-1])
            instrument = words[-1]
        else:
            vocals = ""
        if vocals:
            group_number = settings["format_group_vocals"]
            temp_group = groups[group_number][:]
            if group_number < 2:
                temp_group.append(vocals)
            else:
                temp_group.insert(0, vocals)
            group_separator = settings["format_group_{0}_sep_char".format(group_number)]
            if not group_separator:
                group_separator = " "
            display_group[group_number] = settings["format_group_{0}_start_char".format(group_number)] \
                + group_separator.join(temp_group) \
                + settings["format_group_{0}_end_char".format(group_number)]

        newkey = ('%s:%s%s%s%s' % (mainkey, display_group[1], instrument, display_group[2], display_group[3],))
        log.debug("%s: newkey: %s", PLUGIN_NAME, newkey,)
        for value in values:
            metadata.add_unique(newkey, (value + display_group[4]))


def format_performer_tags(album, metadata, *args):
    word_dict = get_word_dict(config.setting)
    for key, values in list(filter(lambda filter_tuple: filter_tuple[0].startswith('performer:') or filter_tuple[0].startswith('~performersort:'), metadata.rawitems())):
        rewrite_tag(key, values, metadata, word_dict, config.setting)


class FormatPerformerTagsOptionsPage(OptionsPage):

    NAME = "format_performer_tags"
    TITLE = "Format Performer Tags"
    PARENT = "plugins"

    options = [
        config.IntOption("setting", "format_group_additional", 3),
        config.IntOption("setting", "format_group_guest", 4),
        config.IntOption("setting", "format_group_solo", 3),
        config.IntOption("setting", "format_group_vocals", 2),
        config.TextOption("setting", "format_group_1_start_char", ''),
        config.TextOption("setting", "format_group_1_end_char", ' '),
        config.TextOption("setting", "format_group_1_sep_char", ''),
        config.TextOption("setting", "format_group_2_start_char", ', '),
        config.TextOption("setting", "format_group_2_end_char", ''),
        config.TextOption("setting", "format_group_2_sep_char", ''),
        config.TextOption("setting", "format_group_3_start_char", ' ('),
        config.TextOption("setting", "format_group_3_end_char", ')'),
        config.TextOption("setting", "format_group_3_sep_char", ''),
        config.TextOption("setting", "format_group_4_start_char", ' ('),
        config.TextOption("setting", "format_group_4_end_char", ')'),
        config.TextOption("setting", "format_group_4_sep_char", ''),
    ]

    def __init__(self, parent=None):
        super(FormatPerformerTagsOptionsPage, self).__init__(parent)
        self.ui = Ui_FormatPerformerTagsOptionsPage()
        self.ui.setupUi(self)
        self.ui.additional_rb_1.clicked.connect(self.update_examples)
        self.ui.additional_rb_2.clicked.connect(self.update_examples)
        self.ui.additional_rb_3.clicked.connect(self.update_examples)
        self.ui.additional_rb_4.clicked.connect(self.update_examples)
        self.ui.guest_rb_1.clicked.connect(self.update_examples)
        self.ui.guest_rb_2.clicked.connect(self.update_examples)
        self.ui.guest_rb_3.clicked.connect(self.update_examples)
        self.ui.guest_rb_4.clicked.connect(self.update_examples)
        self.ui.solo_rb_1.clicked.connect(self.update_examples)
        self.ui.solo_rb_2.clicked.connect(self.update_examples)
        self.ui.solo_rb_3.clicked.connect(self.update_examples)
        self.ui.solo_rb_4.clicked.connect(self.update_examples)
        self.ui.vocals_rb_1.clicked.connect(self.update_examples)
        self.ui.vocals_rb_2.clicked.connect(self.update_examples)
        self.ui.vocals_rb_3.clicked.connect(self.update_examples)
        self.ui.vocals_rb_4.clicked.connect(self.update_examples)
        self.ui.format_group_1_start_char.editingFinished.connect(self.update_examples)
        self.ui.format_group_2_start_char.editingFinished.connect(self.update_examples)
        self.ui.format_group_3_start_char.editingFinished.connect(self.update_examples)
        self.ui.format_group_4_start_char.editingFinished.connect(self.update_examples)
        self.ui.format_group_1_sep_char.editingFinished.connect(self.update_examples)
        self.ui.format_group_2_sep_char.editingFinished.connect(self.update_examples)
        self.ui.format_group_3_sep_char.editingFinished.connect(self.update_examples)
        self.ui.format_group_4_sep_char.editingFinished.connect(self.update_examples)
        self.ui.format_group_1_end_char.editingFinished.connect(self.update_examples)
        self.ui.format_group_2_end_char.editingFinished.connect(self.update_examples)
        self.ui.format_group_3_end_char.editingFinished.connect(self.update_examples)
        self.ui.format_group_4_end_char.editingFinished.connect(self.update_examples)

    def load(self):
        # Enable external link
        self.ui.format_description.setOpenExternalLinks(True)

        # Settings for Keyword: additional
        temp = config.setting["format_group_additional"]
        if temp > 3:
            self.ui.additional_rb_4.setChecked(True)
        elif temp > 2:
            self.ui.additional_rb_3.setChecked(True)
        elif temp > 1:
            self.ui.additional_rb_2.setChecked(True)
        else:
            self.ui.additional_rb_1.setChecked(True)

        # Settings for Keyword: guest
        temp = config.setting["format_group_guest"]
        if temp > 3:
            self.ui.guest_rb_4.setChecked(True)
        elif temp > 2:
            self.ui.guest_rb_3.setChecked(True)
        elif temp > 1:
            self.ui.guest_rb_2.setChecked(True)
        else:
            self.ui.guest_rb_1.setChecked(True)

        # Settings for Keyword: solo
        temp = config.setting["format_group_solo"]
        if temp > 3:
            self.ui.solo_rb_4.setChecked(True)
        elif temp > 2:
            self.ui.solo_rb_3.setChecked(True)
        elif temp > 1:
            self.ui.solo_rb_2.setChecked(True)
        else:
            self.ui.solo_rb_1.setChecked(True)

        # Settings for all vocal keywords
        temp = config.setting["format_group_vocals"]
        if temp > 3:
            self.ui.vocals_rb_4.setChecked(True)
        elif temp > 2:
            self.ui.vocals_rb_3.setChecked(True)
        elif temp > 1:
            self.ui.vocals_rb_2.setChecked(True)
        else:
            self.ui.vocals_rb_1.setChecked(True)

        # Settings for word group 1
        self.ui.format_group_1_start_char.setText(config.setting["format_group_1_start_char"])
        self.ui.format_group_1_end_char.setText(config.setting["format_group_1_end_char"])
        self.ui.format_group_1_sep_char.setText(config.setting["format_group_1_sep_char"])

        # Settings for word group 2
        self.ui.format_group_2_start_char.setText(config.setting["format_group_2_start_char"])
        self.ui.format_group_2_end_char.setText(config.setting["format_group_2_end_char"])
        self.ui.format_group_2_sep_char.setText(config.setting["format_group_2_sep_char"])

        # Settings for word group 3
        self.ui.format_group_3_start_char.setText(config.setting["format_group_3_start_char"])
        self.ui.format_group_3_end_char.setText(config.setting["format_group_3_end_char"])
        self.ui.format_group_3_sep_char.setText(config.setting["format_group_3_sep_char"])

        # Settings for word group 4
        self.ui.format_group_4_start_char.setText(config.setting["format_group_4_start_char"])
        self.ui.format_group_4_end_char.setText(config.setting["format_group_4_end_char"])
        self.ui.format_group_4_sep_char.setText(config.setting["format_group_4_sep_char"])
        self.update_examples()

        # TODO: Modify self.format_description in ui_options_format_performer_tags.py to include a placeholder
        #       such as {user_guide_url} so that the translated string can be formatted to include the value
        #       of PLUGIN_USER_GUIDE_URL to dynamically set the link while not requiring retranslation if the
        #       link changes.  Preliminary code something like:
        #
        #       temp = (self.ui.format_description.text).format(user_guide_url=PLUGIN_USER_GUIDE_URL,)
        #       self.ui.format_description.setText(temp)


    def save(self):
        self._set_settings(config.setting)

    def restore_defaults(self):
        super().restore_defaults()
        self.update_examples()

    def _set_settings(self, settings):

        # Process 'additional' keyword settings
        temp = 1
        if self.ui.additional_rb_2.isChecked(): temp = 2
        if self.ui.additional_rb_3.isChecked(): temp = 3
        if self.ui.additional_rb_4.isChecked(): temp = 4
        settings["format_group_additional"] = temp

        # Process 'guest' keyword settings
        temp = 1
        if self.ui.guest_rb_2.isChecked(): temp = 2
        if self.ui.guest_rb_3.isChecked(): temp = 3
        if self.ui.guest_rb_4.isChecked(): temp = 4
        settings["format_group_guest"] = temp

        # Process 'solo' keyword settings
        temp = 1
        if self.ui.solo_rb_2.isChecked(): temp = 2
        if self.ui.solo_rb_3.isChecked(): temp = 3
        if self.ui.solo_rb_4.isChecked(): temp = 4
        settings["format_group_solo"] = temp

        # Process all vocal keyword settings
        temp = 1
        if self.ui.vocals_rb_2.isChecked(): temp = 2
        if self.ui.vocals_rb_3.isChecked(): temp = 3
        if self.ui.vocals_rb_4.isChecked(): temp = 4
        settings["format_group_vocals"] = temp

        # Settings for word group 1
        settings["format_group_1_start_char"] = self.ui.format_group_1_start_char.text()
        settings["format_group_1_end_char"] = self.ui.format_group_1_end_char.text()
        settings["format_group_1_sep_char"] = self.ui.format_group_1_sep_char.text()

        # Settings for word group 2
        settings["format_group_2_start_char"] = self.ui.format_group_2_start_char.text()
        settings["format_group_2_end_char"] = self.ui.format_group_2_end_char.text()
        settings["format_group_2_sep_char"] = self.ui.format_group_2_sep_char.text()

        # Settings for word group 3
        settings["format_group_3_start_char"] = self.ui.format_group_3_start_char.text()
        settings["format_group_3_end_char"] = self.ui.format_group_3_end_char.text()
        settings["format_group_3_sep_char"] = self.ui.format_group_3_sep_char.text()

        # Settings for word group 4
        settings["format_group_4_start_char"] = self.ui.format_group_4_start_char.text()
        settings["format_group_4_end_char"] = self.ui.format_group_4_end_char.text()
        settings["format_group_4_sep_char"] = self.ui.format_group_4_sep_char.text()

    def update_examples(self):
        settings = {}
        self._set_settings(settings)
        word_dict = get_word_dict(settings)

        instruments_credits = {
            "guitar": ["Johnny Flux", "John Watson"],
            "guest guitar": ["Jimmy Page"],
            "additional guest solo guitar": ["Jimmy Page"],
        }
        instruments_example = self.build_example(instruments_credits, word_dict, settings)
        self.ui.example_instruments.setText(instruments_example)

        vocals_credits = {
            "additional solo lead vocals": ["Robert Plant"],
            "additional solo guest lead vocals": ["Sandy Denny"],
        }
        vocals_example = self.build_example(vocals_credits, word_dict, settings)
        self.ui.example_vocals.setText(vocals_example)

    @staticmethod
    def build_example(credits, word_dict, settings):
        prefix = "performer:"
        metadata = Metadata()
        for key, values in credits.items():
            rewrite_tag(prefix + key, values, metadata, word_dict, settings)

        examples = []
        for key, values in metadata.rawitems():
            credit = "%s: %s" % (key, ", ".join(values))
            if credit.startswith(prefix):
                credit = credit[len(prefix):]
            examples.append(credit)
        return "\n".join(examples)


# Register the plugin to run at a HIGH priority.
register_track_metadata_processor(format_performer_tags, priority=PluginPriority.HIGH)
register_options_page(FormatPerformerTagsOptionsPage)
