# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Philipp Wolfer
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

PLUGIN_NAME = 'Haiku BFS Attributes'
PLUGIN_AUTHOR = 'Philipp Wolfer'
PLUGIN_DESCRIPTION = 'Save metadata to Haiku BFS attributes.'
PLUGIN_VERSION = "1.0.0"
PLUGIN_API_VERSIONS = ["2.2"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"


from functools import partial
import subprocess
import sys

from picard.file import register_file_post_save_processor
from picard import log
from picard.util import thread


if not sys.platform == 'haiku1':
    log.warning('haikuattrs: this plugin is only for the Haiku operating system')
else:
    attr_map = {
        'artist'     : ('string', 'Audio:Artist'),
        'album'      : ('string', 'Audio:Album'),
        'title'      : ('string', 'Media:Title'),
        'date'       : ('int32' , 'Media:Year'),
        'comment:'   : ('string', 'Media:Comment'),
        'tracknumber': ('int32' , 'Audio:Track'),
        'genre'      : ('string', 'Media:Genre'),
        'composer'   : ('string', 'Audio:Composer'),
        '~rating'    : ('int32' , 'Media:Rating'),
    }


    def set_attr(path, attr_name, attr_value, type='string'):
        try:
            subprocess.check_call(['rmattr', attr_name, path])
            subprocess.check_call(['addattr', '-t', type, attr_name,
                                   attr_value, path])
        except subprocess.CalledProcessError:
            log.error('haikuattrs: setting %s=%s for %s failed' % (attr_name,
                attr_value, path), exc_info=True)


    def set_attrs_from_metadata(file):
        log.debug('haikuattrs: setting attributes for %s' % file.filename)
        for tag, attr in attr_map.items():
            value = file.orig_metadata[tag]
            if value:
                if tag == 'date':
                    value = value[:4]
                elif tag == '~rating':
                    try:
                        value = str(int(value) * 2)
                    except ValueError:
                        continue
                set_attr(file.filename, attr[1], value, type=attr[0])


    def set_attrs_from_metadata_finished(file, result):
        log.debug('haikuattrs: attributes set for %s' % file.filename)


    def set_bfs_attributes_processor(file):
        thread.run_task(
            partial(set_attrs_from_metadata, file),
            partial(set_attrs_from_metadata_finished, file))


    register_file_post_save_processor(set_bfs_attributes_processor)
