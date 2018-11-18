# -*- coding: utf-8 -*-
# Copyright © 2016 Daniel sobey <dns@dns.id.au >

# This work is free. You can redistribute it and/or modify it under the
# terms of the Do What The Fuck You Want To Public License, Version 2,
# as published by Sam Hocevar. See http://www.wtfpl.net/ for more details.

PLUGIN_NAME = 'wikidata-genre'
PLUGIN_AUTHOR = 'Daniel Sobey, Sambhav Kothari'
PLUGIN_DESCRIPTION = 'query wikidata to get genre tags'
PLUGIN_VERSION = '1.1'
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = 'WTFPL'
PLUGIN_LICENSE_URL = 'http://www.wtfpl.net/'

from functools import partial
import threading

from picard import config, log
from picard.metadata import register_track_metadata_processor


class Wikidata:

    def __init__(self):
        self.lock = threading.Lock()
        # Key: mbid, value: List of metadata entries to be updated when we have parsed everything
        self.requests = {}

        # Key: mbid, value: List of items to track the number of outstanding requests
        self.albums = {}

        # cache, items that have been found
        # key: mbid, value: list of strings containing the genre's
        self.cache = {}

        # metabrainz url
        self.mb_host = ''
        self.mb_port = ''

        # web service & logger
        self.ws = None
        self.log = None

    # not used
    def process_release(self, album, metadata, release):
        self.ws = album.tagger.webservice
        self.log = album.log
        item_id = dict.get(metadata, 'musicbrainz_releasegroupid')[0]

        log.info('WIKIDATA: processing release group %s ' % item_id)
        self.process_request(metadata, album, item_id, type='release-group')
        for artist in dict.get(metadata, 'musicbrainz_albumartistid'):
            item_id = artist
            log.info('WIKIDATA: processing release artist %s' % item_id)
            self.process_request(metadata, album, item_id, type='artist')

    # Main processing function
    # First see if we have already found what we need in the cache, finalize loading
    # Next see if we are already looking for the item
    #   If we are add this item to the list of items to be updated once we find what we are looking for.
    #   Otherwise we are the first one to look up this item, start a new request
    # metadata, map containing the new metadata
    #
    def process_request(self, metadata, album, item_id, type):
        with self.lock:
            log.debug('WIKIDATA: Looking up cache for item  %s' % item_id)
            log.debug('WIKIDATA: requests %s' % album._requests)
            log.debug('WIKIDATA: TYPE %s' % type)
            if item_id in self.cache:
                log.info('WIKIDATA: found in cache')
                genre_list = self.cache[item_id]
                new_genre = set(metadata.getall("genre"))
                new_genre.update(genre_list)
                #sort the new genre list so that they don't appear as new entries (not a change) next time
                metadata["genre"] = sorted(new_genre)
                return
            else:
                # pending requests are handled by adding the metadata object to a
                # list of things to be updated when the genre is found
                if item_id in self.albums:
                    log.debug(
                        'WIKIDATA: request already pending, add it to the list of items to update once this has been found')
                    self.requests[item_id].append(metadata)

                else:
                    self.requests[item_id] = [metadata]
                    album._requests += 1
                    self.albums[item_id] = [album]

                    log.debug('WIKIDATA: first request for this item')
                    log.info('WIKIDATA: about to call musicbrainz to look up %s ' % item_id)

                    path = '/ws/2/%s/%s' % (type, item_id)
                    queryargs = {"inc": "url-rels"}

                    self.ws.get(self.mb_host, self.mb_port, path, partial(self.musicbrainz_release_lookup, item_id,
                                                                          metadata),
                                parse_response_type="xml", priority=False, important=False, queryargs=queryargs)

    def musicbrainz_release_lookup(self, item_id, metadata, response, reply, error):
        found = False
        if error:
            log.info('WIKIDATA: error retrieving release group info')
        else:
            if 'metadata' in response.children:
                if 'release_group' in response.metadata[0].children:
                    if 'relation_list' in response.metadata[0].release_group[0].children:
                        for relation in response.metadata[0].release_group[0].relation_list[0].relation:
                            if relation.type == 'wikidata' and 'target' in relation.children:
                                found = True
                                wikidata_url = relation.target[0].text
                                self.process_wikidata(wikidata_url, item_id)
                if 'artist' in response.metadata[0].children:
                    if 'relation_list' in response.metadata[0].artist[0].children:
                        for relation in response.metadata[0].artist[0].relation_list[0].relation:
                            if relation.type == 'wikidata' and 'target' in relation.children:
                                found = True
                                wikidata_url = relation.target[0].text
                                self.process_wikidata(wikidata_url, item_id)
                if 'work' in response.metadata[0].children:
                    if 'relation_list' in response.metadata[0].work[0].children:
                        for relation in response.metadata[0].work[0].relation_list[0].relation:
                            if relation.type == 'wikidata' and 'target' in relation.children:
                                found = True
                                wikidata_url = relation.target[0].text
                                self.process_wikidata(wikidata_url, item_id)
        if not found:
            log.info('WIKIDATA: no wikidata url found for item_id: %s ', item_id)
        with self.lock:
            for album in self.albums[item_id]:
                album._requests -= 1
                log.debug('WIKIDATA:  TOTAL REMAINING REQUESTS %s' % album._requests)
                if not album._requests:
                    self.albums[item_id].remove(album)
                    album._finalize_loading(None)

    def process_wikidata(self, wikidata_url, item_id):
        with self.lock:
            for album in self.albums[item_id]:
                album._requests += 1
        item = wikidata_url.split('/')[4]
        path = "/wiki/Special:EntityData/" + item + ".rdf"
        log.info('WIKIDATA: fetching the folowing url wikidata.org%s' % path)
        self.ws.get('www.wikidata.org', 443, path,
                    partial(self.parse_wikidata_response, item, item_id),
                    parse_response_type="xml", priority=False, important=False)

    def parse_wikidata_response(self, item, item_id, response, reply, error):
        genre_entries = []
        genre_list = []
        if error:
            log.error('WIKIDATA: error getting data from wikidata.org')
        else:
            if 'RDF' in response.children:
                node = response.RDF[0]
                for node1 in node.Description:
                    if 'about' in node1.attribs:
                        if node1.attribs.get('about') == 'http://www.wikidata.org/entity/%s' % item:
                            for key, val in list(node1.children.items()):
                                if key == 'P136':
                                    for i in val:
                                        if 'resource' in i.attribs:
                                            tmp = i.attribs.get('resource')
                                            if 'entity' == tmp.split('/')[3] and len(tmp.split('/')) == 5:
                                                genre_id = tmp.split('/')[4]
                                                log.info(
                                                    'WIKIDATA: Found the wikidata id for the genre: %s' % genre_id)
                                                genre_entries.append(tmp)
                        else:
                            for tmp in genre_entries:
                                if tmp == node1.attribs.get('about'):
                                    list1 = node1.children.get('name')
                                    for node2 in list1:
                                        if node2.attribs.get('lang') == 'en':
                                            genre = node2.text.title()
                                            genre_list.append(genre)
                                            log.debug(
                                                'Our genre is: %s' % genre)

        with self.lock:
            if len(genre_list) > 0:
                log.info('WIKIDATA: final list of wikidata id found: %s' % genre_entries)
                log.info('WIKIDATA: final list of genre: %s' % genre_list)

                log.debug('WIKIDATA: total items to update: %s ' %
                          len(self.requests[item_id]))
                for metadata in self.requests[item_id]:
                    new_genre = set(metadata.getall("genre"))
                    new_genre.update(genre_list)
                    # sort the new genre list so that they don't appear as new entries (not a change) next time
                    metadata["genre"] = sorted(new_genre)
                    self.cache[item_id] = genre_list
                    log.debug('WIKIDATA: setting genre : %s ' % genre_list)

            else:
                log.info('WIKIDATA: Genre not found in wikidata')

            log.info('WIKIDATA: Seeing if we can finalize tags %d  ' % len(self.albums[item_id]))

            for album in self.albums[item_id]:
                album._requests -= 1
                if not album._requests:
                    self.albums[item_id].remove(album)
                    album._finalize_loading(None)
                log.info('WIKIDATA:  TOTAL REMAINING REQUESTS %s' % album._requests)

    def process_track(self, album, metadata, trackXmlNode, releaseXmlNode):
        self.mb_host = config.setting["server_host"]
        self.mb_port = config.setting["server_port"]
        self.ws = album.tagger.webservice
        self.log = album.log

        for release_group in metadata.getall('musicbrainz_releasegroupid'):
            log.debug('WIKIDATA: looking up release group metadata for %s ' % release_group)
            self.process_request(metadata, album, release_group, type='release-group')

        for artist in metadata.getall('musicbrainz_albumartistid'):
            log.info('WIKIDATA: processing release artist %s' % artist)
            self.process_request(metadata, album, artist, type='artist')

        for artist in metadata.getall('musicbrainz_artistid'):
            log.info('WIKIDATA: processing track artist %s' % artist)
            self.process_request(metadata, album, artist, type='artist')

        if 'musicbrainz_workid' in metadata:
            for workid in metadata.getall('musicbrainz_workid'):
                log.info('WIKIDATA: processing track artist %s' % workid)
                self.process_request(metadata, album, workid, type='work')


wikidata = Wikidata()
# register_album_metadata_processor(wikidata.process_release)
register_track_metadata_processor(wikidata.process_track)
