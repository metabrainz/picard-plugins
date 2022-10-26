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

PLUGIN_NAME = 'Musicbrainz Relations Website'
PLUGIN_AUTHOR = 'Tobias Sarner'
PLUGIN_DESCRIPTION = '''Uses Musicbrainz relations to set website.

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
# comment:Artist-1-website https://www.taylorswift.com/

MUSICBRAINZ_HOST = "musicbrainz.org"
MUSICBRAINZ_PORT = 80

ratecontrol.set_minimum_delay((MUSICBRAINZ_HOST, MUSICBRAINZ_PORT), 50)


def result_albumartist(album, metadata, data, reply, error):
    prefix = "AlbumArtist"
    musicbrainz_id = metadata["musicbrainz_albumartistid"]
    if error:
        album._requests -= 1
        album._finalize_loading(None)
        return

    try:
        data = load_json(data).get("relations")
        if data:
            idx = 0
            for relations in data:
                if "url" in relations and "resource" in relations["url"]:
                    idx += 1
                    key = "website:" + prefix + "-" + str(idx) + "-" + relations["type"]
                    if key in metadata:
                        metadata.delete(key)
                    metadata.add(key, relations["url"]["resource"])

            log.debug("%s: %s %s (%s) Parsed response", PLUGIN_NAME, prefix, musicbrainz_id, metadata["albumtitle"])
    except Exception as e:
        log.error("%s: %s %s (%s) Error parsing response: %s", PLUGIN_NAME, prefix, musicbrainz_id, metadata["albumtitle"], str(e))
    finally:
        album._requests -= 1
        album._finalize_loading(None)


def result_release(album, metadata, data, reply, error):
    prefix = "Release"
    musicbrainz_id = metadata["musicbrainz_albumid"]
    if error:
        album._requests -= 1
        album._finalize_loading(None)
        return

    try:
        data = load_json(data).get("relations")
        if data:
            idx = 0
            for relations in data:
                if "url" in relations and "resource" in relations["url"]:
                    idx += 1
                    key = "website:" + prefix + "-" + str(idx) + "-" + relations["type"]
                    if key in metadata:
                        metadata.delete(key)
                    metadata.add(key, relations["url"]["resource"])

            log.debug("%s: %s %s (%s) Parsed response", PLUGIN_NAME, prefix, musicbrainz_id, metadata["albumtitle"])
    except Exception as e:
        log.error("%s: %s %s (%s) Error parsing response: %s", PLUGIN_NAME, prefix, musicbrainz_id, metadata["albumtitle"], str(e))
    finally:
        album._requests -= 1
        album._finalize_loading(None)


def result_releasegroup(album, metadata, data, reply, error):
    prefix = "ReleaseGroup"
    musicbrainz_id = metadata["musicbrainz_releasegroupid"]
    if error:
        album._requests -= 1
        album._finalize_loading(None)
        return

    try:
        data = load_json(data).get("relations")
        if data:
            idx = 0
            for relations in data:
                if "url" in relations and "resource" in relations["url"]:
                    idx += 1
                    key = "website:" + prefix + "-" + str(idx) + "-" + relations["type"]
                    if key in metadata:
                        metadata.delete(key)
                    metadata.add(key, relations["url"]["resource"])

            log.debug("%s: %s %s (%s) Parsed response", PLUGIN_NAME, prefix, musicbrainz_id, metadata["albumtitle"])
    except Exception as e:
        log.error("%s: %s %s (%s) Error parsing response: %s", PLUGIN_NAME, prefix, musicbrainz_id, metadata["albumtitle"], str(e))
    finally:
        album._requests -= 1
        album._finalize_loading(None)


def process_relations(album, metadata, release):
    queryargs = {
        "fmt": "json",
        "inc": "url-rels"
    }
    album.tagger.webservice.get(
        MUSICBRAINZ_HOST,
        MUSICBRAINZ_PORT,
        "/ws/2/artist/" + metadata["musicbrainz_albumartistid"],
        partial(result_albumartist, album, metadata),
        priority=True,
        parse_response_type=None,
        queryargs=queryargs
    )
    album._requests += 1
    album.tagger.webservice.get(
        MUSICBRAINZ_HOST,
        MUSICBRAINZ_PORT,
        "/ws/2/release/" + metadata["musicbrainz_albumid"],
        partial(result_release, album, metadata),
        priority=True,
        parse_response_type=None,
        queryargs=queryargs
    )
    album._requests += 1
    album.tagger.webservice.get(
        MUSICBRAINZ_HOST,
        MUSICBRAINZ_PORT,
        "/ws/2/release-group/" + metadata["musicbrainz_releasegroupid"],
        partial(result_releasegroup, album, metadata),
        priority=True,
        parse_response_type=None,
        queryargs=queryargs
    )
    album._requests += 1


register_album_metadata_processor(process_relations)
