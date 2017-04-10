# -*- coding: utf-8 -*-

PLUGIN_NAME = "Load as non-album track"
PLUGIN_AUTHOR = "Philipp Wolfer"
PLUGIN_DESCRIPTION = "Allows loading selected tracks as non-album tracks. Useful for tagging single tracks where you do not care about the album."
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["1.4.0", "2.0"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard import log
from picard.album import Track
from picard.ui.itemviews import BaseAction, register_track_action

class LoadAsNat(BaseAction):
	NAME = "Load as non-album track..."

	def callback(self, objs):
		tracks = [t for t in objs if isinstance(t, Track)]

		if len(tracks) == 0:
			return

		for track in tracks:
			nat = self.tagger.load_nat(track.metadata['musicbrainz_recordingid'])
			for file in track.iterfiles():
				file.move(nat)
				file.metadata.delete('albumartist')
				file.metadata.delete('albumartistsort')
				file.metadata.delete('albumsort')
				file.metadata.delete('asin')
				file.metadata.delete('barcode')
				file.metadata.delete('catalognumber')
				file.metadata.delete('discnumber')
				file.metadata.delete('discsubtitle')
				file.metadata.delete('media')
				file.metadata.delete('musicbrainz_albumartistid')
				file.metadata.delete('musicbrainz_albumid')
				file.metadata.delete('musicbrainz_discid')
				file.metadata.delete('musicbrainz_releasegroupid')
				file.metadata.delete('releasecountry')
				file.metadata.delete('releasestatus')
				file.metadata.delete('releasetype')
				file.metadata.delete('totaldiscs')
				file.metadata.delete('totaltracks')
				file.metadata.delete('tracknumber')
				log.debug("[LoadAsNat] deleted tags: %r", file.metadata.deleted_tags)


register_track_action(LoadAsNat())
