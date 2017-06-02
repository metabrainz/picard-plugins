PLUGIN_NAME = 'Standardized AlbumArtist'
PLUGIN_AUTHOR = 'Bob Swift (rdswift)'
PLUGIN_DESCRIPTION = '''
Provides standardized artist information, similar to enabling the 'Use
standardized artist name' option, in new StdAlbumArtist and
StdFirstAlbumArtist metadata tags.  The StdFirstAlbumArtist tag contains the
standardized name for the first artist in the AlbumArtist list, and the
StdAlbumArtist tag contains the standardized names for all artists in the
AlbumArtist list separated by the join phrase used in the AlbumArtist
tag.<br /><br />This is useful when your tagging or renaming scripts require
both the standardized artist name and the credited artist
name.<br /><br />NOTE: When using this plugin, the 'Use standardized
artist name' option should be left unchecked.
'''
##############################################################################
#
# Revision History
#
# 2017-05-31    v0.1    rdswift
#     - Initial version based primarily on the 'Album Artist Website' plugin
#       by Sophist, with a few minor tweaks to get the standardized artist
#       name rather than the artist official home page.
#
# 2017-06-01    v0.2    rdswift
#     + Complete rewrite to utilize the album metadata processor rather than
#       the track metadata processor
#     + Eliminate all extra calls to the ws service by using the information
#       already available in the album xml parameter.
#
##############################################################################

PLUGIN_VERSION = "0.2"
PLUGIN_API_VERSIONS = ["1.4.0"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard import log
from picard.metadata import register_album_metadata_processor

class AlbumArtistStdName:

    @staticmethod
    def add_artist_std_name(album, album_metadata, releaseXmlNode):
        albumid = releaseXmlNode.id
        if 'artist_credit' in releaseXmlNode.children:
            stdFirstArtist = ""
            stdArtist = ""
            if 'name_credit' in releaseXmlNode.artist_credit[0].children:
                aCount = 0
                for ncredit in releaseXmlNode.artist_credit[0].name_credit:
                    if 'joinphrase' in ncredit.attribs:
                        jphrase = ncredit.joinphrase
                    else:
                        jphrase = ""
                    if 'artist' in ncredit.children:
                        if 'name' in ncredit.artist[0].children:
                            stdArtist += ncredit.artist[0].name[0].text + jphrase
                            if aCount < 1:
                                stdFirstArtist += ncredit.artist[0].name[0].text
                            aCount += 1
            album_metadata["stdFirstAlbumArtist"] = stdFirstArtist if len(stdFirstArtist) > 0 else "Plugin Error"
            album_metadata["stdAlbumArtist"] = stdArtist if len(stdArtist) > 0 else "Plugin Error"
        else:
            log.error("%s: %r: Error reading XML contents: %s",
                      PLUGIN_NAME, albumid, releaseXmlNode)
        return None

register_album_metadata_processor(AlbumArtistStdName().add_artist_std_name)
