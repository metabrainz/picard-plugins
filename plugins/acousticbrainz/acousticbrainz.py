# -*- coding: utf-8 -*-
# Acousticbrainz plugin for Picard
# Copyright (C) 2015  Andrew Cook
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

PLUGIN_NAME = 'AcousticBrainz Mood-Genre'
PLUGIN_AUTHOR = 'Andrew Cook, Sambhav Kothari'
PLUGIN_DESCRIPTION = '''Uses AcousticBrainz for mood and genre.

WARNING: Experimental plugin. All guarantees voided by use.'''
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.txt"
PLUGIN_VERSION = "1.1"
PLUGIN_API_VERSIONS = ["2.0"]

from functools import partial
from picard import log
from picard.metadata import register_track_metadata_processor
from picard.webservice import ratecontrol
from picard.util import load_json

ACOUSTICBRAINZ_HOST = "acousticbrainz.org"
ACOUSTICBRAINZ_PORT = 80

ratecontrol.set_minimum_delay((ACOUSTICBRAINZ_HOST, ACOUSTICBRAINZ_PORT), 50)


def result(album, metadata, data, reply, error):
    if error or not "highlevel" in data:
        album._requests -= 1
        album._finalize_loading(None)
        return

    moods = []
    genres = []
    try:
        data = load_json(data)["highlevel"]
        for k, v in data.items():
            if k.startswith("genre_") and not v["value"].startswith("not_"):
                genres.append(v["value"])
            if k.startswith("mood_") and not v["value"].startswith("not_"):
                moods.append(v["value"])

        metadata["genre"] = genres
        metadata["mood"] = moods
        log.debug("%s: Track %s (%s) Parsed response (genres: %s, moods: %s)", PLUGIN_NAME, metadata["musicbrainz_recordingid"], metadata["title"], str(genres), str(moods))
    except Exception as e:
        log.error("%s: Track %s (%s) Error parsing response: %s", PLUGIN_NAME, metadata["musicbrainz_recordingid"], metadata["title"], str(e))
    finally:
        album._requests -= 1
        album._finalize_loading(None)


def process_track(album, metadata, release, track):
    album.tagger.webservice.get(
        ACOUSTICBRAINZ_HOST,
        ACOUSTICBRAINZ_PORT,
        "/%s/high-level" % (metadata["musicbrainz_recordingid"]),
        partial(result, album, metadata),
        priority=True,
        parse_response_type=None
    )
    album._requests += 1


register_track_metadata_processor(process_track)
