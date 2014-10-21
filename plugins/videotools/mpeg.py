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
from picard.formats import register_format
from picard.metadata import Metadata


class MpegFile(File):
    EXTENSIONS = [".mpg", ".mpeg"]
    NAME = "MPEG"

    def _load(self, filename):
        log.debug("Loading file %r", filename)
        metadata = Metadata()
        metadata['~format'] = self.NAME
        self._add_path_to_metadata(metadata)
        return metadata

    def _save(self, filename, metadata):
        log.debug("Saving file %r", filename)
        pass
