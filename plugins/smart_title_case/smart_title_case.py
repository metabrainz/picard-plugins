#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Copyright 2007 Javier Kohen
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

PLUGIN_NAME = "Smart Title Case"
PLUGIN_AUTHOR = u"Sophist based on an earlier plugin by Javier Kohen"
PLUGIN_DESCRIPTION = """
Capitalize First Character In Every Word Of Album/Track Title/Artist.<br />
Leaves words containing embedded uppercase as-is i.e. USA or DoA.<br />
For Artist/AlbumArtist, title cases only artists not join phrases<br />
e.g. The Beatles feat. The Who.
"""
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["1.4.0"]
PLUGIN_LICENSE = "GPL-3.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-3.0.html"

import re, unicodedata
from picard import log
from picard.metadata import (
    register_track_metadata_processor,
    register_album_metadata_processor,
)

title_tags = ['title', 'album']
artist_tags = [
    ('artist', 'artists'),
    ('artistsort', '~artists_sort'),
    ('albumartist', '~albumartists'),
    ('albumartistsort', '~albumartists_sort'),
    ]
title_re = re.compile(r'\S+', re.UNICODE)

def match_word(match):
    word = match.group(0)
    if word == word.lower():
        word = word[0].upper() + word[1:]
    return word

def string_title_case(string, locale="utf-8"):
    """Title-case a string using a less destructive method than str.title."""
    if not string:
        return u""
    if not isinstance(string, unicode):
        string = string.decode(locale)
    # Replace with normalised unicode string
    string = unicodedata.normalize("NFKC", string)
    return title_re.sub(match_word, string)

assert "Make Title" == string_title_case("make title")
assert "mAkE tItLe" == string_title_case("mAkE tItLe")
assert "Make's Title's" == string_title_case("make's title's")

def match_phrase(match):
    phrase = match.group(0)
    return string_title_case(phrase)

def artist_title_case(text, artists):
    """
    Use the array of artists and the joined string
    to identify artists to make title case
    and the join strings to leave as-is.
    """
    find = u"^(" + ur")(\s+\S+?\s+)(".join((map(re.escape, artists))) + u")(.*$)"
    replace = "".join([ur"%s\%d" % (string_title_case(a), x*2 + 2) for x, a in enumerate(artists)])
    result = re.sub(find, replace, text, re.UNICODE)
    log.debug("SmartTitleCase: %r replaced with %r", text, result)
    return

assert "The Beatles feat. The Who" == artist_title_case("the beatles feat. the who", ["the beatles", "the who"])

def title_case(tagger, metadata, release, track=None):
    for name in title_tags:
        if name in metadata:
            values = metadata.getall(name)
            metadata[name] = [string_title_case(v) for v in values]
    for artist_string, artists_list in artist_tags:
        if artist_string in metadata and artists_list in metadata:
            values = metadata.getall(artist_string)
            artists = metadata.getall(artists_list)
            metadata[artist_string] = [artist_title_case(x, artists) for x in values]

register_track_metadata_processor(title_case)
register_album_metadata_processor(title_case)
