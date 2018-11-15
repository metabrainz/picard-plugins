# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Philipp Wolfer
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
PLUGIN_VERSION = '1.0'
PLUGIN_API_VERSIONS = ['2.1']
PLUGIN_LICENSE = 'GPL-2.0-or-later'
PLUGIN_LICENSE_URL = 'https://www.gnu.org/licenses/gpl-2.0.html'


import re

from .roman import fromRoman, RomanError

from picard import log
from picard.metadata import register_track_metadata_processor


class Work:
    def __init__(self, title, id=None):
        self.id = id
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
            type = 'Movement'
        elif self.is_work:
            type = 'Work'
        else:
            type = 'Unknown'
        s.append('%s %i: %s' % (type, self.part_number, self.title))
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


_re_work_title = re.compile(r'(?P<work>.*):\s+(?P<movementnumber>[IVXLCDM]+)\.\s+(?P<movement>.*)')
def parse_work_name(title):
    return _re_work_title.search(title)


def normalize_movement_name(work):
    """
    Attempts to parse work.title in the form "<Work>: <Number>. <Movement>",
    where <Number> is in Roman numerals.
    Sets the `is_movement` and `part_number` properties on `work` and creates
    a `parent` work if not already present.
    """
    title = work.title
    m = parse_work_name(title)
    if m:
        work.title = m.group('movement')
        work.is_movement = True
        try:
            number = fromRoman(m.group('movementnumber'))
        except RomanError as e:
            log.error(e)
            number = 0
        if not work.part_number:
            work.part_number = number
        elif work.part_number != number:
            log.warn('Movement number mismatch for "%s": %s != %i' % (
                     title, m.group('movementnumber'), work.part_number))
        if not work.parent:
            work.parent = Work(m.group('work'))
            work.parent.is_work = True
        elif work.parent.title != m.group('work'):
            log.warn('Movement work name mismatch for "%s": "%s" != "%s"' % (
                     title, m.group('work'), work.parent.title))
    return work


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
                    work.part_number = rel['ordering-key']
                    if 'work' in rel:
                        work.parent = parse_work(rel['work'])
                        work.parent.is_work = True
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
    metadata.set('work', '')
    metadata.set('musicbrainz_workid', '')
    metadata.set('movement', '')
    metadata.set('movementnumber', '')
    metadata.set('movementtotal', '')
    metadata.set('showmovement', '')


def set_work(metadata, work):
    metadata['work'] = work.title
    metadata['musicbrainz_workid'] = work.id
    metadata['showmovement'] = 1


def process_track(album, metadata, track, release):
    if 'recording' in track:
        recording = track['recording']
    else:
        recording = track

    if not 'relations' in recording:
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
    work = normalize_movement_name(work)

    if work.is_movement and work.parent and work.parent.is_work:
        movement = work.title
        metadata['movement'] = movement
        if work.part_number:
            metadata['movementnumber'] = work.part_number
        set_work(metadata, work.parent)
    elif work.is_work:
        set_work(metadata, work)


register_track_metadata_processor(process_track)
