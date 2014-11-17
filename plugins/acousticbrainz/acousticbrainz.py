# -*- coding: utf-8 -*-

PLUGIN_NAME = u'Acousticbrainz'
PLUGIN_AUTHOR = u'Andrew Cook'
PLUGIN_DESCRIPTION = u'''Uses Acousticbrainz for mood and genre'''
PLUGIN_VERSION = "0.0"
PLUGIN_API_VERSIONS = ["0.15"]

from json import loads
from functools import partial
from picard import log
from picard.metadata import register_track_metadata_processor

ACOUSTICBRAINZ_HOST = "acousticbrainz.org"
ACOUSTICBRAINZ_PORT = 80

def result(album, metadata, release, track, data, reply, error):
    moods = []
    genres = []
    bpm = False
    try:
        data = loads(data)["highlevel"]
        for k, v in data.items():
            if k.startswith("genre_") and not v["value"].startswith("not_"):
                genres.append(v["value"])
            if k.startswith("mood_") and not v["value"].startswith("not_"):
                moods.append(v["value"])
        metadata["genre"] = genres
        metadata["moods"] = moods
    finally:
        album._requests -= 1
        album._finalize_loading(None)

def process_track(album, metadata, release, track):
    album.tagger.xmlws.download(
        ACOUSTICBRAINZ_HOST,
        ACOUSTICBRAINZ_PORT,
        u"/%s/high-level" % (metadata["musicbrainz_recordingid"]),
        partial(result, album, metadata, release, track),
        priority=True
    )
    album._requests += 1

register_track_metadata_processor(process_track)
