# -*- coding: utf-8 -*-

# Copyright (C) 2016 Anderson Mesquita <andersonvom@gmail.com>
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

PLUGIN_NAME = "Non-ASCII Equivalents"
PLUGIN_AUTHOR = "Anderson Mesquita <andersonvom@trysometinghere>"
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["0.9", "0.10", "0.11", "0.15"]
PLUGIN_LICENSE = "GPLv3"
PLUGIN_LICENSE_URL = "https://gnu.org/licenses/gpl.html"
PLUGIN_DESCRIPTION = '''Replaces accented and otherwise non-ASCII characters
with a somewhat equivalent version of their ASCII counterparts. This allows old
devices to be able to display song artists and titles somewhat correctly,
instead of displaying weird or blank symbols. It's an attempt to do a little
better than Musicbrainz's native "Replace non-ASCII characters" option.'''

CHAR_TABLE = {
    # Acute     # Grave     # Umlaut    # Circumflex
    u"Á": "A",  u"À": "A",  u"Ä": "A",  u"Â": "A",
    u"É": "E",  u"È": "E",  u"Ë": "E",  u"Ê": "E",
    u"Í": "I",  u"Ì": "I",  u"Ï": "I",  u"Î": "I",
    u"Ó": "O",  u"Ò": "O",  u"Ö": "O",  u"Ô": "O",
    u"Ú": "U",  u"Ù": "U",  u"Ü": "U",  u"Û": "U",
    u"Ý": "Y",  u"Ỳ": "Y",  u"Ÿ": "Y",  u"Ŷ": "Y",
    u"á": "a",  u"à": "a",  u"ä": "a",  u"â": "a",
    u"é": "e",  u"è": "e",  u"ë": "e",  u"ê": "e",
    u"í": "i",  u"ì": "i",  u"ï": "i",  u"î": "i",
    u"ó": "o",  u"ò": "o",  u"ö": "o",  u"ô": "o",
    u"ú": "u",  u"ù": "u",  u"ü": "u",  u"û": "u",
    u"ý": "y",  u"ỳ": "y",  u"ÿ": "y",  u"ŷ": "y",

    # Misc Letters
    u"Å": "AA",
    u"å": "aa",
    u"Æ": "AE",
    u"æ": "ae",
    u"Œ": "OE",
    u"œ": "oe",
    u"ẞ": "ss",
    u"ß": "ss",
    u"Ç": "C",
    u"ç": "c",
    u"Ñ": "N",
    u"ñ": "n",
    u"Ø": "O",
    u"ø": "o",

    # Punctuation
    u"¡": "!",
    u"¿": "?",
    u"–": "--",
    u"—": "--",
    u"―": "--",
    u"«": "<<",
    u"»": ">>",
    u"‘": "'",
    u"’": "'",
    u"‚": ",",
    u"‛": "'",
    u"“": '"',
    u"”": '"',
    u"„": ",,",
    u"‟": '"',
    u"‹": "<",
    u"›": ">",
    u"⹂": ",,",
    u"「": "|-",
    u"」": "-|",
    u"『": "|-",
    u"』": "-|",
    u"〝": '"',
    u"〞": '"',
    u"〟": ",,",
    u"﹁": "-|",
    u"﹂": "|-",
    u"﹃": "-|",
    u"﹄": "|-",
    u"＂": '"',
    u"＇": "'",
    u"｢": "|-",
    u"｣": "-|",

    # Mathematics
    u"≠": "!=",
    u"≤": "<=",
    u"≥": ">=",
    u"±": "+-",
    u"∓": "-+",
    u"×": "x",
    u"·": ".",
    u"÷": "/",
    u"√": "\/",
    u"∑": "E",
    u"≪": "<<", # these are different
    u"≫": ">>", # from the quotation marks

    # Misc
    u"ª": "a",
    u"º": "o",
    u"°": "o",
    u"µ": "u",
    u"ı": "i",
    u"†": "t",
    u"©": "(c)",
    u"®": "(R)",
    u"℠": "(SM)",
    u"™": "(TM)",
}

FILTER_TAGS = [
    "album",
    "artist",
    "title",
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
