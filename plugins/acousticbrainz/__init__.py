# -*- coding: utf-8 -*-
# Acousticbrainz plugin for Picard
# Copyright (C) 2021 Wargreen
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

# Plugin metadata
# =============================================================================

PLUGIN_NAME = 'AcousticBrainz Tags'
PLUGIN_AUTHOR = ('Wargreen <wargreen@lebib.org>, '
                 'Hugo Geoffroy "pistache" <pistache@lebib.org>')
PLUGIN_DESCRIPTION = '''
Tag files with tags from the AcousticBrainz database, all highlevel classifiers 
and tonal/rhythm data. 
<br/><br/>
By default, only simple mood and genre information is saved, but the plugin can
be configured to include all highlevel data.
<br/><br/>
Based on code from Andrew Cook, Sambhav Kothari
<br/><br/>
<b>WARNING:</b> Experimental plugin. All guarantees voided by use.'''

PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.txt"
PLUGIN_VERSION = "2.0"
PLUGIN_API_VERSIONS = ["2.0", "2.1", "2.2", "2.3", "2.4", "2.5" ,"2.6"]

# Plugin configuration
# =============================================================================

ACOUSTICBRAINZ_HOST = "acousticbrainz.org"
ACOUSTICBRAINZ_PORT = 80


# Subset of the low level data to add as tags.
# Represent the data as nested dicts.

SUBLOWLEVEL_SUBSET = {"rhythm": {"bpm": None},
                      "tonal": {"chords_changes_rate": None,
                                "chords_key": None,
                                "chords_scale": None,
                                "key_key": None,
                                "key_scale": None}}

# Imports
# =============================================================================

from json import dumps as dump_json, JSONDecodeError
from functools import partial
from picard import config, log
from picard.webservice import ratecontrol
from picard.util import load_json
from picard.ui.options import register_options_page, OptionsPage
from picard.metadata import register_track_metadata_processor
from picard.plugins.acousticbrainz.ui_options_acousticbrainz_tags import Ui_AcousticbrainzOptionsPage

ratecontrol.set_minimum_delay((ACOUSTICBRAINZ_HOST, ACOUSTICBRAINZ_PORT), 250)

# Constants
# =============================================================================

PENDING = object()

LOWLEVEL = "lowlevel"
HIGHLEVEL = "highlevel"


# Track class
# =============================================================================
# (used to fetch and store per-track AcousticBrainz data)

class Track:
    def __init__(self, album, metadata):
        self.album = album
        self.metadata = metadata

        self.data_lowlevel = None
        self.data_highlevel = None

        self.do_simplemood = config.setting["acousticbrainz_add_simplemood"]
        self.do_simplegenre = config.setting["acousticbrainz_add_simplegenre"]
        self.do_keybpm = config.setting["acousticbrainz_add_keybpm"]
        self.do_fullhighlevel = config.setting["acousticbrainz_add_fullhighlevel"]
        self.do_sublowlevel = config.setting["acousticbrainz_add_sublowlevel"]
        
    # Logging utilities
    # -------------------------------------------------------------------------
        
    def log(self, logger, text, *args):
        logger("%s: [%s: %s] " + text, PLUGIN_NAME, self.shortid, self.title, *args)

    def debug(self, *args):
        self.log(log.debug, *args)
        
    def warning(self, *args):
        self.log(log.warning, *args)
        
    def error(self, *args):
        self.log(log.error, *args)

    # Read-only properties
    # -------------------------------------------------------------------------

    @property
    def trackid(self):
        return self.metadata["musicbrainz_recordingid"]

    @property 
    def shortid(self):
        return self.trackid[:8]
        
    @property
    def title(self):
        return self.metadata["title"]
    
    @property
    def queryargs(self):
        return {
            "recording_ids": self.trackid,
            "map_classes": "true"
        }
        
    # Entry point
    # -------------------------------------------------------------------------
        
    def process(self):
        if self.do_simplemood or self.do_fullhighlevel or self.do_simplegenre:
            self.request_highlevel()
        if self.do_keybpm or self.do_sublowlevel:
            self.request_lowlevel()

    def request_lowlevel(self):
        self.debug("requesting lowlevel data")
        self.data_lowlevel = PENDING
        self.album.tagger.webservice.get(
            ACOUSTICBRAINZ_HOST,
            ACOUSTICBRAINZ_PORT,
            "/api/v1/low-level",
            partial(self.receive, "lowlevel"),
            priority=True,
            parse_response_type=None,
            queryargs=self.queryargs
        )
        self.album._requests += 1
    
    def request_highlevel(self):
        self.debug("requesting highlevel data")
        self.data_highlevel = PENDING
        self.album.tagger.webservice.get(
            ACOUSTICBRAINZ_HOST,
            ACOUSTICBRAINZ_PORT,
            "/api/v1/high-level",
            partial(self.receive, "highlevel"),
            priority=True,
            parse_response_type=None,
            queryargs=self.queryargs
        )
        self.album._requests += 1
              
    # Callback
    # -------------------------------------------------------------------------
 
    def receive(self, level, rawdata, _, error):
        try:
            if error:
                self.error("failed to fetch %s data", level)
                return
            
            try:
                data = load_json(rawdata)
                self.store(level, data)
            except (JSONDecodeError, TypeError, KeyError) as ex:
                self.error("failed to parse JSON data (%r)", ex)
                return
            
            self.debug("fetched %s data (pending requests: %i)", level, self.album._requests-1)
            if PENDING not in (self.data_highlevel, self.data_lowlevel):
                if self.do_simplemood:
                    self.process_simplemood()
                if self.do_simplegenre:
                    self.process_simplegenre()
                if self.do_fullhighlevel:
                    self.process_fullhighlevel()
                if self.do_keybpm:
                    self.process_keybpm()
                if self.do_sublowlevel:
                    self.process_sublowlevel()
        finally:
            self.album._requests -= 1
            if self.album._requests == 0:
                self.album._finalize_loading(None)
                
    def store(self, level, data):
        if level == LOWLEVEL:
            self.data_lowlevel = data[self.trackid]["0"]
        elif level == HIGHLEVEL:
            self.data_highlevel = data[self.trackid]["0"]["highlevel"]

    # Processing helper methods
    # -------------------------------------------------------------------------

    def filter_data(self, data, subset):
        result = {}
        for key, value in subset.items():
            if key in data:
                if isinstance(value, dict):
                    self.debug("filter_data : traversing %s", key)
                    result[key] = self.filter_data(data[key], value)
                else:
                    self.debug("filter_data : adding result %s", key)
                    result[key] = data[key]
            else:
                self.debug("filter_data : Subset key %s not found in data", key)
                continue
        self.debug("filter_data : result : %s", result)
        return result

    # Processing methods
    # -------------------------------------------------------------------------
    # (fill metadata with fetched data)
    
    def process_simplemood(self):
        self.debug("processing simplemood data")
        
        moods = []

        for classifier, data in self.data_highlevel.items():
            if "value" in data:
                value = data["value"]
                inverted = value.startswith("not_")
                if classifier.startswith("mood_") and not inverted:
                    moods.append(value)

        self.metadata["mood"] = moods
    
    def process_simplegenre(self):
        self.debug("processing simplegenre data")
        
        genres = []

        for classifier, data in self.data_highlevel.items():
            if "value" in data:
                value = data["value"]
                inverted = value.startswith("not_")
                if classifier.startswith("genre_") and not inverted:
                    genres.append(value)

        self.metadata["genre"] = genres
        
    def process_fullhighlevel(self):
        self.debug("processing fullhighlevel data")
        
        f_count, c_count = 0, 0
        for classifier, data in self.data_highlevel.items():
            classifier = classifier.lower()
            if "all" in data:
                c_count += 1
                for feature, proba in data["all"].items():
                    feature = feature.lower()
                    f_count += 1
                    self.metadata["ab:hi:{}:{}".format(classifier, feature)] = dump_json(proba)
            else:
                self.warning("fullhighlevel : ignored invalid classifier data (%s)", classifier)

        self.debug("fullhighlevel : parsed %d features from %d classifiers", f_count, c_count)
    
    def process_keybpm(self):
        self.debug("processing keybpm data")
        if "tonal" in self.data_lowlevel:
            tonal_data = self.data_lowlevel["tonal"]
            if "key_key" in tonal_data:
                key = tonal_data["key_key"]
                if "key_scale" in tonal_data:
                    if tonal_data["key_scale"] == "minor":
                        key += "m"
                self.metadata["key"] = key
                self.debug("track '%s' is in key %s", self.title, key)
        
        if "rhythm" in self.data_lowlevel:
            rhythm_data = self.data_lowlevel["rhythm"]
            if "bpm" in rhythm_data:
                self.metadata["bpm"] = bpm = int(rhythm_data["bpm"] + 0.5)
                self.debug("keybpm : Track '%s' has %s bpm", self.title, bpm)

    def process_sublowlevel(self):
        self.debug("processing sublowlevel data")
        subset = SUBLOWLEVEL_SUBSET
                             
        filtered_data = self.filter_data(self.data_lowlevel, subset)

        f_count, c_count = 0, 0
        for classifier, data in filtered_data.items():
            classifier = classifier.lower()
            c_count += 1
            for feature, proba in data.items():
                feature = feature.lower()
                f_count += 1
                self.metadata["ab:lo:{}:{}".format(classifier, feature)] = proba

        self.debug("sublowlevel : parsed %d features from %d classifiers", f_count, c_count)
        


# Plugin class
# =============================================================================
# (provides track processing callback)

class AcousticbrainzPlugin:
    
    def __init__(self):
        self.tracks = {}
    
    def process_track(self, album, metadata, _, release):
        track = Track(album, metadata)
        #tracks[track.trackid] = track
        track.process()


# Plugin options page
# =============================================================================
# (define plugin options and link with user interface)

class AcousticbrainzOptionsPage(OptionsPage):
    NAME = "AcousticBrainz"
    TITLE = "AcousticBrainz tags"
    PARENT = "plugins"
    
    options = [
        config.BoolOption("setting", "acousticbrainz_add_simplemood", True),
        config.BoolOption("setting", "acousticbrainz_add_simplegenre", False),
        config.BoolOption("setting", "acousticbrainz_add_keybpm", False),
        config.BoolOption("setting", "acousticbrainz_add_fullhighlevel", False),
        config.BoolOption("setting", "acousticbrainz_add_sublowlevel", False)
    ]

    def __init__(self, parent=None):
        super(AcousticbrainzOptionsPage, self).__init__(parent)
        self.ui = Ui_AcousticbrainzOptionsPage()
        self.ui.setupUi(self)
        
    def load(self):
        setting = config.setting
        self.ui.add_simplemood.setChecked(setting["acousticbrainz_add_simplemood"])
        self.ui.add_simplegenre.setChecked(setting["acousticbrainz_add_simplegenre"])
        self.ui.add_fullhighlevel.setChecked(setting["acousticbrainz_add_fullhighlevel"])
        self.ui.add_keybpm.setChecked(setting["acousticbrainz_add_keybpm"])
        self.ui.add_sublowlevel.setChecked(setting["acousticbrainz_add_sublowlevel"])
        
    def save(self):
        setting = config.setting
        setting["acousticbrainz_add_simplemood"] = self.ui.add_simplemood.isChecked()
        setting["acousticbrainz_add_simplegenre"] = self.ui.add_simplegenre.isChecked()
        setting["acousticbrainz_add_keybpm"] = self.ui.add_keybpm.isChecked()
        setting["acousticbrainz_add_fullhighlevel"] = self.ui.add_fullhighlevel.isChecked()
        setting["acousticbrainz_add_sublowlevel"] = self.ui.add_sublowlevel.isChecked()


plugin = AcousticbrainzPlugin()
register_track_metadata_processor(plugin.process_track)
register_options_page(AcousticbrainzOptionsPage)
