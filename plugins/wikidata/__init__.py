# -*- coding: utf-8 -*-
# Copyright © 2016 Daniel sobey <dns@dns.id.au >

# This work is free. You can redistribute it and/or modify it under the
# terms of the Do What The Fuck You Want To Public License, Version 2,
# as published by Sam Hocevar. See http://www.wtfpl.net/ for more details.

PLUGIN_NAME = 'Wikidata Genre'
PLUGIN_AUTHOR = 'Daniel Sobey, Sambhav Kothari'
PLUGIN_DESCRIPTION = 'Query wikidata to get genre tags'
PLUGIN_VERSION = '1.4.4'
PLUGIN_API_VERSIONS = ["2.0", "2.1", "2.2"]
PLUGIN_LICENSE = 'WTFPL'
PLUGIN_LICENSE_URL = 'http://www.wtfpl.net/'

import re
from functools import partial
from picard import config, log
from picard.metadata import register_track_metadata_processor
from picard.plugins.wikidata.ui_options_wikidata import Ui_WikidataOptionsPage
from picard.ui.options import register_options_page, OptionsPage
from picard.webservice import ratecontrol


WIKIDATA_HOST = 'www.wikidata.org'
WIKIDATA_PORT = 443

ratecontrol.set_minimum_delay((WIKIDATA_HOST, WIKIDATA_PORT), 0)


def parse_ignored_tags(ignore_tags_setting):
    ignore_tags = []
    for tag in ignore_tags_setting.lower().split(','):
        if not tag:
            break
        tag = tag.strip()
        if tag.startswith('/') and tag.endswith('/'):
            try:
                tag = re.compile(tag[1:-1])
            except re.error:
                log.error(
                    'Error parsing ignored tag "%s"', tag, exc_info=True)
        ignore_tags.append(tag)
    return ignore_tags


def matches_ignored(ignore_tags, tag):
    if ignore_tags:
        tag = tag.lower().strip()
        for pattern in ignore_tags:
            if hasattr(pattern, 'match'):
                match = pattern.match(tag)
            else:
                match = pattern == tag
            if match:
                return True
    return False


class Wikidata:

    RELEASE_GROUP = 1
    ARTIST = 2
    WORK = 3

    def __init__(self):
        # Key: mbid, value: List of metadata entries to be updated when we have parsed everything
        self.requests = {}

        # Key: mbid, value: List of items to track the number of outstanding requests
        self.itemAlbums = {}

        # cache, items that have been found
        # key: mbid, value: list of strings containing the genre's
        self.cache = {}

        # metabrainz url
        self.mb_host = ''
        self.mb_port = ''

        # web service & logger
        self.ws = None
        self.log = None

        # settings from options, options
        self.use_release_group_genres = False
        self.use_artist_genres = False
        self.use_artist_only_if_no_release = False
        self.ignore_genres_from_these_artists = ''
        self.ignore_genres_from_these_artists_list = []
        self.use_work_genres = True
        self.ignore_these_genres = ''
        self.ignore_these_genres_list = []
        self.genre_delimiter = ''

    # not used
    def process_release(self, album, metadata, release):
        self.ws = album.tagger.webservice
        self.log = album.log
        item_id = metadata.getall('musicbrainz_releasegroupid')[0]

        log.info('WIKIDATA: Processing release group %s ' % item_id)
        self.process_request(metadata, album, item_id, item_type='release-group')
        for artist in metadata.getall('musicbrainz_albumartistid'):
            item_id = artist
            log.info('WIKIDATA: Processing release artist %s' % item_id)
            self.process_request(metadata, album, item_id, item_type='artist')

    # Main processing function
    # First see if we have already found what we need in the cache, finalize loading
    # Next see if we are already looking for the item
    #   If we are, add this item to the list of items to be updated once we find what we are looking for.
    #   Otherwise we are the first one to look up this item, start a new request
    # metadata, map containing the new metadata
    #
    def process_request(self, metadata, album, item_id, item_type):
        log.debug('WIKIDATA: Looking up cache for item: %s' % item_id)
        log.debug('WIKIDATA: Album request count: %s' % album._requests)
        log.debug('WIKIDATA: Item type %s' % item_type)
        if item_id in self.cache:
            log.debug('WIKIDATA: Found item in cache')
            genre_list = self.cache[item_id]
            new_genre = set(metadata.getall("genre"))
            new_genre.update(genre_list)
            #sort the new genre list so that they don't appear as new entries (not a change) next time
            metadata["genre"] = self.genre_delimiter.join(sorted(new_genre))
            return
        else:
            # pending requests are handled by adding the metadata object to a
            # list of things to be updated when the genre is found
            if item_id in self.itemAlbums:
                log.debug(
                    'WIKIDATA: Request already pending, add it to the list of items to update once this has been'
                    'found')
                self.requests[item_id].append(metadata)
            else:
                self.requests[item_id] = [metadata]
                self.itemAlbums[item_id] = album
                album._requests += 1

                log.debug('WIKIDATA: First request for this item')
                log.debug('WIKIDATA: About to call Musicbrainz to look up %s ' % item_id)

                path = '/ws/2/%s/%s' % (item_type, item_id)
                queryargs = {"inc": "url-rels"}

                self.ws.get(self.mb_host, self.mb_port, path, partial(self.musicbrainz_release_lookup, item_id,
                                                                      metadata),
                            parse_response_type="xml", priority=False, important=False, queryargs=queryargs)

    def musicbrainz_release_lookup(self, item_id, metadata, response, reply, error):
        found = False
        if error:
            log.error('WIKIDATA: Error retrieving release group info')
        else:
            if 'metadata' in response.children:
                if 'release_group' in response.metadata[0].children and self.use_release_group_genres:
                    if 'relation_list' in response.metadata[0].release_group[0].children:
                        for relation in response.metadata[0].release_group[0].relation_list[0].relation:
                            if relation.type == 'wikidata' and 'target' in relation.children:
                                found = True
                                wikidata_url = relation.target[0].text
                                log.debug('WIKIDATA: wikidata url found for RELEASE_GROUP: %s ', wikidata_url)
                                self.process_wikidata(Wikidata.RELEASE_GROUP, wikidata_url, item_id)
                if 'artist' in response.metadata[0].children and self.use_artist_genres:
                    if 'relation_list' in response.metadata[0].artist[0].children:
                        for relation in response.metadata[0].artist[0].relation_list[0].relation:
                            if relation.type == 'wikidata' and 'target' in relation.children:
                                found = True
                                wikidata_url = relation.target[0].text
                                self.process_wikidata(Wikidata.ARTIST, wikidata_url, item_id)
                                log.debug('WIKIDATA: wikidata url found for ARTIST: %s ', wikidata_url)
                if 'work' in response.metadata[0].children and self.use_work_genres:
                    if 'relation_list' in response.metadata[0].work[0].children:
                        for relation in response.metadata[0].work[0].relation_list[0].relation:
                            if relation.type == 'wikidata' and 'target' in relation.children:
                                found = True
                                wikidata_url = relation.target[0].text
                                log.debug('WIKIDATA: wikidata url found for WORK: %s ', wikidata_url)
                                self.process_wikidata(Wikidata.WORK, wikidata_url, item_id)
        if not found:
            log.debug('WIKIDATA: No wikidata url found for item_id: %s ', item_id)

        album = self.itemAlbums[item_id]
        album._requests -= 1
        if not album._requests:
            self.itemAlbums = {k: v for k, v in self.itemAlbums.items() if v != album}
            album._finalize_loading(None)
        log.info('WIKIDATA: Total remaining requests: %s' % album._requests)
        if not self.itemAlbums:
            self.requests.clear()
            log.info('WIKIDATA: Finished (A)')

    def process_wikidata(self, genre_source_type, wikidata_url, item_id):
        album = self.itemAlbums[item_id]
        album._requests += 1
        item = wikidata_url.split('/')[4]
        path = "/wiki/Special:EntityData/" + item + ".rdf"
        log.debug('WIKIDATA: Fetching from wikidata.org%s' % path)
        self.ws.get(WIKIDATA_HOST, WIKIDATA_PORT, path,
                    partial(self.parse_wikidata_response, item, item_id, genre_source_type),
                    parse_response_type="xml", priority=False, important=False)

    def parse_wikidata_response(self, item, item_id, genre_source_type, response, reply, error):
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
                                                log.debug(
                                                    'WIKIDATA: Found the wikidata id for the genre: %s' % genre_id)
                                                genre_entries.append(tmp)
                        else:
                            for tmp in genre_entries:
                                if tmp == node1.attribs.get('about'):
                                    list1 = node1.children.get('name')
                                    if not list1:
                                    	log.warning('WIKIDATA: Response does not contain a name field')
                                    else:
                                        for node2 in list1:
                                            if node2.attribs.get('lang') == 'en':
                                                genre = node2.text.title()
                                                if not matches_ignored(self.ignore_these_genres_list, genre):
                                                    genre_list.append(genre)
                                                    log.debug('New genre has been found and ALLOWED: %s' % genre)
                                                else:
                                                    log.debug('New genre has been found, but IGNORED: %s' % genre)

        if len(genre_list) > 0:
            log.debug('WIKIDATA: item_id: %s' % item_id)
            log.debug('WIKIDATA: Final list of wikidata id found: %s' % genre_entries)
            log.debug('WIKIDATA: Final list of genre: %s' % genre_list)
            log.info('WIKIDATA: Total items to update: %d ' % len(self.requests[item_id]))

            for metadata in self.requests[item_id]:
                if genre_source_type == Wikidata.RELEASE_GROUP:
                    metadata['~release_group_genre_sourced'] = True
                elif genre_source_type == Wikidata.ARTIST:
                    if self.use_artist_only_if_no_release and metadata['~release_group_genre_sourced'] or \
                            matches_ignored(self.ignore_genres_from_these_artists_list, metadata.get("artist")):
                        if item_id not in self.cache:
                            self.cache[item_id] = []
                        log.debug('WIKIDATA: NOT setting Artist-sourced genre: %s ' % genre_list)
                        continue
                    else:
                        log.debug('WIKIDATA: Setting Artist-sourced genre: %s ' % genre_list)

                # getall doesn't handle delimiters so we need to check-n-parse here
                old_genre_metadata = metadata.getall("genre")
                old_genre_list = []
                for genre in old_genre_metadata:
                    if self.genre_delimiter and self.genre_delimiter in genre:
                        old_genre_list.extend(genre.split(self.genre_delimiter))
                    else:
                        old_genre_list.append(genre)

                new_genre = set(old_genre_list)
                new_genre.update(genre_list)
                # Sort the new genre list so that they don't appear as new entries (not a change) next time
                log.debug('WIKIDATA: setting metadata genre to : %s ' % new_genre)
                if self.genre_delimiter:
                    metadata["genre"] = self.genre_delimiter.join(sorted(new_genre))
                else:
                    metadata["genre"] = sorted(new_genre)

                log.debug('WIKIDATA: setting cache genre to : %s ' % genre_list)
                self.cache[item_id] = genre_list
        else:
            log.debug('WIKIDATA: genre not found in wikidata')

        log.debug('WIKIDATA: seeing if we can finalize tags...')

        album = self.itemAlbums[item_id]
        album._requests -= 1
        if not album._requests:
            self.itemAlbums = {k: v for k, v in self.itemAlbums.items() if v != album}
            album._finalize_loading(None)
        log.info('WIKIDATA: total remaining requests: %s' % album._requests)
        if not self.itemAlbums:
            self.requests.clear()
            log.info('WIKIDATA: Finished (B)')

    def process_track(self, album, metadata, track, release):
        self.update_settings()
        self.ws = album.tagger.webservice
        self.log = album.log

        log.info('WIKIDATA: Processing Track...')
        if self.use_release_group_genres:
            for release_group in metadata.getall('musicbrainz_releasegroupid'):
                log.debug('WIKIDATA: Looking up release group metadata for %s ' % release_group)
                self.process_request(metadata, album, release_group, item_type='release-group')

        if self.use_artist_genres:
            for artist in metadata.getall('musicbrainz_albumartistid'):
                log.debug('WIKIDATA: Processing release artist %s' % artist)
                self.process_request(metadata, album, artist, item_type='artist')

        if self.use_artist_genres:
            for artist in metadata.getall('musicbrainz_artistid'):
                log.debug('WIKIDATA: Processing track artist %s' % artist)
                self.process_request(metadata, album, artist, item_type='artist')

        if self.use_work_genres:
            for workid in metadata.getall('musicbrainz_workid'):
                log.debug('WIKIDATA: Processing track artist %s' % workid)
                self.process_request(metadata, album, workid, item_type='work')

    def update_settings(self):
        self.mb_host = config.setting["server_host"]
        self.mb_port = config.setting["server_port"]
        self.use_release_group_genres = config.setting[""]
        self.use_work_genres = config.setting["wikidata_use_work_genres"]
        # Some changed settings could invalidate the cache, so clear it to be safe
        if self.use_release_group_genres != config.setting["wikidata_use_release_group_genres"]:
            self.use_release_group_genres = config.setting["wikidata_use_release_group_genres"]
            self.cache.clear()
        if self.use_artist_genres != config.setting["wikidata_use_artist_genres"]:
            self.use_artist_genres = config.setting["wikidata_use_artist_genres"]
            self.cache.clear()
        if self.use_artist_only_if_no_release != config.setting["wikidata_use_artist_only_if_no_release"]:
            self.use_artist_only_if_no_release = config.setting["wikidata_use_artist_only_if_no_release"]
            self.cache.clear()
        if self.ignore_genres_from_these_artists != parse_ignored_tags(
                config.setting["wikidata_ignore_genres_from_these_artists"]):
            self.ignore_genres_from_these_artists_list = parse_ignored_tags(
                config.setting["wikidata_ignore_genres_from_these_artists"])
            self.cache.clear()
        if self.use_work_genres != config.setting["wikidata_use_work_genres"]:
            self.use_work_genres = config.setting["wikidata_use_work_genres"]
            self.cache.clear()
        if self.ignore_these_genres != parse_ignored_tags(config.setting["wikidata_ignore_these_genres"]):
            self.ignore_these_genres = parse_ignored_tags(config.setting["wikidata_ignore_these_genres"])
            self.ignore_these_genres_list = parse_ignored_tags(
                config.setting["wikidata_ignore_these_genres"])
            self.cache.clear()
        if config.setting["write_id3v23"]:
            self.genre_delimiter = config.setting["wikidata_genre_delimiter"]


class WikidataOptionsPage(OptionsPage):
    NAME = "wikidata"
    TITLE = "Wikidata Genre"
    PARENT = "plugins"

    options = [
        config.BoolOption("setting", "wikidata_use_release_group_genres", True),
        config.BoolOption("setting", "wikidata_use_artist_genres", True),
        config.BoolOption("setting", "wikidata_use_artist_only_if_no_release", True),
        config.TextOption("setting", "wikidata_ignore_genres_from_these_artists", ""),
        config.BoolOption("setting", "wikidata_use_work_genres", True),
        config.TextOption("setting", "wikidata_ignore_these_genres", "seen live, favorites, /\\d+ of \\d+ stars/"),
        config.TextOption("setting", "wikidata_genre_delimiter", "; "),
    ]

    def __init__(self, parent=None):
        super(WikidataOptionsPage, self).__init__(parent)
        self.ui = Ui_WikidataOptionsPage()
        self.ui.setupUi(self)
        if not config.setting["write_id3v23"]:
            self.ui.genre_delimiter.setEnabled(False);
            self.ui.genre_delimiter_label.setEnabled(False);
        else:
            self.ui.genre_delimiter.setEnabled(True);
            self.ui.genre_delimiter_label.setEnabled(True);

    def load(self):
        setting = config.setting
        self.ui.use_release_group_genres.setChecked(setting["wikidata_use_release_group_genres"])
        self.ui.use_artist_genres.setChecked(setting["wikidata_use_artist_genres"])
        self.ui.use_artist_only_if_no_release.setChecked(setting["wikidata_use_artist_only_if_no_release"])
        self.ui.ignore_genres_from_these_artists.setText(setting["wikidata_ignore_genres_from_these_artists"])
        self.ui.use_work_genres.setChecked(setting["wikidata_use_work_genres"])
        self.ui.ignore_these_genres.setText(setting["wikidata_ignore_these_genres"])
        if config.setting["write_id3v23"]:
            self.ui.genre_delimiter.setEditText(setting["wikidata_genre_delimiter"])

    def save(self):
        setting = config.setting
        setting["wikidata_use_release_group_genres"] = self.ui.use_release_group_genres.isChecked()
        setting["wikidata_use_artist_genres"] = self.ui.use_artist_genres.isChecked()
        setting["wikidata_use_artist_only_if_no_release"] = self.ui.use_artist_only_if_no_release.isChecked()
        setting["wikidata_ignore_genres_from_these_artists"] = str(self.ui.ignore_genres_from_these_artists.text())
        setting["wikidata_use_work_genres"] = self.ui.use_work_genres.isChecked()
        setting["wikidata_ignore_these_genres"] = str(self.ui.ignore_these_genres.text())
        if config.setting["write_id3v23"]:
            setting["wikidata_genre_delimiter"] = str(self.ui.genre_delimiter.currentText())


wikidata = Wikidata()
register_track_metadata_processor(wikidata.process_track)
register_options_page(WikidataOptionsPage)
