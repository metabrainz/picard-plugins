PLUGIN_NAME = 'Feat. Artists in Titles'
PLUGIN_AUTHOR = 'Lukas Lalinsky, Michael Wiencek, Bryan Toth, Brian Altenburg'
PLUGIN_DESCRIPTION = 'Move "feat." and other from artist names to album and track titles. Match is case insensitive.'
PLUGIN_VERSION = "0.4"
PLUGIN_API_VERSIONS = ["0.9.0", "0.10", "0.15", "0.16"]

from picard.metadata import register_album_metadata_processor, register_track_metadata_processor
import re 

list = ['feat.', 'with', 'duet med', 'med']
ignoreList = ['danser med drenge']

def move_album_featartists(tagger, metadata, release):
	for item in list:
		for item2 in ignoreList:
			if item2.find(item) > -1:
				break
			_item_re = re.compile(r"([\s\S]+) "+item+" ([\s\S]+)", re.IGNORECASE)
			match = _item_re.match(metadata["albumartist"])
			if match:
				metadata["albumartist"] = match.group(1)
				metadata["album"] += " ("+item+" %s)" % match.group(2)

def move_track_featartists(tagger, metadata, release, track):
	for item in list:
		for item2 in ignoreList:
			if item2.find(item) > -1:
				break
			_item_re = re.compile(r"([\s\S]+) "+item+" ([\s\S]+)", re.IGNORECASE)
			match = _item_re.match(metadata["artist"])
			if match:
				metadata["artist"] = match.group(1)
				metadata["title"] += " ("+item+" %s)" % match.group(2)

register_album_metadata_processor(move_album_featartists)
register_track_metadata_processor(move_track_featartists)
