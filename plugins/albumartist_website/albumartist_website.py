# -*- coding: utf-8 -*-

PLUGIN_NAME = 'Album Artist Website'
PLUGIN_AUTHOR = 'Sophist, Sambhav Kothari'
PLUGIN_DESCRIPTION = '''Add's the album artist(s) Official Homepage(s)
(if they are defined in the MusicBrainz database).'''
PLUGIN_VERSION = '1.0.4'
PLUGIN_API_VERSIONS = ["2.0", "2.1", "2.2"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard import config, log
from picard.util import LockableObject
from picard.metadata import register_track_metadata_processor
from functools import partial

class AlbumArtistWebsite:

    class ArtistWebsiteQueue(LockableObject):

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
        self.website_cache = {}
        self.website_queue = self.ArtistWebsiteQueue()

    def add_artist_website(self, album, track_metadata, track_node, release_node):
        albumArtistIds = track_metadata.getall('musicbrainz_albumartistid')
        for artistId in albumArtistIds:
            if artistId in self.website_cache:
                if self.website_cache[artistId]:
                    track_metadata['website'] = self.website_cache[artistId]
            else:
                # Jump through hoops to get track object!!
                self.website_add_track(album, album._new_tracks[-1], artistId)

    def website_add_track(self, album, track, artistId):
        self.album_add_request(album)
        if self.website_queue.append(artistId, (track, album)):
            host = config.setting["server_host"]
            port = config.setting["server_port"]
            path = "/ws/2/%s/%s" % ('artist', artistId)
            queryargs = {"inc": "url-rels"}
            return album.tagger.webservice.get(host, port, path,
                        partial(self.website_process, artistId),
                                parse_response_type="xml", priority=True, important=False,
                                queryargs=queryargs)

    def website_process(self, artistId, response, reply, error):
        if error:
            log.error("%s: %r: Network error retrieving artist record", PLUGIN_NAME, artistId)
            tuples = self.website_queue.remove(artistId)
            for track, album in tuples:
                self.album_remove_request(album)
            return
        urls = self.artist_process_metadata(artistId, response)
        self.website_cache[artistId] = urls
        tuples = self.website_queue.remove(artistId)
        for track, album in tuples:
            if urls:
                tm = track.metadata
                tm['website'] = urls
                for file in track.iterfiles(True):
                    fm = file.metadata
                    fm['website'] = urls
            self.album_remove_request(album)

    def album_add_request(self, album):
        album._requests += 1

    def album_remove_request(self, album):
        album._requests -= 1
        album._finalize_loading(None)

    def artist_process_metadata(self, artistId, response):
        log.debug("%s: %r: Processing Artist record for official website urls: %r", PLUGIN_NAME, artistId, response)
        relations = self.artist_get_relations(response)
        if not relations:
            log.info("%s: %r: Artist does have any associated urls.", PLUGIN_NAME, artistId)
            return []

        urls = []
        for relation in relations:
            log.debug("%s: %r: Examining: %r", PLUGIN_NAME, artistId, relation)
            if 'type' in relation.attribs and relation.type == 'official homepage':
                if 'target' in relation.children and len(relation.target) > 0:
                    log.debug("%s: Adding artist url: %s", PLUGIN_NAME, relation.target[0].text)
                    urls.append(relation.target[0].text)
                else:
                    log.debug("%s: No url in relation: %r", PLUGIN_NAME, relation)

        if urls:
            log.info("%s: %r: Artist Official Homepages: %r", PLUGIN_NAME, artistId, urls)
        else:
            log.info("%s: %r: Artist does not have any official website urls.", PLUGIN_NAME, artistId)
        return sorted(urls)

    def artist_get_relations(self, response):
        log.debug("%s: artist_get_relations called", PLUGIN_NAME)
        if 'metadata' in response.children and len(response.metadata) > 0:
            if 'artist' in response.metadata[0].children and len(response.metadata[0].artist) > 0:
                if 'relation_list' in response.metadata[0].artist[0].children and len(response.metadata[0].artist[0].relation_list) > 0:
                    if 'relation' in response.metadata[0].artist[0].relation_list[0].children:
                        log.debug("%s: artist_get_relations returning: %r", PLUGIN_NAME, response.metadata[0].artist[0].relation_list[0].relation)
                        return response.metadata[0].artist[0].relation_list[0].relation
                    else:
                        log.debug("%s: artist_get_relations - no relation in relation_list", PLUGIN_NAME)
                else:
                    log.debug("%s: artist_get_relations - no relation_list in artist", PLUGIN_NAME)
            else:
                log.debug("%s: artist_get_relations - no artist in metadata", PLUGIN_NAME)
        else:
            log.debug("%s: artist_get_relations - no metadata in response", PLUGIN_NAME)
        return None


register_track_metadata_processor(AlbumArtistWebsite().add_artist_website)
