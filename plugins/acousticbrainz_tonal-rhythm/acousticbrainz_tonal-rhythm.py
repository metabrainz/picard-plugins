# -*- coding: utf-8 -*-
# Acousticbrainz Tonal/Rhythm plugin for Picard
# Copyright (C) 2015  Sophist
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

PLUGIN_NAME = u'AcousticBrainz Tonal-Rhythm'
PLUGIN_AUTHOR = u'Sophist'
PLUGIN_DESCRIPTION = u'''Add's the following tags:
<ul>
<li>Key (in ID3v2.3 format)</li>
<li>Beats Per Minute (BPM)</li>
</ul>
from the AcousticBrainz database.<br/><br/>
Note: This plugin requires Picard 1.4.'''
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.txt"
PLUGIN_VERSION = '0.1'
PLUGIN_API_VERSIONS = ["1.4.0", "2.0"] # Requires support for TKEY which is in 1.4

import json
from picard import config, log
from picard.util import LockableObject
from picard.metadata import register_track_metadata_processor
from functools import partial
from picard.webservice import REQUEST_DELAY

ACOUSTICBRAINZ_HOST = "acousticbrainz.org"
ACOUSTICBRAINZ_PORT = 80
REQUEST_DELAY[(ACOUSTICBRAINZ_HOST, ACOUSTICBRAINZ_PORT)] = 50

class AcousticBrainz_Key:

    def get_data(self, album, track_metadata, trackXmlNode, releaseXmlNode):
        recordingId = track_metadata['musicbrainz_recordingid']
        if recordingId:
            log.debug("%s: Add AcusticBrainz request for %s (%s)", PLUGIN_NAME, track_metadata['title'], recordingId)
            self.album_add_request(album)
            path = "/%s/low-level" % recordingId
            return album.tagger.xmlws.get(
                        ACOUSTICBRAINZ_HOST,
                        ACOUSTICBRAINZ_PORT,
                        path,
                        partial(self.process_data, album, track_metadata),
                        xml=False, priority=True, important=False)
        return

    def process_data(self, album, track_metadata, response, reply, error):
        if error:
            log.error("%s: Network error retrieving acousticBrainz data for recordingId %s",
                PLUGIN_NAME, track_metadata['musicbrainz_recordingid'])
            self.album_remove_request(album)
            return
        data = json.loads(response)
        if "tonal" in data:
            if "key_key" in data["tonal"]:
                key = data["tonal"]["key_key"]
                if "key_scale" in data["tonal"]:
                    scale = data["tonal"]["key_scale"]
                    if scale == "minor":
                        key += "m"
                track_metadata["key"] = key
                log.debug("%s: Track '%s' is in key %s", PLUGIN_NAME, track_metadata["title"], key)
        if "rhythm" in data:
            if "bpm" in data["rhythm"]:
                bpm = int(data["rhythm"]["bpm"] + 0.5)
                track_metadata["bpm"] = bpm
                log.debug("%s: Track '%s' has %s bpm", PLUGIN_NAME, track_metadata["title"], bpm)
        self.album_remove_request(album)

    def album_add_request(self, album):
        album._requests += 1

    def album_remove_request(self, album):
        album._requests -= 1
        if album._requests == 0:
            album._finalize_loading(None)

register_track_metadata_processor(AcousticBrainz_Key().get_data)
