#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# This is the Abbreviate Artist plugin for MusicBrainz Picard.
# Copyright (C) 2013-2017 Sophist
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

PLUGIN_NAME = u"Abbreviate Artist-Sort v2"
PLUGIN_AUTHOR = u"Sophist"
PLUGIN_DESCRIPTION = u'''
Abbreviate Artist-Sort and Album-Artist-Sort Tags.
e.g. "Vivaldi, Antonio" becomes "Vivaldi A"
This is particularly useful for classical albums that can have a long list of artists.
This version of the plugin differs from version 1 as it modifies the relevant metadata
in place (rather than copying it into new variables.
'''
PLUGIN_VERSION = "1.0"
PLUGIN_API_VERSIONS = ["1.4"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

import re, unicodedata

artist_tags = [
    ('artistsort', '~artists_sort', '~unabbrev_artistsort', '~unabbrev_artists_sort'),
    ('albumartistsort', '~albumartists_sort', '~unabbrev_albumartistsort', '~unabbrev_albumartists_sort'),
    ]

def abbreviate_name(artist):
    if u"," not in artist:
        return artist
    surname, forenames = artist.split(u",", 1)
    return surname + u" " + "".join([x[0] for x in re.split(ur"\W+", forenames.strip())])

def string_cleanup(string, locale="utf-8"):
    if not string:
        return u""
    if not isinstance(string, unicode):
        string = string.decode(locale)
    # Replace with normalised unicode string
    return unicodedata.normalize("NFKC", string)

def abbreviate_artist(artist, locale="utf-8"):
    """Title-case a string using a less destructive method than str.title."""
    return abbreviate_name(string_cleanup(artist, locale))

assert "Bach JS" == abbreviate_artist("Bach, Johann Sebastian")
assert "The Beatles" == abbreviate_artist("The Beatles")

def abbreviate_artistsort(text, artists, abbrev_artists):
    """
    Use the array of artists and the joined string
    to identify artists to make title case
    and the join strings to leave as-is.
    """
    find = u"^(" + ur")(\s*\S+\s*)(".join((map(re.escape, map(string_cleanup,artists)))) + u")(.*$)"
    replace = "".join([ur"%s\%d" % (a, x*2 + 2) for x, a in enumerate(abbrev_artists)])
    result = re.sub(find, replace, string_cleanup(text), re.UNICODE)
    return result

assert "Bach JS; London Symphony Orchestra" == abbreviate_artistsort(
                                        "Bach, Johann Sebastian; London Symphony Orchestra",
                                        ["Bach, Johann Sebastian", "London Symphony Orchestra"],
                                        ["Bach JS", "London Symphony Orchestra"],
                                        )

# Put this here so that above unit tests can run standalone before getting an import error
from picard import log
from picard.metadata import (
    register_track_metadata_processor,
    register_album_metadata_processor,
)

def abbrev_artistsort_metadata(tagger, metadata, release, track=None):
    for artist_string, artists_list, original_artist, original_artists in artist_tags:
        if artist_string in metadata and artists_list in metadata:
            artists = metadata.getall(artists_list)
            artist = metadata.getall(artist_string)
            abbrev_artists = map(abbreviate_artist, artists)
            abbrev_artist = [abbreviate_artistsort(x, artists, abbrev_artists) for x in artist]
            if artists != abbrev_artists and artist != abbrev_artist:
                log.debug("AbbrevArtistSort2: Abbreviated %s from %r to %r", artists_list, artists, abbrev_artists)
                metadata[original_artists] = artists
                metadata[artists_list] = abbrev_artists
                log.debug("AbbrevArtistSort2: Abbreviated %s from %r to %r", artist_string, artist, abbrev_artist)
                metadata[original_artist] = artist
                metadata[artist_string] = abbrev_artist
            elif artists != abbrev_artists or artist != abbrev_artist:
                if artists != abbrev_artists:
                    log.warning("AbbrevArtistSort2: %s abbreviated, %s wasn't", artists_list, artist_string)
                else:
                    log.warning("AbbrevArtistSort2: %s abbreviated, %s wasn't", artist_string, artists_list)

register_track_metadata_processor(abbrev_artistsort_metadata)
register_album_metadata_processor(abbrev_artistsort_metadata)
