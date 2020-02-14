PLUGIN_NAME = 'Standardise Feat.'
PLUGIN_AUTHOR = 'Sambhav Kothari'
PLUGIN_DESCRIPTION = 'Standardises "featuring" join phrases for artists to "feat."'
PLUGIN_VERSION = "0.3"
PLUGIN_API_VERSIONS = ["1.4", "2.0", "2.1", "2.2", "2.3"]
PLUGIN_LICENSE = "GPL-3.0"
PLUGIN_LICENSE_URL = "http://www.gnu.org/licenses/gpl-3.0.txt"

import re
from picard import log
from picard.metadata import register_track_metadata_processor, register_album_metadata_processor
from picard.plugin import PluginPriority

_feat_re = re.compile(r" f(ea)?t(\.|uring)? ", re.IGNORECASE)


def standardise_feat(artists_str, artists_list):
    """
    >>> standardise_feat("The A", ["The A"])
    'The A'
    >>> standardise_feat("The A ft. B", ["The A", "B"])
    'The A feat. B'
    >>> standardise_feat("The A & B featuring C", ["The A", "B", "C"])
    'The A & B feat. C'
    >>> standardise_feat("The A featuring B (and C)", ["The A", "B", "C"])
    'The A feat. B (and C)'
    """
    match_exp = r"(\s*.*\s*)".join((map(re.escape, artists_list))) + r"(\s*.*$)"
    try:
        join_phrases = re.match(match_exp, artists_str).groups()
    except AttributeError:
        log.debug("Unable to standardise artists: %r", artists_str)
        return artists_str
    else:
        standardised_join_phrases = [_feat_re.sub(" feat. ", phrase)
                                     for phrase in join_phrases]
        # Add a blank string at the end to allow zipping of
        # join phrases and artists_list since there is one less join phrase
        standardised_join_phrases.append("")
        return "".join([artist + join_phrase for artist, join_phrase in
                        zip(artists_list, standardised_join_phrases)])


def standardise_track_artist(tagger, metadata, track, release):
    metadata["artist"] = standardise_feat(metadata["artist"], metadata.getall("artists"))
    metadata["artistsort"] = standardise_feat(metadata["artistsort"], metadata.getall("~artists_sort"))


def standardise_album_artist(tagger, metadata, release):
    metadata["albumartist"] = standardise_feat(metadata["albumartist"], metadata.getall("~albumartists"))
    metadata["albumartistsort"] = standardise_feat(metadata["albumartistsort"], metadata.getall("~albumartists_sort"))


register_track_metadata_processor(standardise_track_artist, priority=PluginPriority.HIGH)
register_album_metadata_processor(standardise_album_artist, priority=PluginPriority.HIGH)
