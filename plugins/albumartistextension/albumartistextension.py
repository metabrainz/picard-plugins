PLUGIN_NAME = 'AlbumArtist Extension'
PLUGIN_AUTHOR = 'Bob Swift (rdswift)'
PLUGIN_DESCRIPTION = '''
This plugin provides standardized, credited and sorted artist information
for the album artist.  This is useful when your tagging or renaming scripts
require both the standardized artist name and the credited artist name, or
more detailed information about the album artists.
<br /><br />
The information is provided in the following variables:
<ul>
<li>_aaeStdAlbumArtists = The standardized version of the album artists.
<li>_aaeCredAlbumArtists = The credited version of the album artists.
<li>_aaeSortAlbumArtists = The sorted version of the album artists.
<li>_aaeStdPrimaryAlbumArtist = The standardized version of the first
    (primary) album artist.
<li>_aaeCredPrimaryAlbumArtist = The credited version of the first (primary)
    album artist.
<li>_aaeSortPrimaryAlbumArtist = The sorted version of the first (primary)
    album artist.
<li>_aaeAlbumArtistCount = The number of artists comprising the album artist.
</ul>
PLEASE NOTE: Once the plugin is installed, it automatically makes these 
variables available to File Naming Scripts and other scripts in Picard. 
Like other variables, you must mention them in a script for them to affect 
the file name or other data.
<br /><br />
This plugin is no longer being maintained. 
Consider switching to the 
[Additional Artists Variables plugin](https://github.com/rdswift/picard-plugins/tree/2.0/plugins/additional_artists_variables), 
which fills this 
role, and also includes additional variables. That other plugin uses different 
names for the album artist names provided here, so you if you switch plugins, you
will need to update your scripts with the different names.
<br /><br />
Version 0.6.1 of this plugin functions identically to Version 0.6. Only this 
description (and the version number) has changed.
'''

PLUGIN_VERSION = "0.6.1"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard import config, log
from picard.metadata import register_album_metadata_processor
from picard.plugin import PluginPriority

def add_artist_std_name(album, album_metadata, release_metadata):
    album_id = release_metadata['id']
    # Test for valid metadata node for the release
    if 'artist-credit' in release_metadata:
        # Initialize variables to default values
        cred_artist = ""
        std_artist = ""
        sort_artist = ""
        artist_count = 0
        # The 'artist-credit' key should always be there.
        # This check is to avoid a runtime error if it doesn't exist for some reason.
        for artist_credit in release_metadata['artist-credit']:
            # Initialize temporary variables for each loop.
            temp_std_name = ""
            temp_cred_name = ""
            temp_sort_name = ""
            temp_phrase = ""
            # Check if there is a 'joinphrase' specified.
            if 'joinphrase' in artist_credit:
                temp_phrase = artist_credit['joinphrase']
            else:
                metadata_error(album_id, 'artist-credit.joinphrase')
            # Check if there is a 'name' specified.
            if 'name' in artist_credit:
                temp_cred_name = artist_credit['name']
            else:
                metadata_error(album_id, 'artist-credit.name')
            # Check if there is an 'artist' specified.
            if 'artist' in artist_credit:
                # Check if there is a 'name' specified.
                if 'name' in artist_credit['artist']:
                    temp_std_name = artist_credit['artist']['name']
                else:
                    metadata_error(album_id, 'artist-credit.artist.name')
                if 'sort-name' in artist_credit['artist']:
                    temp_sort_name = artist_credit['artist']['sort-name']
                else:
                    metadata_error(album_id, 'artist-credit.artist.sort-name')
            else:
                metadata_error(album_id, 'artist-credit.artist')
            std_artist += temp_std_name + temp_phrase
            cred_artist += temp_cred_name + temp_phrase
            sort_artist += temp_sort_name + temp_phrase
            if artist_count < 1:
                album_metadata["~aaeStdPrimaryAlbumArtist"] = temp_std_name
                album_metadata["~aaeCredPrimaryAlbumArtist"] = temp_cred_name
                album_metadata["~aaeSortPrimaryAlbumArtist"] = temp_sort_name
            artist_count += 1
    else:
        metadata_error(album_id, 'artist-credit')
    if std_artist:
        album_metadata["~aaeStdAlbumArtists"] = std_artist
    if cred_artist:
        album_metadata["~aaeCredAlbumArtists"] = cred_artist
    if sort_artist:
        album_metadata["~aaeSortAlbumArtists"] = sort_artist
    if artist_count:
        album_metadata["~aaeAlbumArtistCount"] = artist_count
    return None


def metadata_error(album_id, metadata_element):
    log.error("%s: %r: Missing '%s' in release metadata.",
            PLUGIN_NAME, album_id, metadata_element)

# Register the plugin to run at a LOW priority so that other plugins that
# modify the artist information can complete their processing and this plugin
# is working with the latest updated data.
register_album_metadata_processor(add_artist_std_name, priority=PluginPriority.LOW)
