# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Philipp Wolfer
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

import enzyme
from picard import log
from picard.file import File
from picard.formats import register_format
from picard.formats.wav import WAVFile
from picard.metadata import Metadata


class EnzymeFile(File):

    def _load(self, filename):
        log.debug("Loading file %r", filename)
        metadata = Metadata()
        self._add_path_to_metadata(metadata)

        try:
            parser = enzyme.parse(filename)
            log.debug("Metadata for %s:\n%s", filename, unicode(parser))
            self._convertMetadata(parser, metadata)
        except Exception, err:
            log.error("Could not parse file %r: %r", filename, err)

        return metadata

    def _convertMetadata(self, parser, metadata):
        metadata['~format'] = parser.type

        if parser.title:
            metadata["title"] = parser.title

        if parser.artist:
            metadata["artist"] = parser.artist

        if parser.trackno:
            parts = parser.trackno.split("/")
            metadata["tracknumber"] = parts[0]
            if len(parts) > 1:
                metadata["totaltracks"] = parts[1]

        if parser.encoder:
            metadata["encodedby"] = parser.encoder

        if parser.video[0]:
            video = parser.video[0]
            metadata["~video"] = True

        if parser.audio[0]:
            audio = parser.audio[0]
            if audio.channels:
                metadata["~channels"] = audio.channels

            if audio.samplerate:
                metadata["~sample_rate"] = audio.samplerate

            if audio.language:
                metadata["language"] = audio.language

        if parser.length:
            metadata.length = parser.length * 1000
        elif video and video.length:
            metadata.length = parser.video[0].length * 1000

    def _save(self, filename, metadata):
        log.debug("Saving file %r", filename)
        pass


class MatroskaFile(EnzymeFile):
    EXTENSIONS = [".mka", ".mkv", ".webm"]
    NAME = "Matroska"


class MpegFile(EnzymeFile):
    EXTENSIONS = [".mpg", ".mpeg"]
    NAME = "MPEG"


class RiffFile(EnzymeFile):
    EXTENSIONS = [".avi"]
    NAME = "RIFF"


class QuickTimeFile(EnzymeFile):
    EXTENSIONS = [".mov", ".qt"]
    NAME = "QuickTime"
