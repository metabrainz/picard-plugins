# -*- coding: utf-8 -*-
#
# Copyright (C) 2024
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

PLUGIN_NAME = "Look Up with Harmony"
PLUGIN_AUTHOR = "Jade"
PLUGIN_DESCRIPTION = """
Adds a right click option to look up releases on Harmony using the GTIN code.
If a MusicBrainz release ID is available, it will be included in the lookup URL.
"""
PLUGIN_VERSION = "0.1.0"
PLUGIN_API_VERSIONS = ["2.10"]  # Only tested in 2.13 but should be fine
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.txt"

from picard import log
from picard.album import Album
from picard.cluster import Cluster
from picard.track import Track
from picard.ui.itemviews import (
    BaseAction,
    register_album_action,
    register_cluster_action,
    register_track_action,
)
from picard.util.webbrowser2 import open as web_open


def perform_harmony_lookup(metadata):
    """Perform a Harmony lookup using the metadata from an album, track, or cluster."""
    try:
        barcode_value = metadata.get("barcode", "")
        log.debug(
            "{0}: barcode tag raw content: {1} (type: {2})".format(
                PLUGIN_NAME, repr(barcode_value), type(barcode_value).__name__
            )
        )

        # Convert to string and strip (handle lists, etc.)
        if isinstance(barcode_value, list):
            gtin = str(barcode_value[0]).strip() if barcode_value else ""
        else:
            gtin = str(barcode_value).strip() if barcode_value else ""

        # Fallback to 'upc' tag if barcode is not available
        if not gtin:
            upc_value = metadata.get("upc", "")
            log.debug(
                "{0}: upc tag raw content: {1} (type: {2})".format(
                    PLUGIN_NAME, repr(upc_value), type(upc_value).__name__
                )
            )

            if isinstance(upc_value, list):
                gtin = str(upc_value[0]).strip() if upc_value else ""
            else:
                gtin = str(upc_value).strip() if upc_value else ""

        if not gtin:
            log.warning(
                "{0}: No GTIN/UPC code found for this release.".format(PLUGIN_NAME)
            )
            return

        log.info("{0}: Using GTIN: {1}".format(PLUGIN_NAME, gtin))

        mbid_value = metadata.get("musicbrainz_albumid", "")
        log.debug(
            "{0}: musicbrainz_albumid tag raw content: {1} (type: {2})".format(
                PLUGIN_NAME, repr(mbid_value), type(mbid_value).__name__
            )
        )

        if isinstance(mbid_value, list):
            musicbrainz_albumid = str(mbid_value[0]).strip() if mbid_value else ""
        else:
            musicbrainz_albumid = str(mbid_value).strip() if mbid_value else ""

        # Build the Harmony URL
        url = "https://harmony.pulsewidth.org.uk/release?gtin={0}&deezer=&itunes=&spotify=&tidal=&musicbrainz={1}".format(
            gtin, musicbrainz_albumid
        )

        log.debug("{0}: Opening Harmony lookup: {1}".format(PLUGIN_NAME, url))
        web_open(url)
    except Exception as e:
        log.error("{0}: Error during Harmony lookup: {1}".format(PLUGIN_NAME, str(e)))


class LookupHarmonyAlbum(BaseAction):
    NAME = "Look up on Harmony"

    def callback(self, objs):
        for obj in objs:
            if isinstance(obj, Album):
                perform_harmony_lookup(obj.metadata)


class LookupHarmonyCluster(BaseAction):
    NAME = "Look up on Harmony"

    def callback(self, objs):
        for obj in objs:
            if isinstance(obj, Cluster):
                perform_harmony_lookup(obj.metadata)


class LookupHarmonyTrack(BaseAction):
    NAME = "Look up on Harmony"

    def callback(self, objs):
        for obj in objs:
            if isinstance(obj, Track):
                perform_harmony_lookup(obj.metadata)


# Register the actions for albums, tracks, and clusters
register_album_action(LookupHarmonyAlbum())
register_cluster_action(LookupHarmonyCluster())
register_track_action(LookupHarmonyTrack())
