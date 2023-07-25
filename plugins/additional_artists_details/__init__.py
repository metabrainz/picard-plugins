# -*- coding: utf-8 -*-
"""Additional Artists Details
"""
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

# pylint: disable=line-too-long
# pylint: disable=import-error
# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals

from collections import namedtuple
from functools import partial

from picard import (
    config,
    log,
)
from picard.album import register_album_post_removal_processor
from picard.metadata import (
    register_album_metadata_processor,
    register_track_metadata_processor,
)
from picard.plugin import PluginPriority
from picard.plugins.additional_artists_details.ui_options_additional_artists_details import (
    Ui_AdditionalArtistsDetailsOptionsPage,
)
from picard.webservice.api_helpers import MBAPIHelper

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)


PLUGIN_NAME = 'Additional Artists Details'
PLUGIN_AUTHOR = 'Bob Swift (rdswift)'
PLUGIN_DESCRIPTION = '''
This plugin provides specialized album and track variables with artist details for use in tagging and naming scripts.  Note that this creates
additional calls to the MusicBrainz API for the artist and area information, and this will slow down processing.  This will be particularly
noticable when there are many different album or track artists, such as on a [Various Artists] release.  There is an option to disable track
artist processing, which can significantly increase the processing speed if you are only interested in album artist details.
<br /><br />
Please see the <a href="https://github.com/rdswift/picard-plugins/blob/2.0_RDS_Plugins/plugins/additional_artists_details/docs/README.md">user
guide</a> on GitHub for more information.
'''
PLUGIN_VERSION = '0.3'
PLUGIN_API_VERSIONS = ['2.0', '2.1', '2.2', '2.7', '2.8']
PLUGIN_LICENSE = 'GPL-2.0-or-later'
PLUGIN_LICENSE_URL = 'https://www.gnu.org/licenses/gpl-2.0.html'

PLUGIN_USER_GUIDE_URL = 'https://github.com/rdswift/picard-plugins/blob/2.0_RDS_Plugins/plugins/additional_artists_details/docs/README.md'

# Named tuples for code clarity
Area = namedtuple('Area', ['parent', 'name', 'country', 'type', 'type_text'])
MetadataPair = namedtuple('MetadataPair', ['artists', 'target'])

# MusicBrainz ID codes for relationship types
RELATIONSHIP_TYPE_PART_OF = 'de7cc874-8b1b-3a05-8272-f3834c968fb7'

# MusicBrainz ID codes for area types
AREA_TYPE_COUNTRY = '06dd0ae4-8c74-30bb-b43d-95dcedf961de'
AREA_TYPE_COUNTY = 'bcecec27-8bdb-3e00-8254-d948dda502fa'
AREA_TYPE_MUNICIPALITY = '17246454-5ac4-36a1-b81a-4753eb2dab20'

# Area types to exclude from the location string
EXCLUDE_AREA_TYPES = {AREA_TYPE_MUNICIPALITY, AREA_TYPE_COUNTY}

# Standard text for arguments
ALBUM_ARTISTS = 'album_artists'
ARTIST = 'artist'
ARTIST_REQUESTS = 'artist_requests'
AREA = 'area'
AREA_REQUESTS = 'area_requests'
ISO_CODES = 'iso-3166-1-codes'
OPT_AREA_DETAILS = 'aad_area_details'
OPT_PROCESS_TRACKS = 'aad_process_tracks'
TRACKS = 'tracks'


def log_helper(text, *args):
    """Logging helper to prepend the plugin name to the text.

    Args:
        text (str): Text to log.
        args (list): List of text replacement arguments.

    Returns:
        list: updated text and replacement arguments.
    """
    retval = ["%s: " + text, PLUGIN_NAME]
    retval.extend(args)
    return retval


class CustomHelper(MBAPIHelper):
    """Custom MusicBrainz API helper to retrieve artist and area information.
    """

    def get_artist_by_id(self, _id, handler, inc=None, priority=False, important=False,
                         mblogin=False, refresh=False):
        """Get information for the specified artist MBID.

        Args:
            _id (str): Artist MBID to retrieve.
            handler (object): Callback used to process the returned information.
            inc (list, optional): List of includes to add to the API call. Defaults to None.
            priority (bool, optional): Process the request at a high priority. Defaults to False.
            important (bool, optional): Identify the request as important. Defaults to False.
            mblogin (bool, optional): Request requires logging into MusicBrainz. Defaults to False.
            refresh (bool, optional): Request triggers a refresh. Defaults to False.

        Returns:
            RequestTask: Requested task object.
        """
        return self._get_by_id(ARTIST, _id, handler, inc, priority=priority, important=important, mblogin=mblogin, refresh=refresh)

    def get_area_by_id(self, _id, handler, inc=None, priority=False, important=False, mblogin=False, refresh=False):
        """Get information for the specified area MBID.

        Args:
            _id (str): Area MBID to retrieve.
            handler (object): Callback used to process the returned information.
            inc (list, optional): List of includes to add to the API call. Defaults to None.
            priority (bool, optional): Process the request at a high priority. Defaults to False.
            important (bool, optional): Identify the request as important. Defaults to False.
            mblogin (bool, optional): Request requires logging into MusicBrainz. Defaults to False.
            refresh (bool, optional): Request triggers a refresh. Defaults to False.

        Returns:
            RequestTask: Requested task object.
        """
        if inc is None:
            inc = ['area-rels']
        return self._get_by_id(AREA, _id, handler, inc, priority=priority, important=important, mblogin=mblogin, refresh=refresh)


class ArtistDetailsPlugin:
    """Plugin to retrieve artist details, including area and country information.
    """
    result_cache = {
        ARTIST: {},
        ARTIST_REQUESTS: set(),
        AREA: {},
        AREA_REQUESTS: set(),
    }
    album_processing_count = {}
    albums = {}

    def _make_empty_target(self, album_id):
        """Create an empty album target node if it doesn't exist.

        Args:
            album_id (str): MBID of the album.
        """
        if album_id not in self.albums:
            self.albums[album_id] = {ALBUM_ARTISTS: set(), TRACKS: []}

    def _add_target(self, album_id, artists, target_metadata):
        """Add a metadata target to update for an album.

        Args:
            album_id (str): MBID of the album.
            artists (set): Set of artists to include.
            target_metadata (Metadata): Target metadata to update.
        """
        self._make_empty_target(album_id)
        self.albums[album_id][TRACKS].append(MetadataPair(artists, target_metadata))

    def _remove_album(self, album_id):
        """Removes an album from the metadata processing dictionary.

        Args:
            album_id (str): MBID of the album to remove.
        """
        log.debug(*log_helper("Removing album '%s'", album_id))
        self.albums.pop(album_id, None)
        self.album_processing_count.pop(album_id, None)

    def _album_add_request(self, album):
        """Increment the number of pending requests for an album.

        Args:
            album (Album): The Album object to use for the processing.
        """
        if album.id not in self.album_processing_count:
            self.album_processing_count[album.id] = 0
        self.album_processing_count[album.id] += 1
        album._requests += 1

    def _album_remove_request(self, album):
        """Decrement the number of pending requests for an album.

        Args:
            album (Album): The Album object to use for the processing.
        """
        if album.id not in self.album_processing_count:
            self.album_processing_count[album.id] = 1
        self.album_processing_count[album.id] -= 1
        album._requests -= 1
        album._finalize_loading(None)   # pylint: disable=protected-access

    def remove_album(self, album):
        """Remove the album from the albums processing dictionary.

        Args:
            album (Album): The album object to remove.
        """
        self._remove_album(album.id)

    def make_album_vars(self, album, album_metadata, _release_metadata):
        """Process album artists.

        Args:
            album (Album): The Album object to use for the processing.
            album_metadata (Metadata): Metadata object for the album.
            _release_metadata (dict): Dictionary of release data from MusicBrainz api.
        """
        artists = set(artist.id for artist in album.get_album_artists())
        self._make_empty_target(album.id)
        self.albums[album.id][ALBUM_ARTISTS] = artists
        if not config.setting[OPT_PROCESS_TRACKS]:
            log.info(*log_helper("Track artist processing is disabled."))
        self._artist_processing(artists, album, album_metadata, 'Album')

    def make_track_vars(self, album, album_metadata, track_metadata, _release_metadata):
        """Process track artists.

        Args:
            album (Album): The Album object to use for the processing.
            album_metadata (Metadata): Metadata object for the album.
            track_metadata (dict): Dictionary of track data from MusicBrainz api.
            _release_metadata (dict): Dictionary of release data from MusicBrainz api.
        """
        artists = set()
        source_type = 'track'
        # Test for valid metadata node.
        # The 'artist-credit' key should always be there.
        # This check is to avoid a runtime error if it doesn't exist for some reason.
        if config.setting[OPT_PROCESS_TRACKS]:
            if 'artist-credit' in track_metadata:
                for artist_credit in track_metadata['artist-credit']:
                    if 'artist' in artist_credit:
                        if 'id' in artist_credit['artist']:
                            artists.add(artist_credit['artist']['id'])
                    else:
                        # No 'artist' specified.  Log as an error.
                        self._metadata_error(album.id, 'artist-credit.artist', source_type)
            else:
                # No valid metadata found.  Log as error.
                self._metadata_error(album.id, 'artist-credit', source_type)
        self._artist_processing(artists, album, album_metadata, 'Track')

    def _artist_processing(self, artists, album, destination_metadata, source_type):
        """Retrieves the information for each artist not already processed.

        Args:
            artists (set): Set of artist MBIDs to process.
            album (Album): Album object to use for the processing.
            destination_metadata (Metadata): Metadata object to update with the new variables.
            source_type (str): Source type (album or track) for logging messages.
        """
        for temp_id in artists:
            if temp_id not in self.result_cache[ARTIST_REQUESTS]:
                self.result_cache[ARTIST_REQUESTS].add(temp_id)
                log.debug(*log_helper('Retrieving artist ID %s information from MusicBrainz.', temp_id))
                self._get_artist_info(temp_id, album)
            else:
                log.debug(*log_helper('%s artist ID %s information available from cache.', source_type, temp_id))
        self._add_target(album.id, artists, destination_metadata)
        self._save_artist_metadata(album.id)

    def _save_artist_metadata(self, album_id):
        """Saves the new artist details variables to the metadata targets for the specified album.

        Args:
            album_id (str): MBID of the album to process.
        """
        if album_id in self.album_processing_count and self.album_processing_count[album_id]:
            return
        if album_id not in self.albums or not self.albums[album_id][TRACKS]:
            log.error(*log_helper("No metadata targets found for album '%s'", album_id))
            return
        for item in self.albums[album_id][TRACKS]:
            # Add album artists to track so they are available in the metadata
            artists = self.albums[album_id][ALBUM_ARTISTS].copy().union(item.artists)
            destination_metadata = item.target
            for artist in artists:
                if artist in self.result_cache[ARTIST]:
                    self._set_artist_metadata(destination_metadata, artist, self.result_cache[ARTIST][artist])

    def _set_artist_metadata(self, destination_metadata, artist_id, artist_info):
        """Adds the artist information to the destination metadata.

        Args:
            destination_metadata (Metadata): Metadata object to update with new variables.
            artist_id (str): MBID of the artist to update.
            artist_info (dict): Dictionary of information for the artist.
        """
        def _set_item(key, value):
            destination_metadata[f"~artist_{artist_id}_{key.replace('-', '_')}"] = value

        for item in artist_info.keys():
            if item in {'area', 'begin-area', 'end-area'}:
                country, location = self._drill_area(artist_info[item])
                if country:
                    _set_item(item.replace('area', 'country'), country)
                if location:
                    _set_item(item.replace('area', 'location'), location)
            else:
                _set_item(item, artist_info[item])

    def _get_artist_info(self, artist_id, album):
        """Gets the artist information from the MusicBrainz website.

        Args:
            artist_id (str): MBID of the artist to retrieve.
            album (Album): The Album object to use for the processing.
        """
        self._album_add_request(album)
        helper = CustomHelper(album.tagger.webservice)
        handler = partial(
            self._artist_submission_handler,
            artist=artist_id,
            album=album,
            )
        return helper.get_artist_by_id(artist_id, handler)

    def _artist_submission_handler(self, document, _reply, error, artist=None, album=None):
        """Handles the response from the webservice requests for artist information.
        """
        try:
            if error:
                log.error(*log_helper("Artist '%s' information retrieval error.", artist))
                return
            artist_info = {}
            for item in ['type', 'gender', 'name', 'sort-name', 'disambiguation']:
                if item in document and document[item]:
                    artist_info[item] = document[item]
            if 'life-span' in document:
                for item in ['begin', 'end']:
                    if item in document['life-span'] and document['life-span'][item]:
                        artist_info[item] = document['life-span'][item]
            for item in ['area', 'begin-area', 'end-area']:
                if item in document and document[item] and 'id' in document[item] and document[item]['id']:
                    area_id = document[item]['id']
                    artist_info[item] = area_id
                    if area_id not in self.result_cache[AREA_REQUESTS]:
                        self._get_area_info(area_id, album)
            self.result_cache[ARTIST][artist] = artist_info
        finally:
            self._album_remove_request(album)
            self._save_artist_metadata(album.id)

    def _get_area_info(self, area_id, album):
        """Gets the area information from the MusicBrainz website.

        Args:
            area_id (str): MBID of the area to retrieve.
            album (Album): The Album object to use for the processing.
        """
        self.result_cache[AREA_REQUESTS].add(area_id)
        self._album_add_request(album)
        log.debug(*log_helper('Retrieving area ID %s from MusicBrainz.', area_id))
        helper = CustomHelper(album.tagger.webservice)
        handler = partial(
            self._area_submission_handler,
            area=area_id,
            album=album,
            )
        return helper.get_area_by_id(area_id, handler)

    def _area_submission_handler(self, document, _reply, error, area=None, album=None):
        """Handles the response from the webservice requests for area information.
        """
        try:
            if error:
                log.error(*log_helper("Area '%s' information retrieval error.", area))
                return
            (_id, name, country, _type, type_text) = self._parse_area(document)
            if _type == AREA_TYPE_COUNTRY and _id not in self.result_cache[AREA]:
                self._area_logger(_id, f"{name} ({country})", type_text)
                self.result_cache[AREA][_id] = Area('', name, country, _type, type_text)
            if 'relations' in document:
                for rel in document['relations']:
                    self._parse_area_relation(_id, rel, album, name, _type, type_text)
        finally:
            self._album_remove_request(album)
            self._save_artist_metadata(album.id)

    @staticmethod
    def _area_logger(area_id, area_name, area_type):
        """Adds a log entry for the area retrieved.

        Args:
            area_id (str): MBID of the area added.
            area_name (str): Name of the area added.
            area_type (str): Type of area added.
        """
        log.debug(*log_helper("Adding area: %s => %s of type '%s'", area_id, area_name, area_type))

    def _parse_area_relation(self, area_id, area_relation, album, area_name, area_type, area_type_text):
        """Parse an area relation to extract the area information.

        Args:
            area_id (str): MBID of the area providing the relationship.
            area_relation (dict): Dictionary of the area relationship.
            album (Album): The Album object to use for the processing.
            area_name (str): Name of the area providing the relationship.
            area_type (str): MBID of the type of area providing the relationship.
            area_type_text (str): Text description of the area providing the relationship.
        """
        if 'type-id' not in area_relation or 'area' not in area_relation or area_relation['type-id'] != RELATIONSHIP_TYPE_PART_OF:
            return
        (_id, name, country, _type, type_text) = self._parse_area(area_relation['area'])
        if not _id:
            return

        if 'direction' in area_relation and area_relation['direction'] == 'backward':
            if area_id not in self.result_cache[AREA]:
                self._area_logger(area_id, area_name, area_type_text)
                self.result_cache[AREA][area_id] = Area(_id, area_name, '', area_type, type_text)
                self.result_cache[AREA_REQUESTS].add(area_id)
            if _type == AREA_TYPE_COUNTRY:
                if _id not in self.result_cache[AREA]:
                    self._area_logger(_id, f"{name} ({country})", type_text)
                    self.result_cache[AREA][_id] = Area('', name, country, _type, type_text)
                    self.result_cache[AREA_REQUESTS].add(_id)
            else:
                if _id not in self.result_cache[AREA] and _id not in self.result_cache[AREA_REQUESTS]:
                    self._get_area_info(_id, album)
        else:
            self._area_logger(_id, name, type_text)
            self.result_cache[AREA_REQUESTS].add(_id)
            self.result_cache[AREA][_id] = Area(area_id, name, '', _type, type_text)

    @staticmethod
    def _parse_area(area_info):
        """Parse a dictionary of area information to return selected elements.

        Args:
            area_info (dict): Area information to parse.

        Returns:
            tuple: Selected information for the area (id, name, country code, type code, type text).
        """
        if 'id' not in area_info:
            return ('', '', '', '', '')
        area_id = area_info['id']
        area_name = area_info['name'] if 'name' in area_info else 'Unknown Name'
        area_type = area_info['type-id'] if 'type-id' in area_info else ''
        area_type_text = area_info['type'] if 'type' in area_info else 'Unknown Area Type'
        if area_type == AREA_TYPE_COUNTRY:
            country = area_info[ISO_CODES][0] if ISO_CODES in area_info and area_info[ISO_CODES] else ''
        else:
            country = ''
        return (area_id, area_name, country, area_type, area_type_text)

    @staticmethod
    def _metadata_error(album_id, metadata_element, metadata_group):
        """Logs metadata-related errors.

        Args:
            album_id (str): MBID of the album being processed.
            metadata_element (str): Metadata element initiating the error.
            metadata_group (str): Metadata group initiating the error.
        """
        log.error(*log_helper("Album '%s' missing '%s' in %s metadata.", album_id, metadata_element, metadata_group))

    def _drill_area(self, area_id):
        """Drills up from the specified area to determine the two-character
        country code and the full location description for the area.

        Args:
            area_id (str): MBID of the area to process.

        Returns:
            tuple: The two-character country code and full location description for the area.
        """
        country = ''
        location = []
        i = 7   # Counter to avoid potential runaway processing
        while i and area_id and not country:
            i -= 1
            area = self.result_cache[AREA][area_id] if area_id in self.result_cache[AREA] else Area('', '', '', '', '')
            country = area.country
            area_id = area.parent
            if not location or config.setting[OPT_AREA_DETAILS] or area.type not in EXCLUDE_AREA_TYPES:
                location.append(area.name)
        return country, ', '.join(location)


class AdditionalArtistsDetailsOptionsPage(OptionsPage):
    """Options page for the Additional Artists Details plugin.
    """

    NAME = "additional_artists_details"
    TITLE = "Additional Artists Details"
    PARENT = "plugins"

    options = [
        config.BoolOption('setting', OPT_PROCESS_TRACKS, False),
        config.BoolOption('setting', OPT_AREA_DETAILS, False),
    ]

    def __init__(self, parent=None):
        super(AdditionalArtistsDetailsOptionsPage, self).__init__(parent)
        self.ui = Ui_AdditionalArtistsDetailsOptionsPage()
        self.ui.setupUi(self)

        # Enable external link
        self.ui.format_description.setOpenExternalLinks(True)

    def load(self):
        """Load the option settings.
        """
        self.ui.cb_process_tracks.setChecked(config.setting[OPT_PROCESS_TRACKS])
        self.ui.cb_area_details.setChecked(config.setting[OPT_AREA_DETAILS])

    def save(self):
        """Save the option settings.
        """
        # self._set_settings(config.setting)
        config.setting[OPT_PROCESS_TRACKS] = self.ui.cb_process_tracks.isChecked()
        config.setting[OPT_AREA_DETAILS] = self.ui.cb_area_details.isChecked()


plugin = ArtistDetailsPlugin()

# Register the plugin to run at a LOW priority so that other plugins that
# modify the artist information can complete their processing and this plugin
# is working with the latest updated data.
register_album_metadata_processor(plugin.make_album_vars, priority=PluginPriority.LOW)
register_track_metadata_processor(plugin.make_track_vars, priority=PluginPriority.LOW)

register_album_post_removal_processor(plugin.remove_album)
register_options_page(AdditionalArtistsDetailsOptionsPage)
