# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, 2021 Philipp Wolfer
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
PLUGIN_DESCRIPTION = 'Save and load metadata to/from Haiku BFS attributes.'
PLUGIN_VERSION = "1.2"
PLUGIN_API_VERSIONS = ["2.2", "2.3", "2.4", "2.5", "2.6"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"


import os
import struct
import sys
from collections import namedtuple
from ctypes import (CDLL, POINTER, Structure, byref, c_char_p, c_int, c_long,
                    c_longlong, c_size_t, c_ssize_t, c_uint32, c_void_p, cast)
from ctypes.util import find_library
from functools import partial

from picard import log
from picard.file import (
    register_file_post_load_processor,
    register_file_post_save_processor,
    )
from picard.util import thread

if sys.platform == 'haiku1':

    class AttrInfo(Structure):
        _fields_ = [
            ('type', c_uint32),
            ('size', c_size_t)]

        def __repr__(self):
            return 'AttrInfo(type=%r, size=%r)' % (self.type, self.size)

    try:
        libbe_path = find_library('be') or 'libbe.so'
        be = CDLL(libbe_path, use_errno=True)
        be.fs_stat_attr.restype = c_int
        be.fs_stat_attr.argtypes = [c_int, c_char_p, POINTER(AttrInfo)]
        be.fs_read_attr.restype = c_ssize_t
        be.fs_read_attr.argtypes = [c_int, c_char_p, c_uint32, c_size_t,
                                    c_void_p, c_size_t]
        be.fs_remove_attr.restype = c_int
        be.fs_remove_attr.argtypes = [c_int, c_char_p]
        be.fs_write_attr.restype = c_ssize_t
        be.fs_write_attr.argtypes = [c_int, c_char_p, c_uint32, c_size_t,
                                     c_void_p, c_size_t]
    except OSError:
        log.error('haikuattrs: unable to load libbe', exc_info=True)
        be = None
else:
    log.warning('haikuattrs: this plugin is only for the Haiku operating system')
    be = None

if be:
    Attr = namedtuple('Attr', ['type', 'name'])
    attr_map = {
        'artist'     : Attr(b'CSTR', b'Audio:Artist'),
        'album'      : Attr(b'CSTR', b'Audio:Album'),
        'title'      : Attr(b'CSTR', b'Media:Title'),
        'date'       : Attr(b'LONG', b'Media:Year'),
        'comment:'   : Attr(b'CSTR', b'Media:Comment'),
        'tracknumber': Attr(b'LONG', b'Audio:Track'),
        'genre'      : Attr(b'CSTR', b'Media:Genre'),
        'composer'   : Attr(b'CSTR', b'Audio:Composer'),
        '~rating'    : Attr(b'LONG', b'Media:Rating'),
        '~length'    : Attr(b'LLNG', b'Media:Length'),
        '~bitrate'   : Attr(b'CSTR', b'Audio:Bitrate'),
    }

    def get_numeric_type(attr):
        return struct.unpack('>I', attr.type)[0]

    def read_attr(fd, attr):
        info = AttrInfo()
        if be.fs_stat_attr(fd, attr.name, byref(info)) == -1:
            return None

        buffer = b'\0' * info.size
        bytes_read = be.fs_read_attr(fd, attr.name, info.type, 0,
                                     buffer, len(buffer))

        result = None
        if bytes_read > -1:
            buffer = buffer[:bytes_read]
            if attr.type == b'LONG':
                result = str(struct.unpack('=l', buffer)[0])
            elif attr.type == b'LLNG':
                result = str(struct.unpack('=q', buffer)[0])
            elif attr.type == b'CSTR':
                result = buffer.decode('utf-8', errors='replace')
            else:
                raise ValueError('Unsupported attribute type %s' % attr.type)

        log.debug("haikuattrs: fs_read_attr(%r, %r, %r, %r, %r, %r) -> %r: %r" % (
            fd, attr.name, info.type, 0, buffer, len(buffer), bytes_read, result))
        return result

    def remove_attr(fd, attr):
        return be.fs_remove_attr(fd, attr.name) == 0

    def write_attr(fd, attr, attr_value):
        if attr.type in (b'LONG', b'LLNG'):
            try:
                attr_value = int(attr_value)
            except ValueError:
                return False
            length = 4
            c_type = c_long if attr.type == b'LONG' else c_longlong
            buffer = byref(c_type(attr_value))
        elif attr.type == b'CSTR':
            attr_value = attr_value.encode('utf-8')
            length = len(attr_value)
            buffer = cast(attr_value, c_char_p)
        else:
            raise ValueError('Unsupported attribute type %s' % attr.type)

        int_type = get_numeric_type(attr)
        ret_val = be.fs_write_attr(fd, attr.name, int_type, 0, buffer, length)
        log.debug("haikuattrs: fs_write_attr(%r, %r, %r, %r, %r, %r) -> %r" % (
            fd, attr.name, int_type, 0, buffer, length, ret_val))
        return ret_val >= 0

    def set_attrs_from_metadata(file):
        log.debug('haikuattrs: setting attributes for %s' % file.filename)
        fd = os.open(file.filename, os.O_RDWR)
        try:
            for tag, attr in attr_map.items():
                value = file.orig_metadata[tag]
                if value:
                    if tag == 'date':
                        value = value[:4]
                    elif tag == '~length':
                        value = file.orig_metadata.length
                    elif tag == '~rating':
                        try:
                            value = int(value) * 2
                        except ValueError:
                            log.warning(
                                'haikuattrs: rating %r for %s is not an integer value',
                                value, file.filename)
                            continue
                    if not write_attr(fd, attr, value):
                        log.error('haikuattrs: setting %s=%s for %s failed' % (
                            attr.name, value, file.filename))
                else:
                    remove_attr(fd, attr)
        finally:
            os.close(fd)

    def set_attrs_from_metadata_finished(file, result=None, error=None):
        if error:
            log.error('haikuattrs: setting attributes for %s failed: %r' % (
                file.filename, error))
        else:
            log.debug('haikuattrs: attributes set for %s' % file.filename)

    def load_attrs_to_metadata(file):
        fd = os.open(file.filename, os.O_RDONLY)
        filename, _ = os.path.splitext(file.base_filename)
        try:
            for tag, attr in attr_map.items():
                # Technical variables that are loaded directly from the file
                if tag in ('~bitrate', '~length'):
                    continue
                # Ignore tags for which metadata is included in the file.
                # But ignore the special case where the title has been set to
                # the filename.
                value = file.metadata[tag]
                if value and not (tag == 'title' and value == filename):
                    continue
                value = read_attr(fd, attr)
                if value:
                    file.metadata[tag] = value
                    file.orig_metadata[tag] = value
        finally:
            os.close(fd)

    def load_attrs_to_metadata_finished(file, result=None, error=None):
        if error:
            log.error('haikuattrs: loading attributes for %s failed: %r' % (
                file.filename, error))
        else:
            log.debug('haikuattrs: attributes loaded for %s' % file.filename)
            file.update()

    def on_file_load_processor(file):
        thread.run_task(
            partial(load_attrs_to_metadata, file),
            partial(load_attrs_to_metadata_finished, file))

    def on_file_save_processor(file):
        thread.run_task(
            partial(set_attrs_from_metadata, file),
            partial(set_attrs_from_metadata_finished, file))

    register_file_post_load_processor(on_file_load_processor)
    register_file_post_save_processor(on_file_save_processor)
