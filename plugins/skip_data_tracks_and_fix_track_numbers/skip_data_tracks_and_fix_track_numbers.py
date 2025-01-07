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
This plugin intends to present the track list in line with digital music platforms or CD ripper (re-)distributors. For example:
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


def remove_datatracks_from_release(album, metadata, release):
    try:
        log.info("{0}: Infomation: {1}".format(PLUGIN_NAME, "Removing data tracks / silence tracks from release "+release['title'],))
        for disc in release['media']:
            # Assuming that MusicBrainz includes a pregap track in the tracklist only if it's an audio track, so that pregap tracks (if exist) will never be a data track.
            datatrack_positions = []
            for i in reversed(range(len(disc['tracks']))):
                track = disc['tracks'][i]
                # This is a data track if:
                # Track Title / Recording Title is [data track], or Track Artist / Recording Artist is [data]
                # Bonus: also skip when Track Title / Recording Title is [silence]
                if track['title'] == '[data track]' \
                   or track['recording']['title'] == '[data track]' \
                   or track['artist-credit'][0]['artist']['name'] == '[data]' \
                   or track['recording']['artist-credit'][0]['artist']['name'] == '[data]' \
                   or track['title'] == '[silence]' \
                   or track['recording']['title'] == '[silence]' :
                    # The track['number'] field usually conforms with the %_musicbrainz_tracknumber% metadata, which can be vinyl numbering (A1, A2…). This is not to be used.
                    # Assuming that the track['position'] field coincides with the usual %tracknumber% metadata, which are integers starting from 1, even when a pregap track exists in the medium (which is in the disc['pregap'] field with a disc['pregap']['position'] field equal to 0).
                    datatrack_positions.append(track['position'])
                    del disc['tracks'][i]
            disc['track-count'] = len(disc['tracks'])
            if len(datatrack_positions) != 0:
                log.info("{0}: Infomation: {1}".format(PLUGIN_NAME, "Removed data tracks / silence tracks of positions: "+str(sorted(datatrack_positions)),))
            for track in disc['tracks']:
                position = track['position']
                number_to_skip = len([p for p in datatrack_positions if p < position])
                track['position'] = position - number_to_skip
            # Assuming that after the remove_datatracks_from_release function call, MusicBrainz Picard will infer / calculate the metadata %tracknumber% %totaltracks% %_absolutetracknumber% %_totalalbumtracks% from track['position'] fields of the modified release Object, that nothing else is needed to care about.
    except Exception as ex:
        log.error("{0}: Error: {1}".format(PLUGIN_NAME, ex,))

def doublecheck_metadata(album, metadata, track, release):
    try:
        if metadata['~datatrack']:
            log.warning("{0}: Warning: {1}".format(PLUGIN_NAME, "Track "+metadata['tracknumber']+" "+metadata['title']+" is marked as a data track by its metadata %_datatrack%, but its naming doesn't follow the [data] - [data track] rule. Please manually decide whether it is a data track and fix tracknumbers.",))
    except Exception as ex:
        log.error("{0}: Error: {1}".format(PLUGIN_NAME, ex,))


register_album_metadata_processor(remove_datatracks_from_release, priority=PluginPriority.HIGH)
register_track_metadata_processor(doublecheck_metadata, priority=PluginPriority.HIGH)

