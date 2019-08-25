# -*- coding: utf-8 -*-

# Copyright (C) 2019 Alex Rustler <alex_rustler@rambler.ru>
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

PLUGIN_NAME = "Replace Forbidden Symbols"
PLUGIN_AUTHOR = "Alex Rustler <alex_rustler@rambler.ru>"
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["0.9", "0.10", "0.11", "0.15", "2.0", "2.2"]
PLUGIN_LICENSE = "GPL-3.0-or-later"
PLUGIN_LICENSE_URL = "https://gnu.org/licenses/gpl.html"
PLUGIN_DESCRIPTION = '''Replaces Windows forbidden symbols: :, /, *, ?, ", ., | etc.
                    with a similar UNICODE version.
                    Currently replaces characters on "album", "artist",
                    "title", "albumartist", "releasetype", "label" tags.'''

CHAR_TABLE = {

    # forbidden
    ":": "∶",
    "/": "⁄",
    "*": "∗",
    "?": "？",
    '"': '″',
    '\\': '⧵',
    '.': '․',
    '|': 'ǀ',
    '<': '‹',
    '>': '›'
}

FILTER_TAGS = [
    "album",
    "artist",
    "title",
    "albumartist",
    "releasetype",
    "label",
]


def sanitize(char):
    if char in CHAR_TABLE:
        return CHAR_TABLE[char]
    return char


def fix_forbidden(word):
    return "".join(sanitize(char) for char in word)


def replace_forbidden(value):
    return [fix_forbidden(x) for x in value]


def main(tagger, metadata, release, track=None):
    for name, value in metadata.rawitems():
        if name in FILTER_TAGS:
            metadata[name] = replace_forbidden(value)


metadata.register_track_metadata_processor(main)
metadata.register_album_metadata_processor(main)
