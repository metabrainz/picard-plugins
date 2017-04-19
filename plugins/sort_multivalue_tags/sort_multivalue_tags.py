# -*- coding: utf-8 -*-

# This is the Sort Multivalue Tags plugin for MusicBrainz Picard.
# Copyright (C) 2013 Sophist
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

PLUGIN_NAME = "Sort Multi-Value Tags"
PLUGIN_AUTHOR = "Sophist"
PLUGIN_DESCRIPTION = '''
This plugin sorts multi-value tags e.g. Performers alphabetically.<br /><br />
Note: Some multi-value tags are excluded for the following reasons:
<ol>
<li>Sequence is important e.g. Artists</li>
<li>The sequence of one tag is linked to the sequence of another e.g. Label and Catalogue number.</li>
</ol>
'''
PLUGIN_VERSION = "0.2"
PLUGIN_API_VERSIONS = ["0.15"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard.metadata import register_track_metadata_processor

# Define tags where sort order is important
_sort_multivalue_tags_exclude = (
    'artists', '~artists_sort', 'musicbrainz_artistid',
    'albumartists', '~albumartists_sort', 'musicbrainz_albumartistid',
    'work', 'musicbrainz_workid',
    'label', 'catalognumber',
    'country', 'date',
    'releasetype',
)
# Possible future enhancement:
# Sort linked tags e.g. work so that the sequence in related tags e.g. workid retains the relationship between
# e.g. work and workid.


def sort_multivalue_tags(tagger, metadata, track, release):

    for tag in metadata.keys():
        if tag in _sort_multivalue_tags_exclude:
            continue
        data = metadata.getall(tag)
        if len(data) > 1:
            sorted_data = sorted(data)
            if data != sorted_data:
                metadata.set(tag, sorted_data)

register_track_metadata_processor(sort_multivalue_tags)
