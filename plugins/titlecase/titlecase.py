# -*- coding: utf-8 -*-
# Copyright 2007 Javier Kohen
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

PLUGIN_NAME = "Title Case"
PLUGIN_AUTHOR = "Javier Kohen, Sambhav Kothari"
PLUGIN_DESCRIPTION = "Capitalize First Character In Every Word Of A Title"
PLUGIN_VERSION = "1.0.2"
PLUGIN_API_VERSIONS = ['2.0']
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

import unicodedata
from picard.plugin import PluginPriority


def iswbound(char):
    """Returns whether the given character is a word boundary."""
    category = unicodedata.category(char)
    # If it's a space separator or punctuation
    return 'Zs' == category or 'Sk' == category or 'P' == category[0]


def utitle(string):
    """Title-case a string using a less destructive method than str.title."""
    new_string = string[0].capitalize()
    cap = False
    for i in range(1, len(string)):
        s = string[i]
        # Special case apostrophe in the middle of a word.
        if s in "’'" and string[i - 1].isalpha():
            cap = False
        elif iswbound(s):
            cap = True
        elif cap and s.isalpha():
            cap = False
            s = s.capitalize()
        else:
            cap = False
        new_string += s
    return new_string


def title(string):
    """Title-case a string using a less destructive method than str.title."""
    if not string:
        return ""
    # if the string is all uppercase, lowercase it - Erich/Javier
    #   Lots of Japanese songs use entirely upper-case English titles,
    #   so I don't like this change... - JoeW
    #if string == string.upper(): string = string.lower()
    return utitle(string_(string))

from picard.metadata import (
    register_track_metadata_processor,
    register_album_metadata_processor,
)


def title_case(tagger, metadata, *args):
    for name, value in metadata.rawitems():
        if name in ["title", "album", "artist"]:
            metadata[name] = [title(x) for x in value]

register_track_metadata_processor(title_case, priority=PluginPriority.LOW)
register_album_metadata_processor(title_case, priority=PluginPriority.LOW)
