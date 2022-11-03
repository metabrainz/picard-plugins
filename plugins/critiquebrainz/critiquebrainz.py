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

WARNING: Experimental plugin. All guarantees voided by use.

Example: Taylor Swift
Release: Midnights
 https://musicbrainz.org/release/e348fdd6-f73b-47fe-94c4-670bfee26a39 ,
 https://critiquebrainz.org/release-group/0dcc84fb-c592-46e9-ba92-a52bb44dd553

Recording:
 https://musicbrainz.org/recording/93113326-93e9-409c-a3d6-5ec91864ba30 ,
 https://critiquebrainz.org/recording/93113326-93e9-409c-a3d6-5ec91864ba30'''
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.txt"
PLUGIN_VERSION = "1.0.1"
PLUGIN_API_VERSIONS = ["2.0"]

from functools import partial
from picard import log
from picard.metadata import register_album_metadata_processor
from picard.metadata import register_track_metadata_processor
from picard.webservice import ratecontrol
from picard.util import load_json

CRITIQUEBRAINZ_HOST = "critiquebrainz.org"
CRITIQUEBRAINZ_PORT = 80

ratecontrol.set_minimum_delay((CRITIQUEBRAINZ_HOST, CRITIQUEBRAINZ_PORT), 50)


def result_review(album, metadata, data, reply, error):
    if error:
        album._requests -= 1
        album._finalize_loading(None)
        return

    try:
        reviews = load_json(data).get("reviews")
        if reviews:
            for review in reviews:
                if "last_revision" in review:
                    ident = review["entity_type"].replace("_", "-") + "_review_" + review["published_on"] + "_" + review["user"]["display_name"] + "_" + review["language"]
                    review_text = review["last_revision"]["text"] + "\n\nEine Bewertung mit " + str(review["last_revision"]["rating"]) + " von 5 Sternen veröffentlich durch " + review["user"]["display_name"] + " am " + review["published_on"] + " lizensiert unter " + review["full_name"] + ".";
                    if "comment:" + ident in metadata:
                        metadata["comment:" + ident] = review_text
                    else:
                        metadata.add("comment:" + ident, review_text)
                    review_url = "https://critiquebrainz.org/review/" + review["id"]
                    if "website:" + ident in metadata:
                        metadata["website:" + ident] = review_url
                    else:
                        metadata.add("website:" + ident, review_url)
            log.debug("%s: success parsing %s reviews (%s) from response", PLUGIN_NAME, reviews["count"], metadata["albumtitle"])
    except Exception as e:
        log.error("%s: error parsing review (%s) from response: %s", PLUGIN_NAME, metadata["albumtitle"], str(e))
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
        partial(result_review, album, metadata),
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
        partial(result_review, album, metadata),
        priority=True,
        parse_response_type=None,
        queryargs=queryargs
    )
    album._requests += 1


register_album_metadata_processor(process_releasegroup)
register_track_metadata_processor(process_recording)
