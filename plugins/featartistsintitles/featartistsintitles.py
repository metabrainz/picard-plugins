PLUGIN_NAME = 'Feat. Artists in Titles'
PLUGIN_AUTHOR = 'Lukas Lalinsky, Michael Wiencek, Bryan Toth, JeromyNix (NobahdiAtoll)'
PLUGIN_DESCRIPTION = 'Move "feat." from artist names to album and track titles. Match is case insensitive.'
PLUGIN_VERSION = "0.5"
PLUGIN_API_VERSIONS = ["0.9.0", "0.10", "0.15", "0.16", "2.0"]

from picard.metadata import register_album_metadata_processor, register_track_metadata_processor
import re

_feat_re = re.compile(r"([\s\S]+) feat\.([\s\S]+)", re.IGNORECASE)


def move_album_featartists(tagger, metadata, release):
    match = _feat_re.match(metadata["albumartist"])
    if match:
        metadata["albumartist"] = match.group(1)
        metadata["album"] += " (feat.%s)" % match.group(2)
    match = _feat_re.match(metadata["albumartistsort"])
    if match:
        metadata["albumartistsort"] = match.group(1)


def move_track_featartists(tagger, metadata, track, release):
    match = _feat_re.match(metadata["artist"])
    if match:
        metadata["artist"] = match.group(1)
        metadata["title"] += " (feat.%s)" % match.group(2)
    match = _feat_re.match(metadata["artistsort"])
    if match:
        metadata["artistsort"] = match.group(1)

register_album_metadata_processor(move_album_featartists)
register_track_metadata_processor(move_track_featartists)
