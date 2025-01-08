# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 cerenkov (crnkv)
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

PLUGIN_NAME = 'Skip Data Tracks and Fix Track Numbers'
PLUGIN_AUTHOR = 'cerenkov (crnkv)'
PLUGIN_DESCRIPTION = '''
Skip and remove all data tracks and special silence tracks once the album is loaded. Also shift and fix the track numbers.
<br />
This plugin intends to present the track list in line with online digital music platforms or CD ripper (re-)distributors. For example:
<ul>
<li>Track #00: [pregap] audio track        -> No change. Maintain track number #00</li>
<li>Track #01: [data track]                -> Remove</li>
<li>Track #02: audio track                 -> Change track number to #01</li>
<li>Track #03: [data track]                -> Remove</li>
<li>Track #04: audio track                 -> Change track number to #02</li>
<li>Track #05: [crowd noise] yet still an audio track -> Change track number to #03</li>
<li>Track #06: [silence] empty audio track -> Remove</li>
<li>Track #07: hidden audio track          -> Change track number to #04</li>
<li> -- totaltracks: 8 -- </li>
</ul>
The cleaned outcome will be like:
<ul>
<li>Track #00: [pregap] audio track</li>
<li>Track #01: audio track</li>
<li>Track #02: audio track</li>
<li>Track #03: [crowd noise] yet still an audio track</li>
<li>Track #04: hidden audio track</li>
<li> -- totaltracks: 5 -- </li>
</ul>
This is automatic once the album is loaded. Users wouldn't be aware of the existence of data tracks and silence tracks.
<br />
Examples: releases of MBID 9cd9e81a-2dab-46d0-988e-bb486ddc1b05 and 9c0b5a23-ca6e-4b4e-be2f-98280cf56c88
<br /><br />
Its difference with a similar-purpose script of <a href="https://github.com/rdswift/picard-plugins/blob/2.0_RDS_Plugins/plugins/persistent_variables/docs/README.md#example-5">Persistent Variables</a> is that this plugin can skip any number of data tracks on any positions, and that the hidden variables %_absolutetracknumber% and %_totalalbumtracks% will also be fixed.
<br /><br />
More information on special purpose track titles: <a href="https://musicbrainz.org/doc/Style/Unknown_and_untitled/Special_purpose_track_title">https://musicbrainz.org/doc/Style/Unknown_and_untitled/Special_purpose_track_title</a>
'''
PLUGIN_VERSION = '0.1'
PLUGIN_API_VERSIONS = ['2.0', '2.7', '2.8', '2.9']
PLUGIN_LICENSE = 'GPL-2.0-or-later'
PLUGIN_LICENSE_URL = 'https://www.gnu.org/licenses/gpl-2.0.html'

from picard import log
from picard.metadata import (register_album_metadata_processor, register_track_metadata_processor)
from picard.plugin import PluginPriority


# This is a data track if:
# Track Title / Recording Title is [data track], or Track Artist / Recording Artist is [data]
# Bonus: also skip when Track Title / Recording Title is [silence]
# See: https://github.com/metabrainz/picard/blob/master/picard/track.py#L315 for the method '_customize_metadata(self)'
def isDataTrack(track):
    return track.get('title', '') == '[data track]' \
           or track.get('recording', {}).get('title', '') == '[data track]' \
           or track.get('artist-credit', [{}])[0].get('artist', {}).get('name', '') == '[data]' \
           or track.get('recording', {}).get('artist-credit', [{}])[0].get('artist', {}).get('name', '') == '[data]' \
           or track.get('title', '') == '[silence]' \
           or track.get('recording', {}).get('title', '') == '[silence]'

def remove_datatracks_from_release(album, metadata, release):
    try:
        for disc in release['media']:
            datatrack_positions = []

            # Examine the pregap track, assuming its position is 0
            if isDataTrack(disc.get('pregap', {})):
                del disc['pregap'];

            # Remove the 'data-tracks' node (never seen in real album releases, not sure about its structure)
            # Its impact on the track positions in the 'tracks' node is unverified
            # See: https://github.com/metabrainz/picard/blob/master/picard/album.py#L447 for the method '_load_tracks(self)'
            if 'data-tracks' in disc:
                for track in disc['data-tracks']:
                    if 'position' in track:
                        datatrack_positions.append(track['position'])
                del disc['data-tracks']

            # Examine each track under the 'tracks' node
            for i in reversed(range(len(disc['tracks']))):
                track = disc['tracks'][i]
                if isDataTrack(track):
                    # The track['number'] field usually conforms with the %_musicbrainz_tracknumber% metadata, which can be vinyl numbering (A1, A2…). This is not to be used.
                    # Assuming that the track['position'] field coincides with the usual %tracknumber% metadata, which are integers starting from 1, even when a pregap track exists in the medium.
                    datatrack_positions.append(track['position'])
                    del disc['tracks'][i]

            disc['track-count'] = len(disc['tracks']) # pregap doesn't count as seen in real album releases
            for track in disc['tracks']:
                position = track['position']
                number_to_skip = len([p for p in datatrack_positions if p < position])
                track['position'] = position - number_to_skip
            if len(datatrack_positions) > 0:
                log.info("[Info] Removed {0} data / silence tracks, original positions: {1}".format(len(datatrack_positions), sorted(datatrack_positions)))
            # Assuming that after the remove_datatracks_from_release function call, MusicBrainz Picard will infer / calculate the metadata %tracknumber% %totaltracks% %_absolutetracknumber% %_totalalbumtracks% from track['position'] fields of the modified release Object, that nothing else is needed to care about.
    except Exception as ex:
        log.error("[Error] {0}".format(ex))

register_album_metadata_processor(remove_datatracks_from_release, priority=PluginPriority.HIGH)

