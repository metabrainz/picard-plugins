PLUGIN_NAME = 'Standardise Feat.'
PLUGIN_AUTHOR = 'Sambhav Kothari'
PLUGIN_DESCRIPTION = 'Standardises "featuring" join phrases for artists to "feat."'
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["1.4"]

import re
from picard import log
from picard.metadata import register_track_metadata_processor, register_album_metadata_processor
from picard.plugin import PluginPriority

_feat_re = re.compile(r" f(ea)?t(\.|uring)? ", re.IGNORECASE)


def standardise_feat(artists, artists_list):
    match_exp = r"(\s*.*\s*)".join((map(re.escape, artists_list)))
    try:
        join_phrases = re.match(match_exp, artists).groups()
    except AttributeError:
        log.debug("Unable to standardise artists: %r", artists)
        return artists
    else:
        standardised_join_phrases = [re.sub(_feat_re, " feat. ", phrase)
                                     for phrase in join_phrases]
        # Add a blank string at the end to allow zipping of
        # join phrases and artists_list since there is one less join phrase
        standardised_join_phrases.append("")
        return "".join([artist + join_phrase for artist, join_phrase in
                        zip(artists_list, standardised_join_phrases)])


def standardise_track_artist(tagger, metadata, release, track):
    metadata["artist"] = standardise_feat(metadata["artist"], metadata.getall("artists"))
    metadata["artistsort"] = standardise_feat(metadata["artistsort"], metadata.getall("~artists_sort"))


def standardise_album_artist(tagger, metadata, release):
    metadata["albumartist"] = standardise_feat(metadata["albumartist"], metadata.getall("albumartistsort"))
    metadata["~albumartists"] = standardise_feat(metadata["~albumartists"], metadata.getall("~albumartists_sort"))


register_track_metadata_processor(standardise_track_artist, priority=PluginPriority.HIGH)
register_album_metadata_processor(standardise_album_artist, priority=PluginPriority.HIGH)
