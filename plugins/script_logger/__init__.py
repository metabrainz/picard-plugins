# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Bob Swift (rdswift)
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

# pylint: disable=missing-module-docstring, wrong-import-position, line-too-long

PLUGIN_NAME = 'Script Logger'
PLUGIN_AUTHOR = 'Bob Swift (rdswift)'
PLUGIN_DESCRIPTION = '''
This plugin provides a new script function `$logline()` to write entries
to Picard's system log.  By default, the log level is set at `Info`, but
any level can be used by providing the level as an optional second
parameter to the function.

The function is used as:

`$logline(text[,level])`

where `text` is the text to write to the log.  The entry will be written
at log level `Info` by default, but this can be changed by specifying a
different level as an optional second parameter.  Allowable log levels are:

- E (Error)
- W (Warning)
- I (Info)
- D (Debug)

If an unknown level is entered, the function will use the default `Info`
level.
'''
PLUGIN_VERSION = '0.1'
PLUGIN_API_VERSIONS = ['2.0', '2.1', '2.2', '2.3', '2.6', '2.9']
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.txt"

PLUGIN_USER_GUIDE_URL = "https://github.com/rdswift/picard-plugins/blob/2.0_RDS_Plugins/plugins/script_logger/docs/README.md"

DOCUMENTATION = """\
`$logline(text[,level])`

where `text` is the text to write to the log.  The entry will be written
at log level `Info` by default, but this can be changed by specifying a
different level as an optional second parameter.  Allowable log levels are:

- E (Error)
- W (Warning)
- I (Info)
- D (Debug)

If an unknown level is entered, the function will use the default `Info`
level.
"""

from picard import log
from picard.script import register_script_function

LEVELS = {
    'E': log.error,
    'W': log.warning,
    'I': log.info,
    'D': log.debug,
}

def logline(_parser, text: str, level=None):
    """Logs text to the Picard log.

    Args:
        _parser (parser): Script parser
        text (str): Text message to log
        level (str, optional): Level to use for logging ('E', 'W', 'I' or 'D'). Defaults to 'I'.
    """
    if level:
        _level = (str(level).strip().upper() + 'I')[0]
    else:
        _level = 'I'
    if _level not in LEVELS:
        _level = 'I'
    LEVELS[_level](text.strip())
    return ''

register_script_function(logline, documentation=DOCUMENTATION)
