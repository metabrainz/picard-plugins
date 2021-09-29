# -*- coding: utf-8 -*-
#
# Copyright (C) 2018-2019, 2021 Philipp Wolfer
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
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

PLUGIN_NAME = 'Work & Movement'
PLUGIN_AUTHOR = 'Philipp Wolfer'
PLUGIN_DESCRIPTION = 'Set work and movement based on work relationships'
PLUGIN_VERSION = '1.0.2'
PLUGIN_API_VERSIONS = ['2.1', '2.2', '2.3', '2.4', '2.5', '2.6', '2.7']
PLUGIN_LICENSE = 'GPL-2.0-or-later'
PLUGIN_LICENSE_URL = 'https://www.gnu.org/licenses/gpl-2.0.html'


import re

from .roman import (
    fromRoman,
    RomanError,
)

from picard import log
from picard.metadata import register_track_metadata_processor


_re_work_title = re.compile(r'(?P<work>.*):\s+(?P<movementnumber>[IVXLCDM]+)\.\s+(?P<movement>.*)')
_re_part_number = re.compile(r'(?P<number>[0-9IVXLCDM]+)\.?\s+')


class Work:
    def __init__(self, title, mbid=None):
        self.mbid = mbid
        self.title = title
        self.is_movement = False
        self.is_work = False
        self.part_number = 0
        self.parent = None

    def __str__(self):
        s = []
        if self.parent:
            s.append(str(self.parent))
        if self.is_movement:
            work_type = 'Movement'
        elif self.is_work:
            work_type = 'Work'
        else:
            work_type = 'Unknown'
        s.append('%s %i: %s' % (work_type, self.part_number, self.title))
        return '\n'.join(s)


def is_performance_work(rel):
    return (rel['target-type'] == 'work'
            and rel['direction'] == 'forward'
            and rel['type'] == 'performance')


def is_parent_work(rel):
    return (rel['target-type'] == 'work'
            and rel['direction'] == 'backward'
            and rel['type'] == 'parts')


def is_movement_like(rel):
    return ('movement' in rel['attributes']
            or 'act' in rel['attributes']
            or 'ordering-key' in rel)


def is_child_work(rel):
    return (rel['target-type'] == 'work'
            and rel['direction'] == 'forward'
            and rel['type'] == 'parts')


def number_to_int(s):
    """
    Converts a numeric string to int. `s` can also be a Roman numeral.
    """
    try:
        return int(s)
    except ValueError:
        try:
            return fromRoman(s)
        except RomanError as e:
            raise ValueError(e)


def parse_work_name(title):
    return _re_work_title.search(title)


def create_work_and_movement_from_title(work):
    """
    Attempts to parse work.title in the form "<Work>: <Number>. <Movement>",
    where <Number> is in Roman numerals.
    Sets the `is_movement` and `part_number` properties on `work` and creates
    a `parent` work if not already present.
    """
    title = work.title
    match = parse_work_name(title)
    if match:
        work.title = match.group('movement')
        work.is_movement = True
        try:
            number = number_to_int(match.group('movementnumber'))
        except ValueError as e:
            log.error(e)
            number = 0
        if not work.part_number:
            work.part_number = number
        elif work.part_number != number:
            log.warning('Movement number mismatch for "%s": %s != %i',
                        title, match.group('movementnumber'), work.part_number)
        if not work.parent:
            work.parent = Work(match.group('work'))
            work.parent.is_work = True
        elif work.parent.title != match.group('work'):
            log.warning('Movement work name mismatch for "%s": "%s" != "%s"',
                        title, match.group('work'), work.parent.title)
    return work


def normalize_movement_title(work):
    """
    Removes the parent work title and part number from the beginning of
    `work.title`. This ensures movement names don't contain duplicated
    information even if they do not follow the strict naming format used by
    `create_work_and_movement_from_title`.
    """
    movement_title = work.title
    if work.parent:
        work_title = work.parent.title
        if movement_title.startswith(work_title):
            movement_title = movement_title[len(work_title):].lstrip(':').strip()
    match = _re_part_number.match(movement_title)
    if match:
        # Only remove the number if it matches the part_number
        try:
            number = number_to_int(match.group('number'))
            if number == work.part_number:
                movement_title = _re_part_number.sub("", movement_title)
        except ValueError as e:
            log.warning(e)
    return movement_title


def parse_work(work_rel):
    work = Work(work_rel['title'], work_rel['id'])
    if 'relations' in work_rel:
        for rel in work_rel['relations']:
            # If this work has parents and is linked to those as 'movement' or
            # 'act' we consider it a part of a larger work and store it
            # in the movement tag. The parent will be set as the work.
            if is_parent_work(rel):
                if is_movement_like(rel):
                    work.is_movement = True
                    work.part_number = rel.get('ordering-key')
                    if 'work' in rel:
                        work.parent = parse_work(rel['work'])
                        work.parent.is_work = True
                    work.title = normalize_movement_title(work)
                else:
                    # Not a movement, but still part of a larger work.
                    # Mark it as a work.
                    work.is_work = True
            # If this work has any parts, we consider it a proper work.
            # This is a recording directly linked to a larger work.
            if is_child_work(rel):
                work.is_work = True
    return work


def unset_work(metadata):
    metadata.delete('work')
    metadata.delete('musicbrainz_workid')
    metadata.delete('movement')
    metadata.delete('movementnumber')
    metadata.delete('movementtotal')
    metadata.delete('showmovement')


def set_work(metadata, work):
    metadata['work'] = work.title
    metadata['musicbrainz_workid'] = work.mbid
    metadata['showmovement'] = 1


def process_track(album, metadata, track, release):
    if 'recording' in track:
        recording = track['recording']
    else:
        recording = track

    if 'relations' not in recording:
        return

    work = Work(recording['title'])
    for rel in recording['relations']:
        if is_performance_work(rel):
            work = parse_work(rel['work'])
            # Only use the first work that qualifies as a work or movement
            log.debug('Found work:\n%s', work)
            if work.is_movement or work.is_work:
                break

    unset_work(metadata)
    if not work.is_movement:
        work = create_work_and_movement_from_title(work)

    if work.is_movement and work.parent and work.parent.is_work:
        metadata['movement'] = work.title
        if work.part_number:
            metadata['movementnumber'] = work.part_number
        set_work(metadata, work.parent)
    elif work.is_work:
        set_work(metadata, work)


register_track_metadata_processor(process_track)
