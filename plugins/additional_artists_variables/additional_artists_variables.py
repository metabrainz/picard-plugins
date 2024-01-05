# -*- coding: utf-8 -*-
#
# Copyright (C) 2018-2023 Bob Swift (rdswift)
# Copyright (C) 2023 Ruud van Asseldonk (ruuda)
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

PLUGIN_NAME = 'Additional Artists Variables'
PLUGIN_AUTHOR = 'Bob Swift (rdswift)'
PLUGIN_DESCRIPTION = '''
This plugin provides specialized album and track variables for use in
naming scripts. It is based on the "Album Artist Extension" plugin, but
expands the functionality to also include track artists. Note that it
cannot be used as a direct drop-in replacement for the "Album Artist
Extension" plugin because the variables are provided with different
names.  This will require changes to existing scripts if switching to
this plugin.
<br /><br />
Please see the <a href="https://github.com/rdswift/picard-plugins/blob/2.0_RDS_Plugins/plugins/additional_artists_variables/docs/README.md">user guide</a> on GitHub for more information.
'''
PLUGIN_VERSION = '0.9'
PLUGIN_API_VERSIONS = ['2.0', '2.1', '2.2', '2.7', '2.9', '2.10']
PLUGIN_LICENSE = 'GPL-2.0-or-later'
PLUGIN_LICENSE_URL = 'https://www.gnu.org/licenses/gpl-2.0.html'

PLUGIN_USER_GUIDE_URL = 'https://github.com/rdswift/picard-plugins/blob/2.0_RDS_Plugins/plugins/additional_artists_variables/docs/README.md'

from operator import itemgetter

from picard import config, log
from picard.metadata import (register_album_metadata_processor,
                             register_track_metadata_processor)
from picard.plugin import PluginPriority


ID_ALIASES_ARTIST_NAME = '894afba6-2816-3c24-8072-eadb66bd04bc'
ID_ALIASES_LEGAL_NAME = 'd4dcd0c0-b341-3612-a332-c0ce797b25cf'


def process_artists(album_id, source_metadata, destination_metadata, source_type):
    # Test for valid metadata node.
    # The 'artist-credit' key should always be there.
    # This check is to avoid a runtime error if it doesn't exist for some reason.
    if 'artist-credit' in source_metadata:
        # Initialize variables to default values
        sort_pri_artist = ''
        sort_pri_artist_cred = ''
        std_artist = ''
        cred_artist = ''
        sort_artist = ''
        cred_sort_artist = ''
        legal_artist = ''
        additional_std_artist = ''
        additional_cred_artist = ''
        additional_sort_artist = ''
        additional_cred_sort_artist = ''
        additional_legal_artist = ''
        std_artist_list = []
        cred_artist_list = []
        sort_artist_list = []
        cred_sort_artist_list = []
        legal_artist_list = []
        artist_count = 0
        artist_ids = []
        artist_types = []
        artist_join_phrases = []
        for artist_credit in source_metadata['artist-credit']:
            # Initialize temporary variables for each loop.
            temp_std_name = ''
            temp_sort_name = ''
            temp_cred_name = ''
            temp_cred_sort_name = ''
            temp_legal_name = ''
            temp_legal_sort_name = ''
            temp_phrase = ''
            temp_id = ''
            temp_type = ''
            # Check if there is a 'joinphrase' specified.
            if 'joinphrase' in artist_credit:
                temp_phrase = artist_credit['joinphrase']
            else:
                metadata_error(album_id, 'artist-credit.joinphrase', source_type)
            # Check if there is a 'name' specified.
            if 'name' in artist_credit:
                temp_cred_name = artist_credit['name']
            else:
                metadata_error(album_id, 'artist-credit.name', source_type)
            # Check if there is an 'artist' specified.
            if 'artist' in artist_credit:
                if 'id' in artist_credit['artist']:
                    temp_id = artist_credit['artist']['id']
                else:
                    metadata_error(album_id, 'artist-credit.artist.id', source_type)
                if 'name' in artist_credit['artist']:
                    temp_std_name = artist_credit['artist']['name']
                else:
                    metadata_error(album_id, 'artist-credit.artist.name', source_type)
                if 'sort-name' in artist_credit['artist']:
                    temp_sort_name = artist_credit['artist']['sort-name']
                    temp_cred_sort_name = temp_sort_name
                else:
                    metadata_error(album_id, 'artist-credit.artist.sort-name', source_type)
                if 'type' in artist_credit['artist']:
                    temp_type = artist_credit['artist']['type']
                else:
                    metadata_error(album_id, 'artist-credit.artist.type', source_type)
                if 'aliases' in artist_credit['artist']:
                    for item in artist_credit['artist']['aliases']:
                        if 'type-id' in item and item['type-id'] == ID_ALIASES_LEGAL_NAME:
                            if 'ended' in item and not item['ended']:
                                if 'name' in item:
                                    temp_legal_name = item['name']
                                if 'sort-name' in item:
                                    temp_legal_sort_name = item['sort-name']
                        if 'type-id' in item and item['type-id'] == ID_ALIASES_ARTIST_NAME:
                            if 'name' in item and 'sort-name' in item and str(item['name']).lower() == temp_cred_name.lower():
                                temp_cred_sort_name = item['sort-name']
                tag_list = []
                if config.setting['max_genres']:
                    for tag_type in ['user-genres', 'genres', 'user-tags', 'tags']:
                        if tag_type in artist_credit['artist']:
                            for item in sorted(sorted(artist_credit['artist'][tag_type], key=itemgetter('name')), key=itemgetter('count'), reverse=True):
                                if item['count'] > 0:
                                    tag_list.append(item['name'])
                    tag_list = tag_list[:config.setting['max_genres']]
            else:
                # No 'artist' specified.  Log as an error.
                metadata_error(album_id, 'artist-credit.artist', source_type)
            std_artist += temp_std_name + temp_phrase
            cred_artist += temp_cred_name + temp_phrase
            sort_artist += temp_sort_name + temp_phrase
            cred_sort_artist += temp_cred_sort_name + temp_phrase
            artist_types.append(temp_type if temp_type else 'unknown',)
            artist_join_phrases.append(temp_phrase if temp_phrase else '\u200B',)
            if temp_legal_name:
                legal_artist += temp_legal_name + temp_phrase
                legal_artist_list.append(temp_legal_name,)
            else:
                # Use standardized name for combined string if legal name not available
                legal_artist += temp_std_name + temp_phrase
                # Use 'n/a' for list if legal name not available
                legal_artist_list.append('n/a',)
            if temp_std_name:
                std_artist_list.append(temp_std_name,)
            if temp_sort_name:
                sort_artist_list.append(temp_sort_name,)
            if temp_cred_name:
                cred_artist_list.append(temp_cred_name,)
            if temp_cred_sort_name:
                cred_sort_artist_list.append(temp_cred_sort_name,)
            if temp_id:
                artist_ids.append(temp_id,)
            if artist_count < 1:
                if temp_id:
                    destination_metadata['~artists_{0}_primary_id'.format(source_type,)] = temp_id
                destination_metadata['~artists_{0}_primary_std'.format(source_type,)] = temp_std_name
                destination_metadata['~artists_{0}_primary_cred'.format(source_type,)] = temp_cred_name
                destination_metadata['~artists_{0}_primary_sort'.format(source_type,)] = temp_sort_name
                destination_metadata['~artists_{0}_primary_cred_sort'.format(source_type,)] = temp_cred_sort_name
                destination_metadata['~artists_{0}_primary_legal'.format(source_type,)] = temp_legal_name
                destination_metadata['~artists_{0}_primary_sort_legal'.format(source_type,)] = temp_legal_sort_name
                sort_pri_artist += temp_sort_name + temp_phrase
                sort_pri_artist_cred += temp_cred_sort_name + temp_phrase
                if tag_list and source_type == 'album':
                    destination_metadata['~artists_{0}_primary_tags'.format(source_type,)] = tag_list
            else:
                sort_pri_artist += temp_std_name + temp_phrase
                additional_std_artist += temp_std_name + temp_phrase
                additional_cred_artist += temp_cred_name + temp_phrase
                additional_sort_artist += temp_sort_name + temp_phrase
                if temp_legal_name:
                    additional_legal_artist += temp_legal_name + temp_phrase
                else:
                    additional_legal_artist += temp_std_name + temp_phrase
                if temp_cred_sort_name:
                    additional_cred_sort_artist += temp_cred_sort_name + temp_phrase
                    sort_pri_artist_cred += temp_cred_sort_name + temp_phrase
                else:
                    additional_cred_sort_artist += temp_sort_name + temp_phrase
                    sort_pri_artist_cred += temp_sort_name + temp_phrase
        artist_count += 1
    else:
        # No valid metadata found.  Log as error.
        metadata_error(album_id, 'artist-credit', source_type)
    additional_std_artist_list = std_artist_list[1:]
    additional_cred_artist_list = cred_artist_list[1:]
    additional_sort_artist_list = sort_artist_list[1:]
    additional_cred_sort_artist_list = cred_sort_artist_list[1:]
    additional_legal_artist_list = legal_artist_list[1:]
    additional_artist_ids = artist_ids[1:]
    if additional_artist_ids:
        destination_metadata['~artists_{0}_additional_id'.format(source_type,)] = additional_artist_ids
    if additional_std_artist:
        destination_metadata['~artists_{0}_additional_std'.format(source_type,)] = additional_std_artist
    if additional_cred_artist:
        destination_metadata['~artists_{0}_additional_cred'.format(source_type,)] = additional_cred_artist
    if additional_sort_artist:
        destination_metadata['~artists_{0}_additional_sort'.format(source_type,)] = additional_sort_artist
    if additional_cred_sort_artist:
        destination_metadata['~artists_{0}_additional_cred_sort'.format(source_type,)] = additional_cred_sort_artist
    if additional_legal_artist:
        destination_metadata['~artists_{0}_additional_legal'.format(source_type,)] = additional_legal_artist
    if additional_std_artist_list:
        destination_metadata['~artists_{0}_additional_std_multi'.format(source_type,)] = additional_std_artist_list
    if additional_cred_artist_list:
        destination_metadata['~artists_{0}_additional_cred_multi'.format(source_type,)] = additional_cred_artist_list
    if additional_sort_artist_list:
        destination_metadata['~artists_{0}_additional_sort_multi'.format(source_type,)] = additional_sort_artist_list
    if additional_cred_sort_artist_list:
        destination_metadata['~artists_{0}_additional_cred_sort_multi'.format(source_type,)] = additional_cred_sort_artist_list
    if additional_legal_artist_list:
        destination_metadata['~artists_{0}_additional_legal_multi'.format(source_type,)] = additional_legal_artist_list
    if std_artist:
        destination_metadata['~artists_{0}_all_std'.format(source_type,)] = std_artist
    if cred_artist:
        destination_metadata['~artists_{0}_all_cred'.format(source_type,)] = cred_artist
    if cred_sort_artist:
        destination_metadata['~artists_{0}_all_cred_sort'.format(source_type,)] = cred_sort_artist
    if sort_artist:
        destination_metadata['~artists_{0}_all_sort'.format(source_type,)] = sort_artist
    if legal_artist:
        destination_metadata['~artists_{0}_all_legal'.format(source_type,)] = legal_artist
    if std_artist_list:
        destination_metadata['~artists_{0}_all_std_multi'.format(source_type,)] = std_artist_list
    if cred_artist_list:
        destination_metadata['~artists_{0}_all_cred_multi'.format(source_type,)] = cred_artist_list
    if sort_artist_list:
        destination_metadata['~artists_{0}_all_sort_multi'.format(source_type,)] = sort_artist_list
    if cred_sort_artist_list:
        destination_metadata['~artists_{0}_all_cred_sort_multi'.format(source_type,)] = cred_sort_artist_list
    if legal_artist_list:
        destination_metadata['~artists_{0}_all_legal_multi'.format(source_type,)] = legal_artist_list
    if sort_pri_artist:
        destination_metadata['~artists_{0}_all_sort_primary'.format(source_type,)] = sort_pri_artist
    if artist_types:
        destination_metadata['~artists_{0}_all_types'.format(source_type,)] = artist_types
    if artist_join_phrases:
        destination_metadata['~artists_{0}_all_join_phrases'.format(source_type,)] = artist_join_phrases
    if artist_count:
        destination_metadata['~artists_{0}_all_count'.format(source_type,)] = artist_count


def make_album_vars(album, album_metadata, release_metadata):
    album_id = release_metadata['id'] if release_metadata else 'No Album ID'
    process_artists(album_id, release_metadata, album_metadata, 'album')


def make_track_vars(album, album_metadata, track_metadata, release_metadata):
    album_id = release_metadata['id'] if release_metadata else 'No Album ID'
    process_artists(album_id, track_metadata, album_metadata, 'track')


def metadata_error(album_id, metadata_element, metadata_group):
    log.error("{0}: {1!r}: Missing '{2}' in {3} metadata.".format(
        PLUGIN_NAME, album_id, metadata_element, metadata_group,))


# Register the plugin to run at a LOW priority so that other plugins that
# modify the artist information can complete their processing and this plugin
# is working with the latest updated data.
register_album_metadata_processor(make_album_vars, priority=PluginPriority.LOW)
register_track_metadata_processor(make_track_vars, priority=PluginPriority.LOW)
