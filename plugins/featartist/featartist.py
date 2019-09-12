PLUGIN_NAME = 'Feat. Artists Removed'
PLUGIN_AUTHOR = 'Lukas Lalinsky, Bryan Toth'
PLUGIN_DESCRIPTION = 'Removes feat. artists from track titles.  Substitution is case insensitive.'
PLUGIN_VERSION = "0.4"
PLUGIN_API_VERSIONS = ["0.9.0", "0.10", "0.15", "0.16", "2.0"]

from picard.metadata import register_track_metadata_processor
import re

_feat_re = re.compile(r"\s+\(feat\. [^)]*\)", re.IGNORECASE)


def remove_featartists(tagger, metadata, track, release):
    metadata["title"] = _feat_re.sub("", metadata["title"])

register_track_metadata_processor(remove_featartists)
