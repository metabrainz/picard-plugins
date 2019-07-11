# -*- coding: utf-8 -*-
#
# Copyright (C) 2017, 2019 Philipp Wolfer
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

PLUGIN_NAME = "Load as non-album track"
PLUGIN_AUTHOR = "Philipp Wolfer"
PLUGIN_DESCRIPTION = ("Allows loading selected tracks as non-album tracks. "
                      "Useful for tagging single tracks where you do not care "
                      "about the album.")
PLUGIN_VERSION = "0.3"
PLUGIN_API_VERSIONS = ["1.4.0", "2.0", "2.1", "2.2"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard import log
from picard.track import Track
from picard.ui.itemviews import (
    BaseAction,
    register_track_action,
)


class LoadAsNat(BaseAction):
    NAME = "Load as non-album track..."

    def callback(self, objs):
        tracks = [t for t in objs if isinstance(t, Track)]

        if len(tracks) == 0:
            return

        for track in tracks:
            nat = self.tagger.load_nat(
                track.metadata['musicbrainz_recordingid'])
            for file in list(track.linked_files):
                file.move(nat)
                metadata = file.metadata
                metadata.delete('albumartist')
                metadata.delete('albumartistsort')
                metadata.delete('albumsort')
                metadata.delete('asin')
                metadata.delete('barcode')
                metadata.delete('catalognumber')
                metadata.delete('discnumber')
                metadata.delete('discsubtitle')
                metadata.delete('media')
                metadata.delete('musicbrainz_albumartistid')
                metadata.delete('musicbrainz_albumid')
                metadata.delete('musicbrainz_discid')
                metadata.delete('musicbrainz_releasegroupid')
                metadata.delete('releasecountry')
                metadata.delete('releasestatus')
                metadata.delete('releasetype')
                metadata.delete('totaldiscs')
                metadata.delete('totaltracks')
                metadata.delete('tracknumber')
                log.debug("[LoadAsNat] deleted tags: %r", metadata.deleted_tags)


register_track_action(LoadAsNat())
