# -*- coding: utf-8 -*-
# Copyright © 2016 Daniel sobey <dns@dns.id.au >

# This work is free. You can redistribute it and/or modify it under the
# terms of the Do What The Fuck You Want To Public License, Version 2,
# as published by Sam Hocevar. See http://www.wtfpl.net/ for more details.

PLUGIN_NAME = 'Wikidata Genre'
PLUGIN_AUTHOR = 'Daniel Sobey, Sambhav Kothari, Sophist-UK'
PLUGIN_DESCRIPTION = '''
Query wikidata to get genre tags.
<br/><br/>
Since genres can be gathered from multiple sources and the genre tag may be overwritten,
we also set a hidden variable _genre_wikidata to the same values for use in scripts.
'''
PLUGIN_VERSION = '1.4.6'
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
                log.error('Error compiling regex ignore-tag "%s"', tag, exc_info=True)
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

        log.info('WIKIDATA plugin initialised - version %s', PLUGIN_VERSION)

    # not used
    def process_release(self, album, metadata, release):
        self.ws = album.tagger.webservice
        self.log = album.log
        for rg_id in metadata.getall('musicbrainz_releasegroupid'):
            log.debug('WIKIDATA: Processing release group %s...', rg_id)
            self.process_request(metadata, album, rg_id, item_type='release-group')
        for artist_id in metadata.getall('musicbrainz_albumartistid'):
            log.debug('WIKIDATA: Processing release artist %s...', artist_id)
            self.process_request(metadata, album, artist_id, item_type='artist')

    # Main processing function
    # First see if we have already found what we need in the cache, finalize loading
    # Next see if we are already looking for the item
    #   If we are, add this item to the list of items to be updated once we find what we are looking for.
    #   Otherwise we are the first one to look up this item, start a new request
    # metadata, map containing the new metadata

    def process_request(self, metadata, album, item_id, item_type):
        if item_id in self.cache:
            log.debug('WIKIDATA: Found %s %s in cache', item_type, item_id)
            genre_list = self.cache[item_id]
            new_genre = set(metadata.getall("genre"))
            new_genre.update(genre_list)
            #sort the new genre list so that they don't appear as new entries (not a change) next time
            metadata["genre"] = metadata["~genre_wikidata"] = self.genre_delimiter.join(sorted(new_genre))
            return

        # pending requests are handled by adding the metadata object to a
        # list of things to be updated when the genre is found
        if item_id in self.itemAlbums:
            self.requests[item_id].append(metadata)
            log.debug('WIKIDATA: Request for %s %s pending - track added', item_type, item_id)
            return

        self.requests[item_id] = [metadata]
        self.itemAlbums[item_id] = album
        album._requests += 1
        log.debug('WIKIDATA: Request for %s %s added', item_type, item_id)

        path = '/ws/2/%s/%s' % (item_type, item_id)
        queryargs = {"inc": "url-rels"}
        self.ws.get(
            self.mb_host, self.mb_port, path,
            partial(self.musicbrainz_release_lookup, item_id, metadata),
            parse_response_type="xml", priority=False, important=False, queryargs=queryargs)

    def musicbrainz_release_lookup(self, item_id, metadata, response, reply, error):
        found = False
        if error:
            errormsg = 'WIKIDATA: Network error getting release group data: %s' % item_id
            log.warning(errormsg)
            self.finalise_request(item_id, errormsg)
            return

        if 'metadata' not in response.children:
            log.warning('WIKIDATA: No wikidata metadata found for release group %s', item_id)
            self.finalise_request(item_id, errormsg)
            return

        if 'release_group' in response.metadata[0].children and self.use_release_group_genres:
            if 'relation_list' in response.metadata[0].release_group[0].children:
                for relation in response.metadata[0].release_group[0].relation_list[0].relation:
                    if relation.type == 'wikidata' and 'target' in relation.children:
                        found = True
                        wikidata_url = relation.target[0].text
                        log.info('WIKIDATA: wikidata url found for RELEASE_GROUP: %s', wikidata_url)
                        self.process_wikidata(Wikidata.RELEASE_GROUP, wikidata_url, item_id)
        if 'artist' in response.metadata[0].children and self.use_artist_genres:
            if 'relation_list' in response.metadata[0].artist[0].children:
                for relation in response.metadata[0].artist[0].relation_list[0].relation:
                    if relation.type == 'wikidata' and 'target' in relation.children:
                        found = True
                        wikidata_url = relation.target[0].text
                        self.process_wikidata(Wikidata.ARTIST, wikidata_url, item_id)
                        log.info('WIKIDATA: wikidata url found for ARTIST: %s', wikidata_url)
        if 'work' in response.metadata[0].children and self.use_work_genres:
            if 'relation_list' in response.metadata[0].work[0].children:
                for relation in response.metadata[0].work[0].relation_list[0].relation:
                    if relation.type == 'wikidata' and 'target' in relation.children:
                        found = True
                        wikidata_url = relation.target[0].text
                        log.info('WIKIDATA: wikidata url found for WORK: %s', wikidata_url)
                        self.process_wikidata(Wikidata.WORK, wikidata_url, item_id)

        if not found:
            log.debug('WIKIDATA: No wikidata url found for mbid: %s', item_id)

        self.finalise_request(item_id)

    def process_wikidata(self, genre_source_type, wikidata_url, item_id):
        album = self.itemAlbums[item_id]
        album._requests += 1
        item = wikidata_url.split('/')[4]
        path = "/wiki/Special:EntityData/" + item + ".rdf"
        log.debug('WIKIDATA: Fetching from wikidata.org%s', path)
        self.ws.get(WIKIDATA_HOST, WIKIDATA_PORT, path,
                    partial(self.parse_wikidata_response, item, item_id, genre_source_type),
                    parse_response_type="xml", priority=False, important=False)

    def parse_wikidata_response(self, item, item_id, genre_source_type, response, reply, error):
        if error:
            errormsg = 'WIKIDATA: Network error getting genre data: %s' % item_id
            log.warning(errormsg)
            self.finalise_request(item_id, errormsg)
            return
        if 'RDF' not in response.children:
            return

        genre_list = self.parse_wikidata_nodes(item, response.RDF[0].Description)
        if genre_list:
            log.debug('WIKIDATA: Caching results and updating %d entries with %s: %s', len(self.requests[item_id]), item_id, genre_list)
            self.cache[item_id] = genre_list

            for metadata in self.requests[item_id]:
                if genre_source_type == Wikidata.RELEASE_GROUP:
                    metadata['~release_group_genre_sourced'] = True
                elif genre_source_type == Wikidata.ARTIST:
                    if (
                        (self.use_artist_only_if_no_release and metadata['~release_group_genre_sourced'])
                        or
                        matches_ignored(self.ignore_genres_from_these_artists_list, metadata.get("artist"))
                    ):
                        if item_id not in self.cache:
                            self.cache[item_id] = []
                        log.debug('WIKIDATA: Not setting Artist-sourced genre for %s: %s', metadata['musicbrainz_trackid'], genre_list)
                        continue
                    log.debug('WIKIDATA: Adding Artist-sourced genre to %s: %s', metadata['musicbrainz_trackid'], genre_list)

                genres = metadata.getall("genre")
                if self.genre_delimiter:
                    genres = [g for gs in genres for g in gs.split(self.genre_delimiter)]
                genres += genre_list
                # eliminate duplicates and sort to ensure consistency
                genres = metadata["~genre_wikidata"] = sorted(set(genres))
                log.info('WIKIDATA: Setting metadata genre for %s: %s', metadata['musicbrainz_trackid'], genres)
                if self.genre_delimiter:
                    metadata["genre"] = self.genre_delimiter.join(genres)
                else:
                    metadata["genre"] = genres
        else:
            log.info('WIKIDATA: Genres not found in genre response for %s', item_id)

        self.finalise_request(item_id)

    def parse_wikidata_nodes(self, item, nodes):
        genre_entities = []
        for node in nodes:
            if 'about' not in node.attribs:
                continue
            if node.attribs.get('about') != 'http://www.wikidata.org/entity/%s' % item:
                continue
            for key, val in list(node.children.items()):
                if key == 'P136':
                    for i in val:
                        if 'resource' in i.attribs:
                            tmp = i.attribs.get('resource')
                            tmp_split = tmp.split('/')
                            if len(tmp_split) != 5 or 'entity' != tmp_split[3]:
                                continue
                            genre_id = tmp_split[4]
                            log.debug('WIKIDATA: Genre id found: %s', genre_id)
                            genre_entities.append(tmp)

        if not genre_entities:
            return genre_entities

        genre_list = []
        for node in nodes:
            if 'about' not in node.attribs or node.attribs.get('about') not in genre_entities:
                continue

            names = node.children.get('name')
            if not names:
                log.warning('WIKIDATA: Genre response node does not contain a name field: %s', node.attribs.get('about'))
                continue
            for title in names:
                if title.attribs.get('lang') == 'en':
                    genre = title.text.title()
                    if not matches_ignored(self.ignore_these_genres_list, genre):
                        genre_list.append(genre)
                        log.debug('WIKIDATA: Genre ALLOWED: %s', genre)
                    else:
                        log.debug('WIKIDATA: Genre IGNORED: %s', genre)
        return genre_list

    def finalise_request(self, item_id, info_error=''):
        album = self.itemAlbums[item_id]
        if info_error:
            album.error_append(info_error)
        album._requests -= 1
        if not album._requests:
            self.itemAlbums = {k: v for k, v in self.itemAlbums.items() if v != album}
            album._finalize_loading(None)
        if not self.itemAlbums:
            self.requests.clear()
            log.info('WIKIDATA: Idle')

    def process_track(self, album, metadata, track, release):
        self.update_settings()
        self.ws = album.tagger.webservice
        self.log = album.log

        log.info('WIKIDATA: Processing Track %s...', metadata['musicbrainz_trackid'])
        if self.use_release_group_genres:
            for release_group in metadata.getall('musicbrainz_releasegroupid'):
                log.info('WIKIDATA: Looking up release group for %s', release_group)
                self.process_request(metadata, album, release_group, item_type='release-group')

        artists = []
        if self.use_artist_genres:
            for artist in metadata.getall('musicbrainz_albumartistid'):
                artists.append(artist)
                log.info('WIKIDATA: Looking up release artist %s', artist)
                self.process_request(metadata, album, artist, item_type='artist')

            for artist in metadata.getall('musicbrainz_artistid'):
                if artist not in artists: # avoid duplicates
                    artists.append(artist)
                    log.info('WIKIDATA: Looking up track artist %s', artist)
                    self.process_request(metadata, album, artist, item_type='artist')

        if self.use_work_genres:
            for workid in metadata.getall('musicbrainz_workid'):
                log.info('WIKIDATA: Looking up work %s', workid)
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
