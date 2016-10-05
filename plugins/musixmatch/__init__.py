"""
Installation:
	Obtain API Key from Musixmatch:
		https://developer.musixmatch.com
"""
import os
os.environ['MUSIXMATCH_API_KEY'] = 'APIKEY'



PLUGIN_NAME = 'Musixmatch Lyrics'
PLUGIN_AUTHOR = 'm-yn'
PLUGIN_DESCRIPTION = 'Fetch first 30% of lyrics from Musixmatch'
PLUGIN_VERSION = '0.1'
PLUGIN_API_VERSIONS = ["0.9.0", "0.10", "0.15"]


from musixmatch import track as TRACK
from picard.metadata import register_track_metadata_processor

def process_track(album, metadata, release, track):
	try:
		t = TRACK.Track(metadata['musicbrainz_trackid'],musicbrainz=True).lyrics()
		if t['instrumental'] == 1:
			lyrics = "[Instrumental]"
		else:
			lyrics = t['lyrics_body']
		metadata['lyrics:description'] = lyrics
	except Exception as e:
		pass

register_track_metadata_processor(process_track)
