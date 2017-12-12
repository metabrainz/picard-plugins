#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Fix Track Numbers plugin for MusicBrainz Picard
# Copyright (C) 2017 Jonathan Bradley Whited
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

PLUGIN_NAME = 'Fix Track Numbers'
PLUGIN_AUTHOR = 'Jonathan Bradley Whited'
PLUGIN_DESCRIPTION = '''
Fix the track numbers in a cluster by either using the track titles (1) or sequential order (2).

<ol>
  <li>
    The title should contain something like "#-#" (number dash number) and be unique.<br />
    All non-numbers and non-dashes will be removed when comparing the titles.<br />
    This is especially useful for Language Audio Lessons, like this:
    <pre>- Title: "Unit 1 - Lesson 10"</pre>
    For example, take the following titles and track numbers:
    <pre>- Title: "Unit 1 - Lesson 1"  - Track #1</pre>
    <pre>- Title: "Unit 1 - Lesson 2"  - Track #1</pre>
    <pre>- Title: "Unit 2 - Lesson 10" - Track #2</pre>
    <pre>- Title: "Unit 2 - Lesson 1"  - Track #2</pre>
    The track numbers will be changed to:  1, 2, 4, 3<br />
    The 3rd one will be changed to Track #4 because Lesson 1 &lt; Lesson 10.<br />
    The titles will remain unchanged.
  </li>

  <li>The track numbers will be set based on the sequential order they appear within the cluster.</li>
</ol>

How to use:
<ol>
  <li>Cluster a group of files</li>
  <li>Right click on the cluster</li>
  <li>
    Then click one:
    <ul>
      <li>Plugins => Fix track numbers using titles</li>
      <li>Plugins => Fix track numbers using sequence</li>
    </ul>
  </li>
</ol>
'''
PLUGIN_VERSION = '0.1'
PLUGIN_API_VERSIONS = ['0.15', '1.0', '2.0']
PLUGIN_LICENSE = 'GPL-3.0'
PLUGIN_LICENSE_URL = 'https://www.gnu.org/licenses/gpl.txt'

from picard import log
from picard.cluster import Cluster
from picard.ui.itemviews import BaseAction, register_cluster_action

import re

# FIXME: for Python 3.0 and Picard 2.0, use String.format(...) instead of %?


class FixedTrack:

    def __init__(self, tracknumber=0, title=None, title_num1=0, title_num2=0):
        self.title = title
        self.title_num1 = title_num1
        self.title_num2 = title_num2
        self.tracknumber = tracknumber


class FixTrackNumsUsingTitles(BaseAction):
    NAME = 'Fix track numbers using titles'
    TITLE_REGEX = re.compile(r"[^\d\-]+")  # Only digits and '-' allowed

    def callback(self, objs):
        log.debug('[FixTrackNumsUsingTitles]')

        for cluster in objs:
            if not isinstance(cluster, Cluster) or not cluster.files:
                continue

            tracks = []  # Sorted list of FixedTrack

            for i, f in enumerate(cluster.files):
                if not f or not f.metadata or 'title' not in f.metadata:
                    log.debug('No file/metadata/title for [%i]' % (i))
                    continue

                track = FixedTrack(i + 1, f.metadata['title'])

                if not track.title:
                    log.debug('No title for [%i]' % (i))
                    continue

                title_nums = self.TITLE_REGEX.sub('', track.title)
                dash_index = title_nums.find('-')

                if dash_index < 0:
                    log.debug('No dash in [%i][%s]' % (i, title_nums))
                    continue

                try:
                    track.title_num1 = int(title_nums[:dash_index])
                    track.title_num2 = int(title_nums[dash_index + 1:])
                except ValueError:
                    log.debug('Invalid ints in [%i][%s]' % (i, title_nums))
                    continue

                was_added = False

                # Not empty?
                if tracks:
                    # Justin Timberlake?
                    for j, t in enumerate(tracks):
                        if was_added:
                            # Increment all track numbers above last added one
                            t.tracknumber += 1
                        # Don't do "<=" on title_num2 to preserve sequence
                        # - Case 1: "2-10" < "3-1"
                        # - Case 2: "2-1"  < "2-10"
                        elif ((track.title_num1 < t.title_num1) or
                              (track.title_num1 == t.title_num1 and
                               track.title_num2 < t.title_num2)):
                            # t.tracknumber will be updated in next loop cycle
                            track.tracknumber = t.tracknumber
                            tracks.insert(j, track)
                            was_added = True  # Don't break

                if not was_added:
                    tracks.append(track)

            # Let's build a dictionary of the new (fixed) track numbers
            new_tracks = {}

            for i, t in enumerate(tracks):
                # Assume title is unique
                new_tracks[t.title] = str(t.tracknumber)

            for i, f in enumerate(cluster.files):
                if not f or not f.metadata or 'title' not in f.metadata:
                    # Already logged
                    continue

                key = f.metadata['title']

                if not key:
                    # Already logged
                    continue
                if key not in new_tracks:
                    log.debug('No new track for [%i][%s]' % (i, key))
                    continue

                new_track = new_tracks[key]

                log.debug('Change [%s]=>[%s]' % (key, new_track))

                f.metadata['tracknumber'] = new_track
                f.metadata.changed = True
                f.update(signal=True)

            cluster.update()


class FixTrackNumsUsingSeq(BaseAction):
    NAME = 'Fix track numbers using sequence'

    def callback(self, objs):
        log.debug('[FixTrackNumsUsingSeq]')

        for cluster in objs:
            if not isinstance(cluster, Cluster) or not cluster.files:
                continue

            for i, f in enumerate(cluster.files):
                if not f or not f.metadata:
                    log.debug('No file/metadata for [%i]' % (i))
                    continue

                new_track = str(i + 1)

                if 'title' in f.metadata and f.metadata['title']:
                    log.debug('Change [%s]=>[%s]' %
                              (f.metadata['title'], new_track))

                f.metadata['tracknumber'] = new_track
                f.metadata.changed = True
                f.update(signal=True)

            cluster.update()

register_cluster_action(FixTrackNumsUsingTitles())
register_cluster_action(FixTrackNumsUsingSeq())
