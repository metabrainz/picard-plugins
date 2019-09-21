# -*- coding: utf-8 -*-

# Re-converts '«' and '»' (plugin for MusicBrainz Picard)
# Copyright (C) 2019  Nero A.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


PLUGIN_NAME = "re-convert"
PLUGIN_AUTHOR = "Nero A."
PLUGIN_DESCRIPTION = '''Re-converts \'«\' and \'»\'.
The plugin is called "re-convert", because it's aim is to convert back characters/strings (to
Unicode), after the internal converting from Unicode punctuation characters to ASCII in Picard.'''
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["2.0", "2.1", "2.2"]
PLUGIN_LICENSE = "GPL-3.0-or-later"
PLUGIN_LICENSE_URL = "https://gnu.org/licenses/gpl.html"


# Converts characters/strings by other characters/string.
#
# The plugin is called "re-convert", because it's aim is to convert back characters/strings (to
# Unicode), after the internal converting from Unicode punctuation characters to ASCII in Picard.
# In concreto it will be used to re-convert "<<" (double less-than) and ">>" (double greater-than)
# to "«" and "»" (guillemets, see https://en.wikipedia.org/wiki/Guillemet).
# N.B. Currently only double guillemets will be re-converted but the plugin may be used for any
# characters/strings and might be extended in future.
# The converting will be done just straight forward, replace characters/strings by other
# characters/string, without any further logic. This means there might also be "wrong" re-converts.
#
# The internal Unicode punctuation to ASCII converting in Picard converts several characters,
# including double guillemets to double greater-than/less-than signs.
# Since I'd like to keep double guillemets I will convert them back with this plugin.
#
#
# See TAGS_ALBUM and TAGS_TRACK for affected metadata tags.


from picard.metadata import register_album_metadata_processor
from picard.metadata import register_track_metadata_processor


REPLACE_TABLE = {
    # Punctuation: (double) guillemets
    "<<": "«",
    ">>": "»",
}

TAGS_ALBUM = [
    "album",
    "albumartist",
    "albumartistsort",
    "discsubtitle",
    "originalalbum",
    "originalartist",
]

TAGS_TRACK = [
    "title",
    "artist",
    "artists",
    "artistsort",
]

    
def reconvert(value):
    result = value
    for key in REPLACE_TABLE:
        result = result.replace(key, REPLACE_TABLE[key])

    return result


def process_album(tagger, metadata, release):
    for name, value in metadata.rawitems():
        if name in TAGS_ALBUM:
            metadata[name] = [reconvert(v) for v in value]


def process_tracks(tagger, metadata, track, release):
    for name, value in metadata.rawitems():
        if name in TAGS_TRACK:
            metadata[name] = [reconvert(v) for v in value]


register_album_metadata_processor(process_album)
register_track_metadata_processor(process_tracks)
