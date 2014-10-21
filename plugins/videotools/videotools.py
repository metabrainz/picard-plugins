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

PLUGIN_NAME = 'Video tools'
PLUGIN_AUTHOR = 'Philipp Wolfer'
PLUGIN_DESCRIPTION = 'Improves the video support in Picard by adding support for MPEG and Matroska files (renaming and fingerprinting only, no tagging) and providing $is_audio() and $is_video() scripting functions.'
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["1.0.0"]

from picard import log
from picard.file import File
from picard.formats import register_format
from picard.metadata import Metadata
from picard.script import register_script_function


def is_video(parser):
    """Returns true, if the file processed is a video file."""
    if parser.context['~extension'] in ['m4v', 'wmv', 'ogv', 'oggtheora', 'mpg', 'mpeg', 'mkv']:
        return "1"
    else:
        return ""

register_script_function(is_video)


def is_audio(parser):
    """Returns true, if the file processed is an audio file."""
    if is_video(parser) == "1":
        return ""
    else:
        return "1"

register_script_function(is_audio)


class MpegFile(File):
    EXTENSIONS = [".mpg", ".mpeg"]
    NAME = "MPEG"

    def _load(self, filename):
        log.debug("Loading file %r", filename)
        metadata = Metadata()
        metadata['~format'] = 'MPEG'
        self._add_path_to_metadata(metadata)
        return metadata

    def _save(self, filename, metadata):
        log.debug("Saving file %r", filename)
        pass


register_format(MpegFile)


class MatroskaFile(File):
    EXTENSIONS = [".mkv"]
    NAME = "Matroska"

    def _load(self, filename):
        log.debug("Loading file %r", filename)
        metadata = Metadata()
        metadata['~format'] = 'Matroska'
        self._add_path_to_metadata(metadata)
        return metadata

    def _save(self, filename, metadata):
        log.debug("Saving file %r", filename)
        pass


register_format(MatroskaFile)
