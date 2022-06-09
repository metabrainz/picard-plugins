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

PLUGIN_NAME = 'MOD files'
PLUGIN_AUTHOR = 'Philipp Wolfer'
PLUGIN_DESCRIPTION = (
    'Support for loading and renaming various tracker module formats '
    '(.mod, .xm, .it, .mptm, .ahx, .mtm, .med, .s3m, .ult, .699, .okt). '
    'There is limited support for writing the title tag as track name for '
    'some formats.'
)
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["2.8"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from dataclasses import dataclass
from enum import Enum
from io import RawIOBase
import struct

from mutagen._util import resize_bytes

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


class MagicBytes(bytes):
    offset: int = 0

    def __new__(cls, value, offset: int=0):
        self = super().__new__(cls, value)
        self.offset = offset
        return self


class ModuleFile(File):
    # Allows to specify a magic number to identify the file format.
    # Re-implement _ensure_format for more complex cases.
    _magic_bytes: tuple[MagicBytes] = None

    # Specify the encoding for the format.
    # There is not much info about encoding, most files seem to be limited
    # to ASCII. But cp850 seems to be a solid default for the few files that
    # use 8-bit characters.
    _encoding = 'cp850'  # or cp437?

    # List of StaticField. Most fields in mod files
    # have static position and fixed size.
    _static_text_fields: tuple[StaticField] = ()

    @classmethod
    def supports_tag(cls, name: str) -> bool:
        return name in {field.name for field in cls._static_text_fields}

    def _load(self, filename: str) -> Metadata:
        log.debug('Loading file %r', filename)
        metadata = Metadata()
        self._add_path_to_metadata(metadata)
        metadata['~format'] = self.NAME
        with open(filename, 'rb') as f:
            magic = self._ensure_format(f)
            self._parse_file(f, metadata, magic)
        return metadata

    def _save(self, filename: str, metadata: Metadata):
        log.debug('Saving file %r', filename)
        with open(filename, 'rb+') as f:
            self._ensure_format(f)
            self._write_file(f, metadata)

    def _ensure_format(self, f: RawIOBase) -> MagicBytes:
        if not self._magic_bytes:
            raise NotImplementedError('_magic_bytes not set or method not implemented')
        for magic in self._magic_bytes:
            if self._magic_matches(f, magic):
                return magic
        # None of the magic byte sequences matched, fail loading
        raise ValueError('Not a %s file' % self.NAME)

    def _magic_matches(self, f: RawIOBase, magic: MagicBytes) -> bool:
        f.seek(magic.offset)
        file_id = f.read(len(magic))
        return file_id == magic

    def _parse_file(self, f: RawIOBase, metadata: Metadata, magic: MagicBytes):
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

    def _encode_text(self, text: str, length: int=None, fillchar: str=' ') -> bytes:
        if length:
            text = text[:length].ljust(length, fillchar)
        return asciipunct(text).encode(self._encoding, errors='replace')


class MODFile(ModuleFile):
    EXTENSIONS = ['.mod']
    NAME = 'MOD'

    # https://www.ocf.berkeley.edu/~eek/index.html/tiny_examples/ptmod/ap12.html
    _magic_bytes = (MagicBytes(b'M\x2eK\x2e', offset=1080),)
    _static_text_fields = (
        StaticField('title', 0, 20, FieldAccess.READ_WRITE),
    )


class ExtendedModuleFile(ModuleFile):
    EXTENSIONS = ['.xm']
    NAME = 'Extended Module'

    # https://github.com/milkytracker/MilkyTracker/blob/master/resources/reference/xm-form.txt
    _magic_bytes = (MagicBytes(b'Extended Module: '),)
    _static_text_fields = (
        StaticField('title', 17, 20, FieldAccess.READ_WRITE),
        StaticField('encodedby', 38, 20, FieldAccess.READ_WRITE),
    )

    def _parse_file(self, f: RawIOBase, metadata: Metadata, magic: MagicBytes):
        super()._parse_file(f, metadata, magic)
        # OpenMPT seems to use iso-8859-1 encoding.
        if metadata['encodedby'].startswith('OpenMPT'):
            self._encoding = 'iso-8859-1'
            super()._parse_file(f, metadata, magic)
        f.seek(68)
        metadata['~channels'] = struct.unpack('<h', f.read(2))[0]


class ImpulseTrackerFile(ModuleFile):
    EXTENSIONS = ['.it', '.mptm']
    NAME = 'Impulse Tracker'

    # https://fileformats.fandom.com/wiki/Impulse_tracker
    # https://wiki.openmpt.org/Manual:_Module_formats#The_OpenMPT_format_.28.mptm.29
    _magic_bytes = (MagicBytes(b'IMPM'),)
    _static_text_fields = (
        StaticField('title', 4, 26, FieldAccess.READ_WRITE, '\0'),
    )

    def _parse_file(self, f: RawIOBase, metadata: Metadata, magic: MagicBytes):
        if self._magic_matches(f, MagicBytes(b'OMPT', offset=60)):
            self._encoding = 'iso-8859-1'
            metadata['~format'] = 'OpenMPT'
            # TODO: For OpenMPT enhanced format parse also the author and comment
        super()._parse_file(f, metadata, magic)


class AHXFile(ModuleFile):
    EXTENSIONS = ['.ahx']
    NAME = 'AHX'

    # http://lclevy.free.fr/exotica/ahx/ahxformat.txt
    _magic_bytes = (MagicBytes(b'THX'),)

    @classmethod
    def supports_tag(cls, name: str) -> bool:
        return name in {'title'}

    def _parse_file(self, f: RawIOBase, metadata: Metadata, magic: MagicBytes):
        self._seek_names_offset(f)
        metadata['title'] = self._decode_text(self._read_string(f))

    def _write_file(self, f: RawIOBase, metadata: Metadata):
        # Write the title (first null terminated string after the samples)
        names_offset = self._seek_names_offset(f)
        old_title = self._read_string(f)
        new_title = self._encode_text(metadata['title'])
        resize_bytes(f, len(old_title), len(new_title), names_offset)
        f.seek(names_offset)
        f.write(new_title)

    def _seek_names_offset(self, f: RawIOBase) -> int:
        f.seek(6)
        len_ = struct.unpack('>H', f.read(2))[0] & 0xfff
        f.seek(10)
        trl, trk, smp, ss = struct.unpack('BBBB', f.read(4))
        samples_offset = 14 + ss*2 + len_*8 + (trk+1)*trl*3
        f.seek(samples_offset)
        self._skip_samples(f, count=smp)
        return f.tell()

    def _skip_samples(self, f: RawIOBase, count: int):
        while count:
            f.seek(f.tell() + 21)
            plen = struct.unpack('B', f.read(1))[0]
            f.seek(f.tell() + plen*4)
            count -= 1

    def _read_string(self, f: RawIOBase) -> bytes:
        """Reads a null terminated string from the current position."""
        result = b''
        char = f.read(1)
        while char and char != b'\0':
            result += char
            char = f.read(1)
        return result


class MEDFile(ModuleFile):
    EXTENSIONS = ['.med']
    NAME = 'MED'

    # https://github.com/dv1/ion_player/blob/master/extern/uade-2.13/amigasrc/players/med/MMD_FileFormat.doc
    _magic_bytes = (
        MagicBytes(b'MMD0'),
        MagicBytes(b'MMD1'),
        MagicBytes(b'MMD2'),
        MagicBytes(b'MMD3'),
    )

    def _parse_file(self, f: RawIOBase, metadata: Metadata, magic: MagicBytes):
        # TODO: Extract songname
        super()._parse_file(f, metadata, magic)
        metadata['~format'] = '%s (%s)' % (self.NAME, self._decode_text(magic))


class MTMFile(ModuleFile):
    EXTENSIONS = ['.mtm']
    NAME = 'MTM'

    # https://www.fileformat.info/format/mtm/corion.htm
    _magic_bytes = (MagicBytes(b'MTM'),)
    _static_text_fields = (
        StaticField('title', 4, 20, FieldAccess.READ_WRITE, '\0'),
    )


class S3MFile(ModuleFile):
    EXTENSIONS = ['.s3m']
    NAME = 'S3M'

    # https://www.fileformat.info/format/screamtracker/corion.htm
    _magic_bytes = (MagicBytes(b'\x1a', offset=28),)
    _static_text_fields = (
        StaticField('title', 0, 20, FieldAccess.READ_WRITE, '\0'),
        StaticField('encodedby', 20, 8, FieldAccess.READ_WRITE, '\0'),
    )


class ULTFile(ModuleFile):
    EXTENSIONS = ['.ult']
    NAME = 'ULT'

    # http://www.textfiles.com/programming/FORMATS/ultform.pro
    # http://www.textfiles.com/programming/FORMATS/ultform14.pro
    _magic_bytes = (
        MagicBytes(b'MAS_UTrack_V001'),
        MagicBytes(b'MAS_UTrack_V002'),
        MagicBytes(b'MAS_UTrack_V003'),
        MagicBytes(b'MAS_UTrack_V004'),
    )
    _static_text_fields = (
        StaticField('title', 15, 32, FieldAccess.READ_WRITE),
    )

    def _parse_file(self, f: RawIOBase, metadata: Metadata, magic: MagicBytes):
        super()._parse_file(f, metadata, magic)
        metadata['~format'] = '%s (%s)' % (self.NAME, self._decode_text(magic))


class Composer669File(ModuleFile):
    EXTENSIONS = ['.669']
    NAME = 'Composer 669'

    # http://www.textfiles.com/programming/FORMATS/669-form.pro
    _magic_bytes = (
        MagicBytes(b'if'),
        MagicBytes(b'JN'),  # Extended 669
    )
    _static_text_fields = (
        StaticField('comment', 2, 108, FieldAccess.READ_WRITE),
    )

    def _parse_file(self, f: RawIOBase, metadata: Metadata, magic: MagicBytes):
        super()._parse_file(f, metadata, magic)
        if magic == b'JN':
            metadata['~format'] = 'Extended Composer 669'


class OktalyzerFile(ModuleFile):
    EXTENSIONS = ['.okt']
    NAME = 'Oktalyzer'

    # http://www.vgmpf.com/Wiki/index.php?title=OKT
    _magic_bytes = (MagicBytes(b'OKTASONGCMOD'),)


register_format(MODFile)
register_format(ExtendedModuleFile)
register_format(ImpulseTrackerFile)
register_format(AHXFile)
register_format(MEDFile)
register_format(MTMFile)
register_format(S3MFile)
register_format(ULTFile)
register_format(Composer669File)
register_format(OktalyzerFile)
