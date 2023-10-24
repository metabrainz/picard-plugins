# -*- coding: utf-8 -*-
# AcousticBrainz plugin for Picard
#
# Copyright (C) 2021 Wargreen <wargreen@lebib.org>
# Copyright (C) 2021 Philipp Wolfer <ph.wolfer@gmail.com>
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
                 'Hugo Geoffroy "pistache" <pistache@lebib.org>, '
                 'Philipp Wolfer <ph.wolfer@gmail.com>, '
                 'Regorxxx <regorxxx@protonmail.com>')
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
PLUGIN_VERSION = "2.2.3"
PLUGIN_API_VERSIONS = ["2.0", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7"]

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

from functools import partial
from json import dumps as dump_json

from picard import (
    config,
    log,
)
from picard.metadata import (
    register_album_metadata_processor,
    register_track_metadata_processor,
)
from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.webservice import ratecontrol
from picard.plugins.acousticbrainz.ui_options_acousticbrainz_tags import Ui_AcousticBrainzOptionsPage

ratecontrol.set_minimum_delay((ACOUSTICBRAINZ_HOST, ACOUSTICBRAINZ_PORT), 1000)

# Constants
# =============================================================================

LOWLEVEL = "lowlevel"
HIGHLEVEL = "highlevel"


# Logging utilities
# -------------------------------------------------------------------------

def log_msg(logger, text, *args):
    logger("%s: " + text, PLUGIN_NAME, *args)

def debug(*args):
    log_msg(log.debug, *args)

def warning(*args):
    log_msg(log.warning, *args)

def error(*args):
    log_msg(log.error, *args)


# TrackDataProcessor class
# =============================================================================
# (used to apply AcousticBrainz data to Track metadata)

class TrackDataProcessor:
    def __init__(self, recording_id, metadata, level, data, files=None):
        self.recording_id = recording_id
        self.metadata = metadata
        self.level = level
        self.data = self._extract_data(data)
        self.files = files
        self.do_simplemood = config.setting["acousticbrainz_add_simplemood"]
        self.simplemood_tagname = config.setting["acousticbrainz_simplemood_tagname"]
        self.do_simplegenre = config.setting["acousticbrainz_add_simplegenre"]
        self.simplegenre_tagname = config.setting["acousticbrainz_simplegenre_tagname"]
        self.do_keybpm = config.setting["acousticbrainz_add_keybpm"]
        self.do_fullhighlevel = config.setting["acousticbrainz_add_fullhighlevel"]
        self.do_sublowlevel = config.setting["acousticbrainz_add_sublowlevel"]

    # Logging utilities
    # -------------------------------------------------------------------------

    def log(self, logger, text, *args):
        log_msg(logger, "[%s: %s] " + text, self.shortid, self.title, *args)

    def debug(self, *args):
        self.log(log.debug, *args)

    def warning(self, *args):
        self.log(log.warning, *args)

    def error(self, *args):
        self.log(log.error, *args)

    # Read-only properties
    # -------------------------------------------------------------------------

    @property
    def shortid(self):
        return self.recording_id[:8]

    @property
    def title(self):
        return self.metadata["title"]

    # Callback
    # -------------------------------------------------------------------------

    def process(self):
        if not self.data:
            self.warning('No %s data for track %s', self.level, self.recording_id)

        if self.level == HIGHLEVEL:
            if self.do_simplemood:
                self.process_simplemood()
            if self.do_simplegenre:
                self.process_simplegenre()
            if self.do_fullhighlevel:
                self.process_fullhighlevel()

        if self.level == LOWLEVEL:
            if self.do_keybpm:
                self.process_keybpm()
            if self.do_sublowlevel:
                self.process_sublowlevel()

    # Processing helper methods
    # -------------------------------------------------------------------------

    def _extract_data(self, data):
        if not self.recording_id in data:
            return {}
        if self.level == LOWLEVEL:
            return data[self.recording_id]["0"]
        elif self.level == HIGHLEVEL:
            return data[self.recording_id]["0"]["highlevel"]

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

    def update_metadata(self, name, values):
        self.metadata[name] = values
        if self.files:
            for file in self.files:
                file.metadata[name] = values

    # Processing methods
    # -------------------------------------------------------------------------
    # (fill metadata with fetched data)

    def process_simplemood(self):
        self.debug("processing simplemood data")

        mood_tagname = self.simplemood_tagname;
        moods = []

        for classifier, data in self.data.items():
            if "value" in data:
                value = data["value"]
                inverted = value.startswith("not_")
                if classifier.startswith("mood_") and not inverted:
                    moods.append(value)

        self.update_metadata(mood_tagname, moods)

    def process_simplegenre(self):
        self.debug("processing simplegenre data")

        genre_tagname = self.simplegenre_tagname;
        genres = []

        for classifier, data in self.data.items():
            if "value" in data:
                value = data["value"]
                inverted = value.startswith("not_")
                if classifier.startswith("genre_") and not inverted:
                    genres.append(value)

        self.update_metadata(genre_tagname, genres)

    def process_fullhighlevel(self):
        self.debug("processing fullhighlevel data")

        f_count, c_count = 0, 0
        for classifier, data in self.data.items():
            classifier = classifier.lower()
            if "all" in data:
                c_count += 1
                for feature, proba in data["all"].items():
                    feature = feature.lower()
                    f_count += 1
                    self.update_metadata("ab:hi:{}:{}".format(classifier, feature), dump_json(proba))
            else:
                self.warning("fullhighlevel : ignored invalid classifier data (%s)", classifier)

        self.debug("fullhighlevel : parsed %d features from %d classifiers", f_count, c_count)

    def process_keybpm(self):
        self.debug("processing keybpm data")
        if "tonal" in self.data:
            tonal_data = self.data["tonal"]
            if "key_key" in tonal_data:
                key = tonal_data["key_key"]
                if "key_scale" in tonal_data:
                    if tonal_data["key_scale"] == "minor":
                        key += "m"
                self.update_metadata('key', key)
                self.debug("track '%s' is in key %s", self.title, key)

        if "rhythm" in self.data:
            rhythm_data = self.data["rhythm"]
            if "bpm" in rhythm_data:
                bpm = int(rhythm_data["bpm"] + 0.5)
                self.update_metadata('bpm', bpm)
                self.debug("keybpm : Track '%s' has %s bpm", self.title, bpm)

    def process_sublowlevel(self):
        self.debug("processing sublowlevel data")
        subset = SUBLOWLEVEL_SUBSET

        filtered_data = self.filter_data(self.data, subset)

        f_count, c_count = 0, 0
        for classifier, data in filtered_data.items():
            classifier = classifier.lower()
            c_count += 1
            for feature, proba in data.items():
                feature = feature.lower()
                f_count += 1
                self.update_metadata("ab:lo:{}:{}".format(classifier, feature), proba)

        self.debug("sublowlevel : parsed %d features from %d classifiers", f_count, c_count)


class AcousticBrainzRequest:

    MAX_BATCH_SIZE = 25

    def __init__(self, webservice, recording_ids):
        self.webservice = webservice
        self.recording_ids = recording_ids

    def request_highlevel(self, callback):
        self._batch('high-level', self.recording_ids, callback, {})

    def request_lowlevel(self, callback):
        self._batch('low-level', self.recording_ids, callback, {})

    def _batch(self, action, recording_ids, callback, result, response=None, reply=None, error=None):
        if response and not error:
            self._merge_results(result, response)

        if not recording_ids or error:
            callback(result, error)
            return

        batch = recording_ids[:self.MAX_BATCH_SIZE]
        recording_ids = recording_ids[self.MAX_BATCH_SIZE:]
        self._do_request(action, batch,
            callback=partial(self._batch, action, recording_ids, callback, result))

    def _do_request(self, action, recording_ids, callback):
        self.webservice.get(
            ACOUSTICBRAINZ_HOST,
            ACOUSTICBRAINZ_PORT,
            '/api/v1/%s' % action,
            callback,
            priority=True,
            parse_response_type='json',
            queryargs=self._get_query_args(action, recording_ids)
        )

    def _get_query_args(self, action, recording_ids):
        queryargs = {
            'recording_ids': ';'.join(recording_ids),
        }
        if action == 'high-level':
            queryargs['map_classes'] = 'true'
        return queryargs

    def _merge_results(self, full, new):
        mapping = new.get('mbid_mapping', {})
        new = {mapping.get(k, k): v for (k, v) in new.items() if k != 'mbid_mapping'}
        full.update(new)


# Plugin class
# =============================================================================
# (provides track processing callback)

class AcousticBrainzPlugin:

    result_cache = {
        LOWLEVEL: {},
        HIGHLEVEL: {},
    }

    def process_album(self, album, metadata, release):
        debug('Processing album %s', album.id)
        recording_ids = self.get_recording_ids(release)
        self.run_requests(album, recording_ids, self.album_callback)

    def process_track(self, album, metadata, track_node, release_node):
        # Run requests for standalone recordings
        if not release_node and 'id' in track_node:
            recording_id = track_node['id']
            debug('Processing recording %s', recording_id)
            self.run_requests(album, [recording_id], partial(self.nat_callback, recording_id))
        # Apply metadata changes for already loaded results for album tracks
        elif 'recording' in track_node:
            recording_id = track_node['recording']['id']
            for level in (LOWLEVEL, HIGHLEVEL):
                result = self.result_cache[level].get(album.id)
                if result:
                    self.apply_result(recording_id, metadata, level, result)

    def run_requests(self, album, recording_ids, callback):
        request = AcousticBrainzRequest(album.tagger.webservice, recording_ids)
        if self.do_highlevel:
            album._requests += 1
            request.request_highlevel(partial(callback, HIGHLEVEL, album))
        if self.do_lowlevel:
            album._requests += 1
            request.request_lowlevel(partial(callback, LOWLEVEL, album))

    @property
    def do_highlevel(self):
        return (config.setting["acousticbrainz_add_simplemood"]
            or config.setting["acousticbrainz_add_simplegenre"]
            or config.setting["acousticbrainz_add_fullhighlevel"])

    @property
    def do_lowlevel(self):
        return (config.setting["acousticbrainz_add_keybpm"]
            or config.setting["acousticbrainz_add_sublowlevel"])

    def get_recording_ids(self, release):
        return [track['recording']['id'] for track in self.iter_tracks(release)]

    @staticmethod
    def iter_tracks(release):
        for media in release['media']:
            if 'pregap' in media:
                yield media['pregap']

            if 'tracks' in media:
                yield from media['tracks']

            if 'data-tracks' in media:
                yield from media['data-tracks']

    def album_callback(self, level, album, result=None, error=None):
        if not error:
            # Store the result, the actual processing will be done by the
            # track metadata processor.
            self.result_cache[level][album.id] = result
            album.run_when_loaded(partial(self.clear_cache, level, album))
        album._requests -= 1
        album._finalize_loading(error)

    def nat_callback(self, recording_id, level, album, result=None, error=None):
        for track in album.tracks:
            if track.id == recording_id:
                self.apply_result(track.id, track.metadata, level, result, files=track.files)

    def apply_result(self, recording_id, metadata, level, result, files=None):
        debug('Updating recording %s with %s results', recording_id, level)
        processor = TrackDataProcessor(recording_id, metadata, level, result, files=files)
        processor.process()

    def clear_cache(self, level, album):
        try:
            del self.result_cache[level][album.id]
        except KeyError:
            pass


# Plugin options page
# =============================================================================
# (define plugin options and link with user interface)

class AcousticBrainzOptionsPage(OptionsPage):
    NAME = "acousticbrainz_tags"
    TITLE = "AcousticBrainz tags"
    PARENT = "plugins"

    options = [
        config.BoolOption("setting", "acousticbrainz_add_simplemood", True),
        config.TextOption("setting", "acousticbrainz_simplemood_tagname", "ab:mood"),
        config.BoolOption("setting", "acousticbrainz_add_simplegenre", True),
        config.TextOption("setting", "acousticbrainz_simplegenre_tagname", "ab:genre"),
        config.BoolOption("setting", "acousticbrainz_add_keybpm", False),
        config.BoolOption("setting", "acousticbrainz_add_fullhighlevel", False),
        config.BoolOption("setting", "acousticbrainz_add_sublowlevel", False)
    ]

    def __init__(self, parent=None):
        super(AcousticBrainzOptionsPage, self).__init__(parent)
        self.ui = Ui_AcousticBrainzOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        setting = config.setting
        self.ui.add_simplemood.setChecked(setting["acousticbrainz_add_simplemood"])
        self.ui.simplemood_tagname.setText(setting["acousticbrainz_simplemood_tagname"])
        self.ui.add_simplegenre.setChecked(setting["acousticbrainz_add_simplegenre"])
        self.ui.simplegenre_tagname.setText(setting["acousticbrainz_simplegenre_tagname"])
        self.ui.add_fullhighlevel.setChecked(setting["acousticbrainz_add_fullhighlevel"])
        self.ui.add_keybpm.setChecked(setting["acousticbrainz_add_keybpm"])
        self.ui.add_sublowlevel.setChecked(setting["acousticbrainz_add_sublowlevel"])

    def save(self):
        setting = config.setting
        setting["acousticbrainz_add_simplemood"] = self.ui.add_simplemood.isChecked()
        setting["acousticbrainz_simplemood_tagname"] = str(self.ui.simplemood_tagname.text())
        setting["acousticbrainz_add_simplegenre"] = self.ui.add_simplegenre.isChecked()
        setting["acousticbrainz_simplegenre_tagname"] = str(self.ui.simplegenre_tagname.text())
        setting["acousticbrainz_add_keybpm"] = self.ui.add_keybpm.isChecked()
        setting["acousticbrainz_add_fullhighlevel"] = self.ui.add_fullhighlevel.isChecked()
        setting["acousticbrainz_add_sublowlevel"] = self.ui.add_sublowlevel.isChecked()


plugin = AcousticBrainzPlugin()
register_album_metadata_processor(plugin.process_album)
register_track_metadata_processor(plugin.process_track)
register_options_page(AcousticBrainzOptionsPage)
