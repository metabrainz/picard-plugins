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
PLUGIN_DESCRIPTION = 'Improves the video support in Picard by adding support for Matroska, WebM, AVI, QuickTime and MPEG files (renaming and fingerprinting only, no tagging) and providing $is_audio() and $is_video() scripting functions.'
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["1.0.0"]

from picard.formats import register_format
from picard.script import register_script_function
from picard.plugins.videotools.formats import MatroskaFile, MpegFile, QuickTimeFile, RiffFile
from picard.plugins.videotools.script import is_audio, is_video


# Now this is kind of a hack, but Picard won't process registered objects that
# are in a submodule of a plugin. I still want the code to be in separate files.
MatroskaFile.__module__ = MpegFile.__module__ = QuickTimeFile.__module__ = \
    RiffFile.__module__ = is_audio.__module__ = is_video.__module__ = \
    __name__

register_format(MatroskaFile)
register_format(MpegFile)
register_format(QuickTimeFile)
register_format(RiffFile)

register_script_function(is_audio)
register_script_function(is_video)
