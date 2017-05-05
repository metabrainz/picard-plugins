PLUGIN_NAME = 'Release Type'
PLUGIN_AUTHOR = 'Elliot Chance'
PLUGIN_DESCRIPTION = 'Appends information to EPs and Singles'
PLUGIN_VERSION = '1.3'
PLUGIN_API_VERSIONS = ["0.9.0", "0.10", "0.15", "2.0"]

from picard.metadata import register_album_metadata_processor

RELEASE_TYPE_MAPPING = {
    "ep": " EP",
    "single": " (single)"
}


def add_release_type(tagger, metadata, release):

    # make sure "EP" (or "single", ...) is not already a word in the name
    words = metadata["album"].lower().split(" ")
    for word in ["ep", "e.p.", "single", "(single)"]:
        if word in words:
            return

    # check release type
    for releasetype, text in RELEASE_TYPE_MAPPING.iteritems():
        if (metadata["~primaryreleasetype"] == releasetype) or (
                metadata["releasetype"].startswith(releasetype)):
            rs = text
            break
    else:
        rs = ""

  # append title
    metadata["album"] = metadata["album"] + rs

register_album_metadata_processor(add_release_type)
