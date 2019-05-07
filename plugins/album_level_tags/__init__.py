# SPDX-License-Identifier: GPL-2.0-only
#
# Copyright (c) 2019 Joel Lintunen <joellintunen@gmail.com>

PLUGIN_NAME = "Album-level Tags"
PLUGIN_AUTHOR = "Joel Lintunen"
PLUGIN_DESCRIPTION = """<p>Provides two script functions which combine track-level tags into single album-level
entities. These script functions are useful if you want to use tags like <code>%_sample_rate%</code> in a directory
name but don't want Picard to split an album into multiple directories because of it.</p>

<p>Function descriptions:
<ul>
  <li><code>$album_level(TAG)</code> returns a list of the values.</li>
  <li><code>$album_level_average(TAG)</code> returns an average of the values. All the values have to be numerical.</li>
</ul></p>

<p>Both functions can take two arguments:
<ol>
  <li>A tag whose values are being processed.</li>
  <li>(Optional.) An options profile name. See the options page of the plugin.</li>
</ol></p>

<p>Examples:
<ul>
  <li><code>$album_level(_sample_rate)</code></li>
  <li><code>$album_level(_bits_per_sample,)</code></li>
  <li><code>$album_level(_extension,)</code></li>
  <li><code>$album_level(media,media_all)</code></li>
  <li><code>$album_level(media,media_loaded)</code></li>
  <li><code>$album_level_average(bpm)</code></li>
  <li><code>$album_level_average(_bitrate,bitrates)</code></li>
</ul></p>
"""
PLUGIN_VERSION = "3.0.0"
PLUGIN_API_VERSIONS = ["2.1"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"


from collections import (
    Counter,
    defaultdict,
)
import json
from picard.album import NatAlbum
from picard.config import TextOption
from picard.metadata import MULTI_VALUED_JOINER
from picard.plugins.album_level_tags.ui_options_album_level_tags import Ui_AlbumLevelTagsOptionsPage
from picard.script import (
    normalize_tagname,
    register_script_function,
)
from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from PyQt5 import QtGui
from PyQt5.QtWidgets import QButtonGroup
import time

# Option strings
TAG_LIMIT_OPTION = "tag_limit"
OMIT_STRING_OPTION = "omitter"
SEPARATOR_OPTION = "separator"
FORMATTER_OPTION = "formatter"
FORMATTER_WHEN_ONE_OPTION = "formatter_when_one"
LOADED_FILES_ONLY_OPTION = "loaded_files_only"
GROUPING_OPTION = "grouping_tag"
REPLACEMENTS_PROFILE_OPTION = "replacements"

DEFAULT_OPTION_VALUES = {
    TAG_LIMIT_OPTION: 0,
    OMIT_STRING_OPTION: "",
    SEPARATOR_OPTION: MULTI_VALUED_JOINER,
    FORMATTER_OPTION: "{0}",
    FORMATTER_WHEN_ONE_OPTION: "",
    LOADED_FILES_ONLY_OPTION: False,
    GROUPING_OPTION: "",
    REPLACEMENTS_PROFILE_OPTION: ""
}
DEFAULT_AVERAGE_OVERRIDE_VALUES = {
    FORMATTER_OPTION: "{:.0f}",
    FORMATTER_WHEN_ONE_OPTION: "{:.0f}"
}

# All tags are processed during the first file save so there's no need to redo everything for every file
tag_cache = defaultdict(dict)
last_run_time = 0


def get_script_func(average_mode):
    def script_func(parser, metadata_key, option_profile=None):
        metadata_key = normalize_tagname(metadata_key)
        try:
            album = parser.file.parent.album
        except AttributeError:  # Happens with the file naming example box
            return metadata_key.strip("~").upper()
        if isinstance(album, NatAlbum):
            raise TypeError("{0}: NAT-albums are not processed.".format(PLUGIN_NAME))

        # Check if cached data is recent enough to be used (i.e. we can assume that the user hasn't modified the tags
        # in the meantime) or remove other releases from the cache to keep it small
        global tag_cache
        global last_run_time
        album_cache = tag_cache.get(album.id, {})
        if album_cache:
            t = time.time()

            cached_results = album_cache.get((metadata_key, option_profile))
            if cached_results and t - last_run_time < 4:  # seconds
                tag_cache[album.id][(metadata_key, option_profile)] = cached_results
                last_run_time = t
                return cached_results
        else:
            tag_cache.clear()

        # Get options
        options = DEFAULT_OPTION_VALUES.copy()
        if average_mode:
            options.update(DEFAULT_AVERAGE_OVERRIDE_VALUES)
        try:
            all_user_options = json.loads(album.tagger.config.setting["a_l_t_options"])
            profile_options = all_user_options.get(option_profile, {})
        except json.decoder.JSONDecodeError:
            raise SyntaxError("{0}: Syntax error in options.".format(PLUGIN_NAME))

        if option_profile is not None and option_profile not in all_user_options:
            raise KeyError("{0}: Unknown option profile \"{1}\" used in a script.".format(PLUGIN_NAME, option_profile))
        if profile_options.get(FORMATTER_WHEN_ONE_OPTION):
            formatter2_is_default = False
        else:
            formatter2_is_default = True
        options.update(profile_options)

        tag_limit = options[TAG_LIMIT_OPTION]
        omit_string = options[OMIT_STRING_OPTION]
        separator = options[SEPARATOR_OPTION]
        formatter = options[FORMATTER_OPTION]
        formatter_when_one = formatter if formatter2_is_default else options[FORMATTER_WHEN_ONE_OPTION]
        loaded_files_only = options[LOADED_FILES_ONLY_OPTION]
        grouping_key = normalize_tagname(options[GROUPING_OPTION])
        replacements_profile = options[REPLACEMENTS_PROFILE_OPTION]

        # Get tags
        group_by_medium = True if metadata_key == "media" else False
        discnumber = 0
        temp = defaultdict(list)
        for t in album.tracks:
            # Note: a release always has standardized discnumbers
            if group_by_medium and discnumber == int(t.metadata["discnumber"]):
                continue
            discnumber += 1
            if t.num_linked_files > 0:
                for lf in t.linked_files:
                    temp[lf.metadata.get(grouping_key)] += lf.metadata.getall(metadata_key)
            elif not loaded_files_only:
                temp[t.metadata.get(grouping_key)] += t.metadata.getall(metadata_key)

        if average_mode:
            tag_counter = Counter({ sum(map(float, tag_list)) / len(tag_list): 1
                                    for tag_list in temp.values() if len(tag_list) > 0 })
        else:
            tag_counter = Counter([ tag for k in temp for tag in temp[k] ])

        # Rename tag values if that's wanted behaviour
        try:
            replacements = json.loads(album.tagger.config.setting["a_l_t_replacements"]).get(replacements_profile, {})
        except json.decoder.JSONDecodeError:
            raise SyntaxError(PLUGIN_NAME + ": Syntax error in replacements.")
        tag_counter = Counter({ replacements.get(tag, tag): count for tag, count in tag_counter.items() })

        # Effectively removes the None key from the counter
        tag_counter[None] = 0
        tag_counter = +tag_counter

        # Limits the number of tags
        if len(tag_counter) > tag_limit > 0:
            tag_counter = Counter({ k: v for k, v in tag_counter.most_common(tag_limit) })
        else:
            omit_string = ""

        results = separator.join([ formatter.format(tag, count)
                                   if count > 1 else formatter_when_one.format(tag, count)
                                   for tag, count in tag_counter.items()
                                   ]) + omit_string

        # Save results to the cache for the next file to use
        tag_cache[album.id][(metadata_key, option_profile)] = results
        last_run_time = time.time()

        return results
    return script_func


class AlbumLevelTagsOptionsPage(OptionsPage):

    NAME = "album_level_tags"
    TITLE = "Album-level Tags"
    PARENT = "plugins"

    DEFAULT_OPTIONS = {
        "": {
            SEPARATOR_OPTION: ", "
        },
        "media_loaded": {
            SEPARATOR_OPTION: " + ",
            FORMATTER_OPTION: "{1}×{0}",
            FORMATTER_WHEN_ONE_OPTION: "{0}",
            LOADED_FILES_ONLY_OPTION: True,
            REPLACEMENTS_PROFILE_OPTION: "media"
        },
        "media_all": {
            SEPARATOR_OPTION: " + ",
            FORMATTER_OPTION: "{1}×{0}",
            FORMATTER_WHEN_ONE_OPTION: "{0}",
            REPLACEMENTS_PROFILE_OPTION: "media"
        },
        "bitrates": {
            SEPARATOR_OPTION: ", ",
            LOADED_FILES_ONLY_OPTION: True,
            GROUPING_OPTION: "media",
        }
    }

    DEFAULT_REPLACEMENTS = {
        "media": {
            "Copy Control CD": "CCCD",
            "8cm CD": "CD",
            "8cm CD+G": "CD+G",
            "7\" Vinyl": "Vinyl",
            "10\" Vinyl": "Vinyl",
            "12\" Vinyl": "Vinyl",
            "7\" Flexi-disc": "Flexi-disc",
            "7\" Shellac": "Shellac",
            "10\" Shellac": "Shellac",
            "12\" Shellac": "Shellac",
            "Digital Media": "Digital",
            "DVD-Audio": "DVD",
            "DVD-Video": "DVD",
            "Hybrid SACD (CD layer)": "Hybrid SACD",
            "Hybrid SACD (SACD layer)": "Hybrid SACD",
            "DualDisc (CD side)": "DualDisc",
            "DualDisc (DVD-Video side)": "DualDisc",
            "DualDisc (DVD-Audio side)": "DualDisc",
            "8-Track Cartridge": "Cartridge",
            "DVDplus (CD side)": "DVDplus",
            "DVDplus (DVD-Video side)": "DVDplus",
            "DVDplus (DVD-Audio side)": "DVDplus",
            "3.5\" Floppy Disk": "Floppy Disk",
            "8\" LaserDisc": "LaserDisc",
            "12\" LaserDisc": "LaserDisc",
            "VinylDisc (CD side)": "VinylDisc",
            "VinylDisc (DVD side)": "VinylDisc",
            "VinylDisc (Vinyl side)": "VinylDisc"
        }
    }

    options = [
        TextOption("setting", "a_l_t_options", json.dumps(DEFAULT_OPTIONS, indent="\t")),
        TextOption("setting", "a_l_t_replacements", json.dumps(DEFAULT_REPLACEMENTS, indent="\t")),
    ]

    def __init__(self, parent=None):
        super(AlbumLevelTagsOptionsPage, self).__init__(parent)
        self.ui = Ui_AlbumLevelTagsOptionsPage()
        self.ui.setupUi(self)

        font = QtGui.QFont("Courier")
        self.ui.plainTextEdit_raw.setFont(font)
        tab_width = QtGui.QFontMetricsF(self.ui.plainTextEdit_raw.font()).width(' ') * 4
        self.ui.plainTextEdit_raw.setTabStopDistance(tab_width)
        self.ui.pushButton_valid_raw.clicked.connect(self.options_validation_func)

        self.ui.plainTextEdit_raw_2.setFont(font)
        self.ui.plainTextEdit_raw_2.setTabStopDistance(tab_width)
        self.ui.pushButton_valid_raw_2.clicked.connect(self.replacements_validation_func)

        self.ui.pushButton_2.clicked.connect(self.add_options_profile)
        self.ui.pushButton_3.clicked.connect(self.reset_option_fields)
        self.ui.button_group = QButtonGroup()
        self.ui.button_group.addButton(self.ui.radioButton, 0)
        self.ui.button_group.addButton(self.ui.radioButton_2, 1)

    def add_options_profile(self):
        profile_name = self.ui.lineEdit_7.text()
        new_option_profile = {
            TAG_LIMIT_OPTION: self.ui.spinBox.value(),
            OMIT_STRING_OPTION: self.ui.lineEdit.text(),
            SEPARATOR_OPTION: self.ui.lineEdit_2.text(),
            FORMATTER_OPTION: self.ui.lineEdit_3.text(),
            FORMATTER_WHEN_ONE_OPTION: self.ui.lineEdit_4.text(),
            LOADED_FILES_ONLY_OPTION: True if self.ui.button_group.checkedId() else False,
            GROUPING_OPTION: self.ui.lineEdit_5.text(),
            REPLACEMENTS_PROFILE_OPTION: self.ui.lineEdit_6.text()
        }
        new_option_profile = { k: v for k, v in new_option_profile.items() if v }
        if self.ui.checkBox_copy_defaults.isChecked():
            new_option_profile = dict(DEFAULT_OPTION_VALUES, **new_option_profile)
        try:
            option_profiles = json.loads(self.ui.plainTextEdit_raw.toPlainText())
            self.ui.label_error.setText("")
        except json.decoder.JSONDecodeError:
            self.ui.label_error.setText("Syntax error! Make sure the JSON below is valid.")
            return
        option_profiles.update({profile_name: new_option_profile})
        self.ui.plainTextEdit_raw.document().setPlainText(json.dumps(option_profiles, indent="\t"))

    def reset_option_fields(self):
        self.ui.spinBox.setValue(0)
        self.ui.lineEdit.setText("")
        self.ui.lineEdit_2.setText("")
        self.ui.lineEdit_3.setText("")
        self.ui.lineEdit_4.setText("")
        self.ui.radioButton.setChecked(True)
        self.ui.lineEdit_5.setText("")
        self.ui.lineEdit_6.setText("")
        self.ui.lineEdit_7.setText("")

    def options_validation_func(self):
        text_area = self.ui.plainTextEdit_raw
        label = self.ui.label_valid_raw
        try:
            possibly_bad_options = json.loads(text_area.toPlainText())
        except json.decoder.JSONDecodeError as e:
            label.setText("Syntax error! " + str(e))
            return
        for option, value in [ (option, value) for profile in possibly_bad_options
                               for option, value in possibly_bad_options[profile].items() ]:
            defaultvalue = DEFAULT_OPTION_VALUES.get(option)
            if defaultvalue is None:
                label.setText("Option error! \"{0}\" isn't a known option name.".format(option))
                return
            elif not isinstance(value, type(defaultvalue)):
                label.setText("Option error! \"{0}\" expected {1}, got {2}.".format(
                    option, str(type(defaultvalue)), str(type(value))))
                return
        label.setText("Success! Valid syntax. Valid options.")

    def replacements_validation_func(self):
        text_area = self.ui.plainTextEdit_raw_2
        label = self.ui.label_valid_raw_2
        try:
            _ = json.loads(text_area.toPlainText())
        except json.decoder.JSONDecodeError as e:
            label.setText("Syntax error! " + str(e))
            return
        label.setText("Success! Valid syntax.")

    def load(self):
        self.ui.plainTextEdit_raw.document().setPlainText(self.config.setting["a_l_t_options"])
        self.ui.plainTextEdit_raw_2.document().setPlainText(self.config.setting["a_l_t_replacements"])

    def save(self):
        self.config.setting["a_l_t_options"] = self.ui.plainTextEdit_raw.toPlainText()
        self.config.setting["a_l_t_replacements"] = self.ui.plainTextEdit_raw_2.toPlainText()


register_script_function(get_script_func(average_mode=True), "album_level_average")
register_script_function(get_script_func(average_mode=False), "album_level")
register_options_page(AlbumLevelTagsOptionsPage)
