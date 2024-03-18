# -*- coding: utf-8 -*-
#
# Copyright (C) 2014, 2017, 2021, 2023-2024 Philipp Wolfer
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

PLUGIN_NAME = 'Tagger script functions $is_lossless() and $is_lossy()'
PLUGIN_AUTHOR = 'Philipp Wolfer'
PLUGIN_DESCRIPTION = 'Tagger script functions to detect if a file is lossless or lossy'
PLUGIN_VERSION = "0.3"
PLUGIN_API_VERSIONS = ["2.0", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9", "2.10", "2.11"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"


LOSSLESS_EXTENSIONS = ['flac', 'oggflac', 'ape', 'ofr', 'tak', 'wv', 'tta',
                       'aiff', 'aif', 'wav']

from picard.script import register_script_function


def is_lossless(parser):
    """
    Returns true, if the file processed is a lossless audio format.
    Note: This depends mainly on the file extension and does not look inside the
    file to detect the codec.
    """
    if parser.context['~extension'] in LOSSLESS_EXTENSIONS:
        return "1"
    elif parser.context['~extension'] == 'm4a':
        # Mutagen < 1.26 fails to detect the bitrate for Apple Lossless Audio Codec.
        if not parser.context['~bitrate']:
            return "1"
        else:
            try:
                bitrate = float(parser.context['~bitrate'])
                return "1" if bitrate > 1000 else ""
            except (TypeError, ValueError):
                return ""
    else:
        return ""


def is_lossy(parser):
    """Returns true, if the file processed is a lossy audio format."""
    return "" if is_lossless(parser) == "1" else "1"


register_script_function(is_lossless)
register_script_function(is_lossy)
