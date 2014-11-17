# -*- coding: utf-8 -*-

PLUGIN_NAME = u'Acousticbrainz'
PLUGIN_AUTHOR = u'Andrew Cook'
PLUGIN_DESCRIPTION = u'''Uses Acousticbrainz for mood and genre'''
PLUGIN_VERSION = "0.0"
PLUGIN_API_VERSIONS = ["0.15"]

from functools import partial
from picard.metadata import register_track_metadata_processor

ACOUSTICBRAINZ_HOST = "acousticbrainz.org"
ACOUSTICBRAINZ_PORT = 80

def result(album, metadata, release, track, data, reply, error):
    album._requests -= 1
    album._finalize_loading(None)

def process_track(album, metadata, release, track):
    album.tagger.xmlws.get(
        ACOUSTICBRAINZ_HOST,
        ACOUSTICBRAINZ_PORT,
        u"/%s/high-level" % (metadata["musicbrainz_recordingid"]),
        partial(result, album, metadata, release, track),
        priority=True
    )
    album._requests += 1

register_track_metadata_processor(process_track)
