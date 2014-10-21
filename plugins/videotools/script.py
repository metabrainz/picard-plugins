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


def is_video(parser):
    """Returns true, if the file processed is a video file."""
    if parser.context['~extension'] in ['m4v', 'wmv', 'ogv', 'oggtheora', 'mpg', 'mpeg', 'mkv', 'webm', 'mov', 'avi']:
        return "1"
    else:
        return ""


def is_audio(parser):
    """Returns true, if the file processed is an audio file."""
    if is_video(parser) == "1":
        return ""
    else:
        return "1"
