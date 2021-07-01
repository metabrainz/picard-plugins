# -*- coding: utf-8 -*-

PLUGIN_NAME = 'Last.fm'
PLUGIN_AUTHOR = 'Lukáš Lalinský, Philipp Wolfer'
PLUGIN_DESCRIPTION = 'Use tags from Last.fm as genre.'
PLUGIN_VERSION = "0.10.1"
PLUGIN_API_VERSIONS = ["2.0"]

import re
from functools import partial
from PyQt5 import QtCore
from picard import config, log
from picard.config import BoolOption, IntOption, TextOption
from picard.metadata import register_track_metadata_processor
from picard.plugins.lastfm.ui_options_lastfm import Ui_LastfmOptionsPage
from picard.ui.options import register_options_page, OptionsPage
from picard.util import build_qurl
from picard.webservice import ratecontrol

LASTFM_HOST = 'ws.audioscrobbler.com'
LASTFM_PORT = 80
LASTFM_PATH = '/2.0/'
LASTFM_API_KEY = '0a210a4a6741f2ec8f27a791b9d5d971'

# From https://www.last.fm/api/tos, 2018-09-04
# 4.4 […] You will not make more than 5 requests per originating IP address per
# second, averaged over a 5 minute period, without prior written consent. […]
ratecontrol.set_minimum_delay((LASTFM_HOST, LASTFM_PORT), 200)

# Cache for Tags to avoid re-requesting tags within same Picard session
_cache = {}

# Keeps track of requests for tags made to webservice API but not yet returned
# (to avoid re-requesting the same URIs)
_pending_requests = {}

# TODO: move this to an options page
TRANSLATE_TAGS = {
    "hip hop": "Hip-Hop",
    "synth-pop": "Synthpop",
    "electronica": "Electronic",
}
TITLE_CASE = True


def parse_ignored_tags(ignore_tags_setting):
    ignore_tags = []
    for tag in ignore_tags_setting.lower().split(','):
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
    tag = tag.lower().strip()
    for pattern in ignore_tags:
        if hasattr(pattern, 'match'):
            match = pattern.match(tag)
        else:
            match = pattern == tag
        if match:
            return True
    return False


def _tags_finalize(album, metadata, tags, next_):
    if next_:
        next_(tags)
    else:
        tags = list(set(tags))
        if tags:
            join_tags = config.setting["lastfm_join_tags"]
            if join_tags:
                tags = join_tags.join(tags)
            metadata["genre"] = tags


def _tags_downloaded(album, metadata, min_usage, ignore, next_, current, data,
                     reply, error):
    if error:
        album._requests -= 1
        album._finalize_loading(None)
        return

    try:
        try:
            intags = data.lfm[0].toptags[0].tag
        except AttributeError:
            intags = []
        tags = []
        for tag in intags:
            name = tag.name[0].text.strip()
            try:
                count = int(tag.count[0].text.strip())
            except ValueError:
                count = 0
            if count < min_usage:
                break
            try:
                name = TRANSLATE_TAGS[name]
            except KeyError:
                pass
            if not matches_ignored(ignore, name):
                tags.append(name.title())
        url = reply.url().toString()
        _cache[url] = tags
        _tags_finalize(album, metadata, current + tags, next_)

        # Process any pending requests for the same URL
        if url in _pending_requests:
            pending = _pending_requests[url]
            del _pending_requests[url]
            for delayed_call in pending:
                delayed_call()

    except Exception:
        log.error('Problem processing download tags', exc_info=True)
    finally:
        album._requests -= 1
        album._finalize_loading(None)


def get_tags(album, metadata, queryargs, min_usage, ignore, next_, current):
    """Get tags from an URL."""
    url = build_qurl(
        LASTFM_HOST, LASTFM_PORT, LASTFM_PATH, queryargs).toString()
    if url in _cache:
        _tags_finalize(album, metadata, current + _cache[url], next_)
    else:
        # If we have already sent a request for this URL, delay this call
        if url in _pending_requests:
            _pending_requests[url].append(
                partial(get_tags, album, metadata, queryargs, min_usage,
                        ignore, next_, current))
        else:
            _pending_requests[url] = []
            album._requests += 1
            album.tagger.webservice.get(
                LASTFM_HOST, LASTFM_PORT, LASTFM_PATH,
                partial(_tags_downloaded, album, metadata, min_usage, ignore,
                        next_, current),
                queryargs=queryargs, parse_response_type='xml',
                priority=True, important=True)


def encode_str(s):
    s = QtCore.QUrl.toPercentEncoding(s)
    return bytes(s).decode()


def get_queryargs(queryargs):
    queryargs = {k: encode_str(v) for (k, v) in queryargs.items()}
    queryargs['api_key'] = LASTFM_API_KEY
    return queryargs


def get_track_tags(album, metadata, artist, track, min_usage,
                   ignore, next_, current):
    """Get track top tags."""
    queryargs = get_queryargs({
        'method': 'Track.getTopTags',
        'artist': artist,
        'track': track,
    })
    get_tags(album, metadata, queryargs, min_usage, ignore, next_, current)


def get_artist_tags(album, metadata, artist, min_usage,
                    ignore, next_, current):
    """Get artist top tags."""
    queryargs = get_queryargs({
        'method': 'Artist.getTopTags',
        'artist': artist,
    })
    get_tags(album, metadata, queryargs, min_usage, ignore, next_, current)


def process_track(album, metadata, track, release):
    use_track_tags = config.setting["lastfm_use_track_tags"]
    use_artist_tags = config.setting["lastfm_use_artist_tags"]
    min_tag_usage = config.setting["lastfm_min_tag_usage"]
    ignore_tags = parse_ignored_tags(config.setting["lastfm_ignore_tags"])
    if use_track_tags or use_artist_tags:
        artist = metadata["artist"]
        title = metadata["title"]
        if artist:
            if use_artist_tags:
                get_artist_tags_func = partial(get_artist_tags, album,
                                               metadata, artist, min_tag_usage,
                                               ignore_tags, None)
            else:
                get_artist_tags_func = None
            if title and use_track_tags:
                get_track_tags(album, metadata, artist, title, min_tag_usage,
                               ignore_tags, get_artist_tags_func, [])
            elif get_artist_tags_func:
                get_artist_tags_func([])


class LastfmOptionsPage(OptionsPage):

    NAME = "lastfm"
    TITLE = "Last.fm"
    PARENT = "plugins"

    options = [
        BoolOption("setting", "lastfm_use_track_tags", False),
        BoolOption("setting", "lastfm_use_artist_tags", False),
        IntOption("setting", "lastfm_min_tag_usage", 90),
        TextOption("setting", "lastfm_ignore_tags",
                   "seen live, favorites, /\\d+ of \\d+ stars/"),
        TextOption("setting", "lastfm_join_tags", ""),
    ]

    def __init__(self, parent=None):
        super(LastfmOptionsPage, self).__init__(parent)
        self.ui = Ui_LastfmOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        setting = config.setting
        self.ui.use_track_tags.setChecked(setting["lastfm_use_track_tags"])
        self.ui.use_artist_tags.setChecked(setting["lastfm_use_artist_tags"])
        self.ui.min_tag_usage.setValue(setting["lastfm_min_tag_usage"])
        self.ui.ignore_tags.setText(setting["lastfm_ignore_tags"])
        self.ui.join_tags.setEditText(setting["lastfm_join_tags"])

    def save(self):
        global _cache
        setting = config.setting
        if setting["lastfm_min_tag_usage"] != self.ui.min_tag_usage.value() \
           or setting["lastfm_ignore_tags"] != str(self.ui.ignore_tags.text()):
            _cache = {}
        setting["lastfm_use_track_tags"] = self.ui.use_track_tags.isChecked()
        setting["lastfm_use_artist_tags"] = self.ui.use_artist_tags.isChecked()
        setting["lastfm_min_tag_usage"] = self.ui.min_tag_usage.value()
        setting["lastfm_ignore_tags"] = str(self.ui.ignore_tags.text())
        setting["lastfm_join_tags"] = str(self.ui.join_tags.currentText())


register_track_metadata_processor(process_track)
register_options_page(LastfmOptionsPage)
