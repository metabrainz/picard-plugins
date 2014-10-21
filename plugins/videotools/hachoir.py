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


from picard import log
from picard.file import File
from picard.metadata import Metadata

try:
    from hachoir_core.error import HachoirError
    from hachoir_parser import createParser
    from hachoir_metadata import extractMetadata
    from hachoir_metadata.metadata import MultipleMetadata
    hasHachoir = True
except ImportError, err:
    log.warning("videotools: hachoir not available, no video metadata")
    log.debug(err)
    hasHachoir = False


class HachoirFile(File):

    def _load(self, filename):
        log.debug("Loading file %r", filename)
        metadata = Metadata()
        metadata['~format'] = self.NAME
        if hasHachoir:
          parsedMetadata = self._parseMetadata(filename)
          self._fillMetadata(metadata, parsedMetadata)
        self._add_path_to_metadata(metadata)
        return metadata

    def _save(self, filename, metadata):
        log.debug("Saving file %r", filename)
        pass

    def _parseMetadata(self, filename):
        metadata = None
        parser = createParser(filename)

        if not parser:
            log.warn("Could not parse metadata for %r", realname)
        else:
            try:
                metadata = extractMetadata(parser)
            except HachoirError, err:
                log.error("Metadata extraction error: %s", unicode(err))

        return metadata

    def _fillMetadata(self, metadata, parsedMetadata):
        if parsedMetadata:
            log.debug(
                "Metadata %s", parsedMetadata.exportPlaintext(human=False))

            codecInfo = self._getCodecInfo(parsedMetadata)
            if codecInfo:
              metadata['~format'] = "%s (%s)" % (self.NAME, codecInfo)

            if parsedMetadata.has("title"):
                metadata["title"] = parsedMetadata.get("title")

            if parsedMetadata.has("duration"):
                metadata.length = 1000 * \
                    parsedMetadata.get("duration").total_seconds()

            audioData = self._getAudioMetadata(parsedMetadata)
            if audioData:
                if audioData.has("nb_channel"):
                    metadata['~channels'] = audioData.get("nb_channel")
                if audioData.has("bits_per_sample"):
                    metadata['~bits_per_sample'] = audioData.get(
                        "bits_per_sample")
                if audioData.has("sample_rate"):
                    metadata['~sample_rate'] = audioData.get("sample_rate")

    def _getCodecInfo(self, metadata):
        codecs = []

        video = self._getVideoMetadata(metadata)
        if video:
            codecs.append(video.get("compression"))

        audio = self._getAudioMetadata(metadata)
        if audio:
            codecs.append(audio.get("compression"))

        codecInfo = ", ".join(codecs)
        return codecInfo

    def _getVideoMetadata(self, metadata):
        return self._findMetadataGroup(metadata, ["video", "video[1]"])

    def _getAudioMetadata(self, metadata):
        return self._findMetadataGroup(metadata, ["audio", "audio[1]"])

    def _findMetadataGroup(self, metadata, keys):
        if not isinstance(metadata, MultipleMetadata):
          return None

        for key in keys:
            if key in metadata:
                return metadata[key]
        else:
            return None


class AviFile(HachoirFile):
    EXTENSIONS = [".avi"]
    NAME = "Microsoft AVI"


class MatroskaFile(HachoirFile):
    EXTENSIONS = [".mkv"]
    NAME = "Matroska"


class QuickTimeFile(HachoirFile):
    EXTENSIONS = [".mov"]
    NAME = "QuickTime"
