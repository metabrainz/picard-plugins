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

PLUGIN_NAME = 'Artist Variables'
PLUGIN_AUTHOR = 'Bob Swift (rdswift)'
PLUGIN_DESCRIPTION = '''
This plugin provides specialized album and track variables for use in
naming scripts. It combines the functionality of the "Album Artist
Extension" and "RDS Naming Variables" plugins, although the variables
are provided with different names.  This will require changes to existing
scripts that used these previous plugins.
<br /><br />
The variables provided are:
<br /><br />
<strong>Album Variables</strong>
<ul>
<li><strong><i>_PriAArtistID</i></strong> - The ID of the primary / first album artist listed
<li><strong><i>_PriAArtistStd</i></strong> - The primary / first album artist listed (standardized)
<li><strong><i>_PriAArtistCred</i></strong> - The primary / first album artist listed (as credited)
<li><strong><i>_PriAArtistSort</i></strong> - The primary / first album artist listed (sort name)
<li><strong><i>_AdditionalAArtistID</i></strong> - The IDs of all album artists listed except for the primary / first artist, separated by a semicolon and space
<li><strong><i>_AdditionalAArtistStd</i></strong> - All album artists listed (standardized) except for the primary / first artist, separated with strings provided from the release entry
<li><strong><i>_AdditionalAArtistCred</i></strong> - All album artists listed (as credited) except for the primary / first artist, separated with strings provided from the release entry
<li><strong><i>_FullAArtistStd</i></strong> - All album artists listed (standardized), separated with strings provided from the release entry
<li><strong><i>_FullAArtistCred</i></strong> - All album artists listed (as credited), separated with strings provided from the release entry
<li><strong><i>_FullAArtistSort</i></strong> - All album artists listed (sort names), separated with strings provided from the release entry
<li><strong><i>_FullAArtistPriSort</i></strong> - The primary / first album artist listed (sort name) followed by all additional album artists (standardized), separated with strings provided from the release entry
<li><strong><i>_AArtistCount</i></strong> - The number of artists listed as album artists
</ul><br />
<strong>Track Variables</strong>
<ul>
<li><strong><i>_PriTArtistID</i></strong> - The ID of the primary / first track artist listed
<li><strong><i>_PriTArtistStd</i></strong> - The primary / first track artist listed (standardized)
<li><strong><i>_PriTArtistCred</i></strong> - The primary / first track artist listed (as credited)
<li><strong><i>_PriTArtistSort</i></strong> - The primary / first track artist listed (sort name)
<li><strong><i>_AdditionalTArtistID</i></strong> - The IDs of all track artists listed except for the primary / first artist, separated by a semicolon and space
<li><strong><i>_AdditionalTArtistStd</i></strong> - All track artists listed (standardized) except for the primary / first artist, separated with strings provided from the track entry
<li><strong><i>_AdditionalTArtistCred</i></strong> - All track artists listed (as credited) except for the primary / first artist, separated with strings provided from the track entry
<li><strong><i>_FullTArtistStd</i></strong> - All track artists listed (standardized), separated with strings provided from the track entry
<li><strong><i>_FullTArtistCred</i></strong> - All track artists listed (as credited), separated with strings provided from the track entry
<li><strong><i>_FullTArtistSort</i></strong> - All track artists listed (sort names), separated with strings provided from the track entry
<li><strong><i>_FullTArtistPriSort</i></strong> - The primary / first track artist listed (sort name) followed by all additional track artists (standardized), separated with strings provided from the track entry
<li><strong><i>_TArtistCount</i></strong> - The number of artists listed as track artists
</ul><br />
<strong>PLEASE NOTE</strong>: Tagger scripts are required to make use of these hidden
variables.
<br /><br />
Please see the <a href="https://github.com/rdswift/picard-plugins/blob/2.0_RDS_Plugins/plugins/artist_variables/docs/README.md">user guide</a> on GitHub for more information.
'''

PLUGIN_VERSION = "0.3"
PLUGIN_API_VERSIONS = ["2.0", "2.1"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

PLUGIN_USER_GUIDE_URL = "https://github.com/rdswift/picard-plugins/blob/2.0_RDS_Plugins/plugins/artist_variables/docs/README.md"

from picard import config, log
from picard.metadata import (register_album_metadata_processor,
                             register_track_metadata_processor)
from picard.plugin import PluginPriority


def process_artists(album_id, source_metadata, destination_metadata, source_type):
    metadata_type = 'release' if source_type == 'A' else 'track'
    # Test for valid metadata node for the release
    # The 'artist-credit' key should always be there.
    # This check is to avoid a runtime error if it doesn't exist for some reason.
    if 'artist-credit' in source_metadata:
        # Initialize variables to default values
        sort_pri_artist = ""
        std_artist = ""
        cred_artist = ""
        sort_artist = ""
        additional_std_artist = ""
        additional_cred_artist = ""
        artist_count = 0
        additional_artist_ids = []
        for artist_credit in source_metadata['artist-credit']:
            # Initialize temporary variables for each loop.
            temp_std_name = ""
            temp_cred_name = ""
            temp_sort_name = ""
            temp_phrase = ""
            temp_id = ""
            # Check if there is a 'joinphrase' specified.
            if 'joinphrase' in artist_credit:
                temp_phrase = artist_credit['joinphrase']
            else:
                metadata_error(album_id, 'artist-credit.joinphrase', metadata_type)
            # Check if there is a 'name' specified.
            if 'name' in artist_credit:
                temp_cred_name = artist_credit['name']
            else:
                metadata_error(album_id, 'artist-credit.name', metadata_type)
            # Check if there is an 'artist' specified.
            if 'artist' in artist_credit:
                # Check if there is an 'id' specified.
                if 'id' in artist_credit['artist']:
                    temp_id = artist_credit['artist']['id']
                else:
                    metadata_error(album_id, 'artist-credit.artist.id', metadata_type)
                # Check if there is a 'name' specified.
                if 'name' in artist_credit['artist']:
                    temp_std_name = artist_credit['artist']['name']
                else:
                    metadata_error(album_id, 'artist-credit.artist.name', metadata_type)
                if 'sort-name' in artist_credit['artist']:
                    temp_sort_name = artist_credit['artist']['sort-name']
                else:
                    metadata_error(album_id, 'artist-credit.artist.sort-name', metadata_type)
            else:
                metadata_error(album_id, 'artist-credit.artist', metadata_type)
            std_artist += temp_std_name + temp_phrase
            cred_artist += temp_cred_name + temp_phrase
            sort_artist += temp_sort_name + temp_phrase
            if artist_count < 1:
                if temp_id:
                    destination_metadata["~Pri{0}ArtistID".format(source_type,)] = temp_id
                destination_metadata["~Pri{0}ArtistStd".format(source_type,)] = temp_std_name
                destination_metadata["~Pri{0}ArtistCred".format(source_type,)] = temp_cred_name
                destination_metadata["~Pri{0}ArtistSort".format(source_type,)] = temp_sort_name
                sort_pri_artist += temp_sort_name + temp_phrase
            else:
                if temp_id:
                    additional_artist_ids.append(temp_id,)
                sort_pri_artist += temp_std_name + temp_phrase
                additional_std_artist += temp_std_name + temp_phrase
                additional_cred_artist += temp_cred_name + temp_phrase
            artist_count += 1
    else:
        metadata_error(album_id, 'artist-credit', metadata_type)
    if additional_artist_ids:
        destination_metadata["~Additional{0}ArtistID".format(source_type,)] = "; ".join(additional_artist_ids)
    if std_artist:
        destination_metadata["~Full{0}ArtistStd".format(source_type,)] = std_artist
    if cred_artist:
        destination_metadata["~Full{0}ArtistCred".format(source_type,)] = cred_artist
    if additional_std_artist:
        destination_metadata["~Additional{0}ArtistStd".format(source_type,)] = additional_std_artist
    if additional_cred_artist:
        destination_metadata["~Additional{0}ArtistCred".format(source_type,)] = additional_cred_artist
    if sort_pri_artist:
        destination_metadata["~Full{0}ArtistPriSort".format(source_type,)] = sort_pri_artist
    if sort_artist:
        destination_metadata["~Full{0}ArtistSort".format(source_type,)] = sort_artist
    if artist_count:
        destination_metadata["~{0}ArtistCount".format(source_type,)] = artist_count
    return None


def make_album_vars(album, album_metadata, release_metadata):
    album_id = release_metadata['id'] if release_metadata else 'No Album ID'
    process_artists(album_id, release_metadata, album_metadata, 'A')
    return None


def make_track_vars(album, album_metadata, track_metadata, release_metadata):
    album_id = release_metadata['id'] if release_metadata else 'No Album ID'
    process_artists(album_id, track_metadata, album_metadata, 'T')
    return None


def metadata_error(album_id, metadata_element, metadata_group):
    log.error("%s: %r: Missing '%s' in %s metadata.",
            PLUGIN_NAME, album_id, metadata_element, metadata_group)


# Register the plugin to run at a LOW priority so that other plugins that
# modify the artist information can complete their processing and this plugin
# is working with the latest updated data.
register_album_metadata_processor(make_album_vars, priority=PluginPriority.LOW)
register_track_metadata_processor(make_track_vars, priority=PluginPriority.LOW)
