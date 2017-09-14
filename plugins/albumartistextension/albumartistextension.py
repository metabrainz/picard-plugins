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
PLEASE NOTE: Tagger scripts are required to make use of these hidden
variables.
'''

PLUGIN_VERSION = "0.6"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0 or later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard import config, log
from picard.metadata import register_album_metadata_processor
from picard.plugin import PluginPriority

def add_artist_std_name(album, album_metadata, release_metadata):
    albumid = release_metadata['id']
    # Test for valid metadata node for the release
    if 'artist-credit' in release_metadata:
        # Initialize variables to default values
        credArtist = ""
        stdArtist = ""
        sortArtist = ""
        aCount = 0
        # The 'artist-credit' key should always be there.
        # This check is to avoid a runtime error if it doesn't exist for some reason.
        for ncredit in release_metadata['artist-credit']:
            # Initialize temporary variables for each loop.
            tempStdName = ""
            tempCredName = ""
            tempSortName = ""
            tempPhrase = ""
            # Check if there is a 'joinphrase' specified.
            if 'joinphrase' in ncredit:
                tempPhrase = ncredit['joinphrase']
            else:
                log.error("%s: %r: Missing 'artist-credit.joinphrase' in release metadata.",
                        PLUGIN_NAME, albumid)
            # Check if there is a 'name' specified.
            if 'name' in ncredit:
                tempCredName = ncredit['name']
            else:
                log.error("%s: %r: Missing 'artist-credit.name' in release metadata.",
                        PLUGIN_NAME, albumid)
            # Check if there is an 'artist' specified.
            if 'artist' in ncredit:
                # Check if there is a 'name' specified.
                if 'name' in ncredit['artist']:
                    tempStdName = ncredit['artist']['name']
                else:
                    log.error("%s: %r: Missing 'artist-credit.artist.name' in release metadata.",
                            PLUGIN_NAME, albumid)
                if 'sort-name' in ncredit['artist']:
                    tempSortName = ncredit['artist']['sort-name']
                else:
                    log.error("%s: %r: Missing 'artist-credit.artist.sort-name' in release metadata.",
                            PLUGIN_NAME, albumid)
            else:
                log.error("%s: %r: Missing 'artist-credit.artist' in release metadata.",
                        PLUGIN_NAME, albumid)
            stdArtist += tempStdName + tempPhrase
            credArtist += tempCredName + tempPhrase
            sortArtist += tempSortName + tempPhrase
            if aCount < 1:
                album_metadata["~aaeStdPrimaryAlbumArtist"] = tempStdName
                album_metadata["~aaeCredPrimaryAlbumArtist"] = tempCredName
                album_metadata["~aaeSortPrimaryAlbumArtist"] = tempSortName
            aCount += 1
    else:
        log.error("%s: %r: Missing 'artist-credit' in release metadata: %s",
                PLUGIN_NAME, albumid, release_metadata)
    if len(stdArtist) > 0:
        album_metadata["~aaeStdAlbumArtists"] = stdArtist
    if len(credArtist) > 0:
        album_metadata["~aaeCredAlbumArtists"] = credArtist
    if len(sortArtist) > 0:
        album_metadata["~aaeSortAlbumArtists"] = sortArtist
    if aCount > 0:
        album_metadata["~aaeAlbumArtistCount"] = aCount
    return None

# Register the plugin to run at a LOW priority so that other plugins that
# modify the contents of the _albumartists and _albumartists_sort lists can
# complete their processing and this plugin is working with the latest
# updated data.
register_album_metadata_processor(add_artist_std_name, priority=PluginPriority.LOW)
