PLUGIN_NAME = 'Musixmatch Lyrics'
PLUGIN_AUTHOR = 'm-yn'
PLUGIN_DESCRIPTION = 'Fetch first 30% of lyrics from Musixmatch'
PLUGIN_VERSION = '0.2'
PLUGIN_API_VERSIONS = ["0.9.0", "0.10", "0.15"]


from picard.metadata import register_track_metadata_processor
from picard.ui.options import register_options_page, OptionsPage
from picard.config import TextOption
from ui_options_musixmatch import Ui_MusixmatchOptionsPage

class MusixmatchOptionsPage(OptionsPage):
	NAME = 'musixmatch'
	TITLE = 'Musixmatch API Key'
	PARENT = "plugins"
	options = [
			TextOption("setting","musixmatch_api_key","")
	]
	def __init__(self,parent=None):
		super(MusixmatchOptionsPage,self).__init__(parent)
		self.ui = Ui_MusixmatchOptionsPage()
		self.ui.setupUi(self)
	
	def load(self):
		self.ui.api_key.setText(self.config.setting["musixmatch_api_key"])
	
	def save(self):
		self.config.setting["musixmatch_api_key"] = self.ui.api_key.text()
register_options_page(MusixmatchOptionsPage)

import picard.tagger as tagger
import os
try:
	os.environ['MUSIXMATCH_API_KEY'] = tagger.config.setting["musixmatch_api_key"]
except:
	pass

from musixmatch import track as TRACK

def process_track(album, metadata, release, track):
	if('MUSIXMATCH_API_KEY' not in os.environ):
		return
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
