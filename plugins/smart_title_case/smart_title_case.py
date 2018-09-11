#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This is the Smart Title Case plugin for MusicBrainz Picard.
# Copyright (C) 2017 Sophist.
#
# Updated for use with Picard v2.0 by Bob Swift (rdswift).
#
# It is based on the Title Case plugin by Javier Kohen
# Copyright 2007 Javier Kohen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

PLUGIN_NAME = "Smart Title Case"
PLUGIN_AUTHOR = "Sophist based on an earlier plugin by Javier Kohen"
PLUGIN_DESCRIPTION = """
Capitalize First Character In Every Word Of Album/Track Title/Artist.<br />
Leaves words containing embedded uppercase as-is i.e. USA or DoA.<br />
For Artist/AlbumArtist, title cases only artists not join phrases<br />
e.g. The Beatles feat. The Who.
"""
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-3.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-3.0.html"

import re, unicodedata

title_tags = ['title', 'album']
artist_tags = [
    ('artist', 'artists'),
    ('artistsort', '~artists_sort'),
    ('albumartist', '~albumartists'),
    ('albumartistsort', '~albumartists_sort'),
    ]
title_re = re.compile(r'\w[^-,/\s\u2010\u2011]*')

def match_word(match):
    word = match.group(0)
    if word == word.lower():
        word = word[0].upper() + word[1:]
    return word

def string_title_match(match_word, string):
    return title_re.sub(match_word, string)

def string_cleanup(string):
    if not string:
        return ""
    return unicodedata.normalize("NFKC", string)

def string_title_case(string):
    """Title-case a string using a less destructive method than str.title."""
    return string_title_match(match_word, string_cleanup(string))


assert "Make Title Case" == string_title_case("make title case")
assert "Already Title Case" == string_title_case("Already Title Case")
assert "mIxEd cAsE" == string_title_case("mIxEd cAsE")
assert "A" == string_title_case("a")
assert "Apostrophe's Apostrophe's" == string_title_case("apostrophe's apostrophe's")
assert "(Bracketed Text)" == string_title_case("(bracketed text)")
assert "'Single Quotes'" == string_title_case("'single quotes'")
assert '"Double Quotes"' == string_title_case('"double quotes"')
assert "A,B" == string_title_case("a,b")
assert "A-B" == string_title_case("a-b")
assert "A/B" == string_title_case("a/b")
assert "Flügel" == string_title_case("flügel")
assert "HARVEST STORY By 杉山清貴" == string_title_case("HARVEST STORY by 杉山清貴")


def artist_title_case(text, artists, artists_upper):
    """
    Use the array of artists and the joined string
    to identify artists to make title case
    and the join strings to leave as-is.
    """
    find = "^(" + r")(\s+\S+?\s+)(".join((map(re.escape, map(string_cleanup,artists)))) + ")(.*$)"
    replace = "".join([r"%s\%d" % (a, x*2 + 2) for x, a in enumerate(artists_upper)])
    result = re.sub(find, replace, string_cleanup(text), re.UNICODE)
    return result

assert "The Beatles feat. The Who" == artist_title_case(
                                        "the beatles feat. the who",
                                        ["the beatles", "the who"],
                                        ["The Beatles", "The Who"]
                                        )


# Put this here so that above unit tests can run standalone before getting an import error
from picard import log
from picard.metadata import (
    register_track_metadata_processor,
    register_album_metadata_processor,
)

def title_case(tagger, metadata, release, track=None):
    for name in title_tags:
        if name in metadata:
            values = metadata.getall(name)
            new_values = [string_title_case(v) for v in values]
            if values != new_values:
                log.debug("SmartTitleCase: %s: %r replaced with %r", name, values, new_values)
                metadata[name] = new_values
    for artist_string, artists_list in artist_tags:
        if artist_string in metadata and artists_list in metadata:
            artist = metadata.getall(artist_string)
            artists = metadata.getall(artists_list)
            new_artists = map(string_title_case, artists)
            new_artist = [artist_title_case(x, artists, new_artists) for x in artist]
            if artists != new_artists and artist != new_artist:
                log.debug("SmartTitleCase: %s: %s replaced with %s", artist_string, artist, new_artist)
                log.debug("SmartTitleCase: %s: %r replaced with %r", artists_list, artists, new_artists)
                metadata[artist_string] = new_artist
                metadata[artists_list] = new_artists
            elif artists != new_artists or artist != new_artist:
                if artists != new_artists:
                    log.warning("SmartTitleCase: %s changed, %s wasn't", artists_list, artist_string)
                    log.warning("SmartTitleCase: %s: %r changed to %r", artists_list, artists, new_artists)
                    log.warning("SmartTitleCase: %s: %r unchanged", artist_string, artist)
                else:
                    log.warning("SmartTitleCase: %s changed, %s wasn't", artist_string, artists_list)
                    log.warning("SmartTitleCase: %s: %r changed to %r", artist_string, artist, new_artist)
                    log.warning("SmartTitleCase: %s: %r unchanged", artists_list, artists)

register_track_metadata_processor(title_case)
register_album_metadata_processor(title_case)
