# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 Philipp Wolfer
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

PLUGIN_NAME = 'MOD formats'
PLUGIN_AUTHOR = 'Philipp Wolfer'
PLUGIN_DESCRIPTION = (
    'Support for loading and renaming various tracker files formats '
    '(.mod, .xm, .it).'
)
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["2.8"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from dataclasses import dataclass
from enum import Enum
import struct

from picard import log
from picard.file import File
from picard.formats import register_format
from picard.metadata import Metadata
from picard.util.textencoding import asciipunct


class FieldAccess(Enum):
    READ_ONLY = 0
    READ_WRITE = 1


@dataclass
class StaticField:
    name: str
    offset: int
    length: int
    access: FieldAccess
    fillchar: str = ' '


class ModuleFile(File):
    # Allows to specify a magic number to identify the file format.
    # Re-implement _ensure_format for more complex cases.
    _magic = None

    # Specify the encoding for the format.
    _encoding = 'cp850'  # or cp437?

    # List of StaticField. Most fields in mod files
    # have static position and fixed size.
    _static_text_fields = ()

    @classmethod
    def supports_tag(cls, name: str) -> bool:
        return name in {field.name for field in cls._static_text_fields}

    def _load(self, filename: str) -> Metadata:
        log.debug('Loading file %r', filename)
        metadata = Metadata()
        metadata['~format'] = self.NAME
        self._add_path_to_metadata(metadata)
        with open(filename, 'rb') as f:
            self._ensure_format(f)
            self._parse_file(f, metadata)
        return metadata

    def _save(self, filename: str, metadata: Metadata):
        log.debug('Saving file %r', filename)
        with open(filename, 'rb+') as f:
            self._ensure_format(f)
            self._write_file(f, metadata)

    def _ensure_format(self, f: RawIOBase):
        magic = self._magic
        if not magic:
            raise NotImplementedError('_magic not set or method not implemented')
        id = f.read(len(magic))
        if id != magic:
            raise ValueError('Not a %s file' % self.NAME)

    def _parse_file(self, f: RawIOBase, metadata: Metadata):
        for field in self._static_text_fields:
            f.seek(field.offset)
            metadata[field.name] = self._decode_text(f.read(field.length))

    def _write_file(self, f: RawIOBase, metadata: Metadata):
        for field in self._static_text_fields:
            if field.access == FieldAccess.READ_WRITE and not field.name.startswith('~'):
                f.seek(field.offset)
                f.write(self._encode_text(metadata[field.name], field.length, field.fillchar))

    def _decode_text(self, data: bytes) -> str:
        return data.decode(self._encoding, errors='replace').strip().strip('\0')

    def _encode_text(self, text: str, length: int, fillchar: str=' ') -> bytes:
        text = text[:length].ljust(length, fillchar)
        return asciipunct(text).encode(self._encoding, errors='replace')


class MODFile(ModuleFile):
    EXTENSIONS = ['.mod']
    NAME = 'MOD'

    # https://www.ocf.berkeley.edu/~eek/index.html/tiny_examples/ptmod/ap12.html
    _static_text_fields = (
        StaticField('title', 0, 20, FieldAccess.READ_WRITE),
    )

    def _ensure_format(self, f: RawIOBase):
        magic = b'M\x2eK\x2e'
        f.seek(1080)
        id = f.read(4)
        if id != magic:
            raise ValueError('Not a %s file' % self.NAME)


class ExtendedModuleFile(ModuleFile):
    EXTENSIONS = ['.xm']
    NAME = 'Extended Module'

    # https://github.com/milkytracker/MilkyTracker/blob/master/resources/reference/xm-form.txt
    _magic = b'Extended Module: '
    _static_text_fields = (
        StaticField('title', 17, 20, FieldAccess.READ_WRITE),
        StaticField('encodedby', 38, 20, FieldAccess.READ_WRITE),
    )

    def _parse_file(self, f: RawIOBase, metadata: Metadata):
        super()._parse_file(f, metadata)
        f.seek(68)
        metadata['~channels'] = struct.unpack('<h', f.read(2))[0]


class ImpulseTrackerFile(ModuleFile):
    EXTENSIONS = ['.it']
    NAME = 'Impulse Tracker'

    # https://fileformats.fandom.com/wiki/Impulse_tracker
    _magic = b'IMPM'
    _static_text_fields = (
        StaticField('title', 4, 26, FieldAccess.READ_WRITE, '\0'),
    )


register_format(MODFile)
register_format(ExtendedModuleFile)
register_format(ImpulseTrackerFile)

