# -*- coding: utf-8 -*-
# Critiquebrainz plugin for Picard
# Copyright (C) 2022  Tobias Sarner
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

PLUGIN_NAME = 'Critiquebrainz Review Comment'
PLUGIN_AUTHOR = 'Tobias Sarner'
PLUGIN_DESCRIPTION = '''Uses Critiquebrainz for comment as review or rating.

WARNING: Experimental plugin. All guarantees voided by use.'''
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.txt"
PLUGIN_VERSION = "1.0.0"
PLUGIN_API_VERSIONS = ["2.0"]

from functools import partial
from picard import log
from picard.metadata import register_album_metadata_processor
from picard.metadata import register_track_metadata_processor
from picard.webservice import ratecontrol
from picard.util import load_json

# Example: Taylor Swift
# Release: Midnights
# https://musicbrainz.org/release/e348fdd6-f73b-47fe-94c4-670bfee26a39
# https://critiquebrainz.org/release-group/0dcc84fb-c592-46e9-ba92-a52bb44dd553
#
# Recording:
# https://musicbrainz.org/recording/93113326-93e9-409c-a3d6-5ec91864ba30
# https://critiquebrainz.org/recording/93113326-93e9-409c-a3d6-5ec91864ba30

CRITIQUEBRAINZ_HOST = "critiquebrainz.org"
CRITIQUEBRAINZ_PORT = 80

ratecontrol.set_minimum_delay((CRITIQUEBRAINZ_HOST, CRITIQUEBRAINZ_PORT), 50)


def result_releasegroup(album, metadata, data, reply, error):
    if error:
        album._requests -= 1
        album._finalize_loading(None)
        return

    try:
        data = load_json(data).get("reviews")
        if data:
            idx = 0
            for review in data:
                if "last_revision" in review:
                    idx += 1
                    if "comment:ReleaseGroup-Review-" + str(idx) in metadata:
                        metadata.delete("comment:ReleaseGroup-Review-" + str(idx))
                    metadata.add("comment:ReleaseGroup-Review-" + str(idx), review["last_revision"]["text"])

            log.debug("%s: ReleaseGroup %s (%s) Parsed response", PLUGIN_NAME, metadata["musicbrainz_releasegroupid"], metadata["albumtitle"])
    except Exception as e:
        log.error("%s: ReleaseGroup %s (%s) Error parsing response: %s", PLUGIN_NAME, metadata["musicbrainz_releasegroupid"], metadata["albumtitle"], str(e))
    finally:
        album._requests -= 1
        album._finalize_loading(None)

def result_recording(album, metadata, data, reply, error):
    if error:
        album._requests -= 1
        album._finalize_loading(None)
        return

    try:
        data = load_json(data).get("reviews")
        if data:
            idx = 0
            for review in data:
                if "last_revision" in review:
                    idx += 1
                    if "comment:Recording-Review-" + str(idx) in metadata:
                        metadata.delete("comment:Recording-Review-" + str(idx))
                    metadata.add("comment:Recording-Review-" + str(idx), review["last_revision"]["text"])

            log.debug("%s: Track %s (%s) Parsed response", PLUGIN_NAME, metadata["musicbrainz_recordingid"], metadata["title"])
    except Exception as e:
        log.error("%s: Track %s (%s) Error parsing response: %s", PLUGIN_NAME, metadata["musicbrainz_recordingid"], metadata["title"], str(e))
    finally:
        album._requests -= 1
        album._finalize_loading(None)

def process_releasegroup(album, metadata, release):
    queryargs = {
        "entity_id": metadata["musicbrainz_releasegroupid"],
        "entity_type": "release_group"
    }
    album.tagger.webservice.get(
        CRITIQUEBRAINZ_HOST,
        CRITIQUEBRAINZ_PORT,
        "/ws/1/review",
        partial(result_releasegroup, album, metadata),
        priority=True,
        parse_response_type=None,
        queryargs=queryargs
    )
    album._requests += 1

def process_recording(album, metadata, track, release):
    queryargs = {
        "entity_id": metadata["musicbrainz_recordingid"],
        "entity_type": "recording"
    }
    album.tagger.webservice.get(
        CRITIQUEBRAINZ_HOST,
        CRITIQUEBRAINZ_PORT,
        "/ws/1/review",
        partial(result_recording, album, metadata),
        priority=True,
        parse_response_type=None,
        queryargs=queryargs
    )
    album._requests += 1

register_album_metadata_processor(process_releasegroup)
register_track_metadata_processor(process_recording)
