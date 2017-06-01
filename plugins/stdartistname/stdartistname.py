PLUGIN_NAME = 'Standardized Artist Names'
PLUGIN_AUTHOR = 'Bob Swift (rdswift)'
PLUGIN_DESCRIPTION = '''
Provides standardized artist information, similar to enabling the 'Use
standardized artist name' option, in new StdAlbumArtist and StdAlbumArtists
metadata tags.  The StdAlbumArtist tag contains the standardized name for
the first artist in the AlbumArtist list, and the StdAlbumArtists tag
contains the standardized names for all artists in the AlbumArtist list
separated by a semi-colon.<br /><br />This is useful when your tagging or
renaming scripts require both the standardized artist name and the credited
artist name.<br /><br />NOTE: When using this plugin, the 'Use standardized
artist name' option should be left unchecked.
'''

# This is essentially the 'Album Artist Website' plugin by Sophist, with a
# few minor tweaks to get the standardized artist name rather than the artist
# official home page.

PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["1.4.0"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard import config, log
from picard.util import LockableObject
from picard.metadata import register_track_metadata_processor
from functools import partial

class AlbumArtistStdName:

    class ArtistStdNameQueue(LockableObject):

        def __init__(self):
            LockableObject.__init__(self)
            self.queue = {}

        def __contains__(self, name):
            return name in self.queue

        def __iter__(self):
            return self.queue.__iter__()

        def __getitem__(self, name):
            self.lock_for_read()
            value = self.queue[name] if name in self.queue else None
            self.unlock()
            return value

        def __setitem__(self, name, value):
            self.lock_for_write()
            self.queue[name] = value
            self.unlock()

        def append(self, name, value):
            self.lock_for_write()
            if name in self.queue:
                self.queue[name].append(value)
                value = False
            else:
                self.queue[name] = [value]
                value = True
            self.unlock()
            return value

        def remove(self, name):
            self.lock_for_write()
            value = None
            if name in self.queue:
                value = self.queue[name]
                del self.queue[name]
            self.unlock()
            return value

    def __init__(self):
        self.artist_cache = {}
        self.std_name_cache = {}
        self.std_name_queue = self.ArtistStdNameQueue()

    def add_artist_std_name(self, album, track_metadata, trackXmlNode, releaseXmlNode):
        albumArtistIds = dict.get(track_metadata,'musicbrainz_albumartistid', [])
        for artistId in albumArtistIds:
            if artistId in self.std_name_cache:
                if self.std_name_cache[artistId]:
                    tsArtist, tsArtists = self.make_standards(albumArtistIds)
                    track_metadata["StdAlbumArtist"] = tsArtist
                    track_metadata["StdAlbumArtists"] = tsArtists
            else:
                # Jump through hoops to get track object!!
                self.std_name_add_track(album, album._new_tracks[-1], artistId)

    def std_name_add_track(self, album, track, artistId):
        self.album_add_request(album)
        if self.std_name_queue.append(artistId, (track, album)):
            host = config.setting["server_host"]
            port = config.setting["server_port"]
            path = "/ws/2/%s/%s" % ('artist', artistId)
            queryargs = {}  #queryargs = {"inc": "url-rels"}
            return album.tagger.xmlws.get(host, port, path,
                        partial(self.std_name_process, artistId),
                                xml=True, priority=True, important=True,
                                queryargs=queryargs)

    def std_name_process(self, artistId, response, reply, error):
        if error:
            log.error("%s: %r: Network error retrieving artist record", PLUGIN_NAME, artistId)
            tuples = self.std_name_queue.remove(artistId)
            for track, album in tuples:
                self.album_remove_request(album)
            return
        std_name = self.artist_process_metadata(artistId, response)
        self.artist_cache[artistId] = std_name
        self.std_name_cache[artistId] = std_name
        tuples = self.std_name_queue.remove(artistId)
        log.debug("%s: %r: Artist Standardized Name = %r", PLUGIN_NAME,
                  artistId, std_name)
        for track, album in tuples:
            tm = track.metadata
            albumArtistIds = dict.get(tm,'musicbrainz_albumartistid', [])
            if std_name:
                tsArtist, tsArtists = self.make_standards(albumArtistIds)
                tm["StdAlbumArtist"] = tsArtist
                tm["StdAlbumArtists"] = tsArtists
                for file in track.iterfiles(True):
                    fm = file.metadata
                    fm["StdAlbumArtist"] = tsArtist
                    fm["StdAlbumArtists"] = tsArtists
            self.album_remove_request(album)

    def album_add_request(self, album):
        album._requests += 1

    def album_remove_request(self, album):
        album._requests -= 1
        album._finalize_loading(None)

    def artist_process_metadata(self, artistId, response):
        if 'metadata' in response.children:
            if 'artist' in response.metadata[0].children:
                if 'name' in response.metadata[0].artist[0].children:
                    self.artist_cache[artistId] = response.metadata[0].artist[0].name[0].text
                    return response.metadata[0].artist[0].name[0].text
            else:
                log.error("%s: %r: MusicBrainz artist xml result not in correct format - %s",
                          PLUGIN_NAME, artistId, response)
        return None

    def make_standards(self, albumArtistIds):
        junk = []
        aCount = 0
        for sArtistId in albumArtistIds:
            junk.append(self.artist_cache[sArtistId] if sArtistId in self.artist_cache else sArtistId)
            if aCount < 1:
                tsArtist = self.artist_cache[sArtistId] if sArtistId in self.artist_cache else sArtistId
            aCount += 1
        tsArtists = ";".join(junk)
        return [tsArtist, tsArtists]


register_track_metadata_processor(AlbumArtistStdName().add_artist_std_name)
