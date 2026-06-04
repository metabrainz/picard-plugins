# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 alydevs <aly@aly.pet>
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
# Disclosure: Claude Sonnet 4.6 was used in the creation of pseudo-release-titlesort.py

# Plugin metadata
# =============================================================================
PLUGIN_NAME = "Pseudo-Release Title Sort"
PLUGIN_AUTHOR = "alydevs <aly@aly.pet>"
PLUGIN_DESCRIPTION = """
For releases matched to a Pseudo-Release on MusicBrainz, sets the **Title Sort**
tag (`titlesort`) to the pseudo-release's own track title (e.g. a romanised
English transliteration) rather than leaving it blank or using the original-
language recording title.
 
If the matched release is *not* a pseudo-release, the tag is left untouched.
"""
PLUGIN_VERSION = "1.0.4"
PLUGIN_API_VERSIONS = ["2.0", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard import log
from picard.metadata import register_track_metadata_processor


def set_titlesort_from_pseudo_release(tagger, metadata, track, release):
    """
    Called by Picard for every track after it has populated `metadata` from MusicBrainz
    """

    # Only act on pseudo-releases.
    # release["status"] is the <status> text, e.g. "Pseudo-Release".
    try:
        status = release.get("status", "")
        if not status:
            return
        if status != "Pseudo-Release":
            return
    except Exception as e:
        log.debug(str(e))
        return

    # Pull the track-level title if it differs from recording title
    try:
        title = track.get("title", "")
        if not title:
            log.warning("No title tag on track node")
            return
        if title == track.get("recording", {}).get("title",""):
            log.info("Pseudo-release title matches recording title, skipping")
            return
        metadata["titlesort"] = title
        log.info(f"Set titlesort to {title}")
    except Exception as e:
        log.warning(str(e))


register_track_metadata_processor(set_titlesort_from_pseudo_release)
