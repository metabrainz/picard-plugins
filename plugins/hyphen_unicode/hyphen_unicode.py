# -*- coding: utf-8 -*-

# Copyright (C) 2016 Anderson Mesquita <andersonvom@gmail.com>
# Copyright (C) 2019 Alan Swanson <reiver@improbability.net>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.

from picard import metadata

PLUGIN_NAME = "Hyphen unicode"
PLUGIN_AUTHOR = "Alan Swanson <revier@improbability.net>"
PLUGIN_VERSION = "1.0"
PLUGIN_API_VERSIONS = ["0.9", "0.10", "0.11", "0.15", "2.0"]
PLUGIN_LICENSE = "GPL-3.0-or-later"
PLUGIN_LICENSE_URL = "https://gnu.org/licenses/gpl.html"
PLUGIN_DESCRIPTION = '''Replaces unicode character HYPHEN (U+2010) [0xE2 0x80
0x90] with typographically identical HYPHEN-MINUS (U+002D) [0x2D] for fonts
that do not support HYPHEN and to prevent visually duplicate filenames
differentiated only by their hyphens.

Unicode duplicated hyphen from ASCII as an unambiguous way to designate a
hyphen from a minus whilst still being typographically indentical. Since 
text processing on music tags is rare so choice is purely pedantic esepcially
as keyboards only have HYPHEN-MINUS.

Replaces character on "album", "title", "artist", "artists", "artistsort",
"albumartist", "albumartists" and "albumartistsort" tags.'''

# Based on Non-ASCII Equivalents plugin.
# Musicbrainz form discussion on HYPHEN versus HYPHEN-MINUS at;
# https://community.metabrainz.org/t/correct-hyphen-unicode-hyphen-or-hyphen-minus/19610

CHAR_TABLE = {
    # HYPHEN to HYPHEN-MINUS
    "‐": "-",
}

FILTER_TAGS = [
    "title",
    "artist",
    "artists",
    "artistsort",
    "album",
    "albumsort",
    "albumartist",
    "albumartists",
    "albumartistsort",
]


def sanitize(char):
    if char in CHAR_TABLE:
        return CHAR_TABLE[char]
    return char


def ascii(word):
    return "".join(sanitize(char) for char in word)


def main(tagger, metadata, release, track=None):
    for name, value in metadata.rawitems():
        if name in FILTER_TAGS:
            metadata[name] = [ascii(x) for x in value]


metadata.register_track_metadata_processor(main)
metadata.register_album_metadata_processor(main)
