# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Bob Swift (rdswift)
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

PLUGIN_NAME = 'Data Dumper'
PLUGIN_AUTHOR = 'Bob Swift (rdswift)'
PLUGIN_DESCRIPTION = '''
This plugin saves the output for the track and release metadata
to a text file.  By default, the file is called 'data_dump.txt'
and is saved in the file naming destination directory.
<br /><br />
This can be used to help develop release and track plugins by
providing a log of the information passed to the plugin.
'''

PLUGIN_VERSION = "0.2"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0 or later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

OFILE = "data_dump.txt"

import json
import os

from picard import config, log
from picard.metadata import (register_album_metadata_processor,
                             register_track_metadata_processor)
from picard.plugin import PluginPriority

file_to_write = config.setting["move_files_to"] + os.path.sep + OFILE


def write_line(line_type, object_to_write, dump_json=False):
    try:
        with open(file_to_write, "a", encoding="UTF-8") as f:
            if dump_json:
                f.write('{0} JSON dump follows:\n'.format(line_type,))
                f.write('{0}\n\n'.format(json.dumps(object_to_write, indent=4)))
            else:
                f.write("{0:s}: {1:s}\n".format(line_type, str(object_to_write),))
    except Exception as ex:
        log.error("{0}: Error: {1}".format(PLUGIN_NAME, ex,))


def dump_release_info(album, metadata, release):
    write_line('Release Argument 1 (album)', album)
    write_line('Release Argument 3 (release)', release, dump_json=True)


def dump_track_info(album, metadata, track, release):
    write_line('Track Argument 1 (album)', album)
    write_line('Track Argument 3 (track)', track, dump_json=True)
    # write_line('Track Argument 4 (release)', release, dump_json=True)


# Register the plugin to run at a HIGH priority so that other plugins will
# not have an opportunity to modify the contents of the metadata provided.
register_album_metadata_processor(dump_release_info, priority=PluginPriority.HIGH)
register_track_metadata_processor(dump_track_info, priority=PluginPriority.HIGH)
