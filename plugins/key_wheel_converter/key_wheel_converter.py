# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 Bob Swift (rdswift)
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

# pylint: disable=C0413     (wrong-import-position)
# pylint: disable=W0613     (unused-argument)

PLUGIN_NAME = 'Key Wheel Converter'
PLUGIN_AUTHOR = 'Bob Swift'
PLUGIN_DESCRIPTION = '''
<p>
Adds functions to convert between 'standard', 'camelot' and 'open key' key formats.
</p>
'''
PLUGIN_VERSION = '1.0'
PLUGIN_API_VERSIONS = ['2.3', '2.4', '2.6', '2.7']
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.txt"

import re

# pylint: disable=E0402     (import-error)
from picard import log
from picard.script import register_script_function


# pylint: disable=R0903     (too-few-public-methods)
class KeyMap():
    """\
        Class to hold the mapping dictionary.  The dictionary is
        stored as a class variable so that it is only generated once.
    """
    # List of tuples of:
    #   'camelot key',
    #   'open key',
    #   'standard key /w symbols',
    #   'standard key /w text'
    _keys = [
        ('1A', '6m', 'A♭ Minor', 'A-Flat Minor'),
        ('1B', '6d', 'B Major', 'B Major'),
        ('2A', '7m', 'E♭ Minor', 'E-Flat Minor'),
        ('2B', '7d', 'F# Major', 'F-Sharp Major'),
        ('3A', '8m', 'B♭ Minor', 'B-Flat Minor'),
        ('3B', '8d', 'D♭ Major', 'D-Flat Major'),
        ('4A', '9m', 'F Minor', 'F Minor'),
        ('4B', '9d', 'A♭ Major', 'A-Flat Major'),
        ('5A', '10m', 'C Minor', 'C Minor'),
        ('5B', '10d', 'E♭ Major', 'E-Flat Major'),
        ('6A', '11m', 'G Minor', 'G Minor'),
        ('6B', '11d', 'B♭ Major', 'B-Flat Major'),
        ('7A', '12m', 'D Minor', 'D Minor'),
        ('7B', '12d', 'F Major', 'F Major'),
        ('8A', '1m', 'A Minor', 'A Minor'),
        ('8B', '1d', 'C Major', 'C Major'),
        ('9A', '2m', 'E Minor', 'E Minor'),
        ('9B', '2d', 'G Major', 'G Major'),
        ('10A', '3m', 'B Minor', 'B Minor'),
        ('10B', '3d', 'D Major', 'D Major'),
        ('11A', '4m', 'G♭ Minor', 'G-Flat Minor'),
        ('11B', '4d', 'A Major', 'A Major'),
        ('12A', '5m', 'D♭ Minor', 'D-Flat Minor'),
        ('12B', '5d', 'E Major', 'E Major'),
    ]

    # Build mapping dictionary with 'camelot' and 'standard with text' keys.
    keys = {}
    for item in _keys:
        for i in [0, 3]:
            keys[item[i]] = {
                'camelot': item[0],
                'open': item[1],
                'standard_s': item[2],
                'standard_t': item[3],
            }

    def __init__(self):
        """Class to hold the mapping dictionary.
        """


def _matcher(text, out_type):
    """Helper function that performs the actual key lookup.

    Args:
        text (str): Key provided by the user.
        out_type (str): Output format to use for the return value

    Returns:
        str: Value mapped to the key for the specified output type
    """
    match_text = _parse_input(text)
    if match_text not in KeyMap.keys:
        log.debug("{0}: Unable to match key: '{1}'".format(PLUGIN_NAME, text,))
        return ''
    return KeyMap.keys[match_text][out_type]


def _parse_input(text):
    """Helper function to parse the input argument to try to match
    one of the supported formats used for the mapping keys.

    Args:
        text (str): Input argument provided by the user

    Returns:
        str: Argument converted to supported key format (if possible)
    """
    text = text.strip()
    if not text:
        return ''

    if re.match("[0-9]{1,2}[ABab]$", text):
        # Matches camelot key.  Fix capitalization for lookup.
        return text.upper()

    if re.match("[0-9]{1,2}[dmDM]$", text):
        # Matches open key format.  Convert to camelot key for lookup.
        temp = int(text[0:-1])
        # if temp > 0 and temp < 13:
        if 0 < temp < 13:
            _num = ((temp + 6) % 12) + 1
            _char = text[-1:].lower().replace('m', 'A').replace('d', 'B')
            return "{0}{1}".format(_num, _char,)

    # Parse as standard key
    # Add missing hyphens before 'Flat' and 'Sharp'
    text = text.lower().replace(' s', '-s').replace(' f', '-f')
    # Convert symbols to text for lookup.
    parts = text.replace('♭', '-Flat').replace('#', '-Sharp').split()
    for (i, part) in enumerate(parts):
        parts[i] = part[0:1].upper() + part[1:]
    _return = ' '.join(parts).replace('-s', '-S').replace('-f', '-F')
    # Handle cases where there are multiple circle of fifths entries for the item
    if _return == 'G-Flat Major':
        _return = 'F-Sharp Major'
    elif _return == 'D-Sharp Minor':
        _return = 'E-Flat Minor'
    return _return


def key2camelot(parser, text):
    """Any key to camelot format converter.

    Args:
        parser (object): Picard parser object
        text (str): Key to convert

    Returns:
        str: Converted key value

    Tests:

    >>> key2camelot(None, '1A')
    '1A'
    >>> key2camelot(None, '6m')
    '1A'
    >>> key2camelot(None, 'A♭ Minor')
    '1A'
    >>> key2camelot(None, 'A-Flat Minor')
    '1A'
    >>> key2camelot(None, '1a')
    '1A'
    >>> key2camelot(None, '6M')
    '1A'
    >>> key2camelot(None, 'A-FLAT MINOR')
    '1A'
    >>> key2camelot(None, 'a-flat minor')
    '1A'
    >>> key2camelot(None, ' 1A')
    '1A'
    >>> key2camelot(None, '1A ')
    '1A'
    >>> key2camelot(None, '')
    ''
    >>> key2camelot(None, 'A-Flat Minor x')
    ''
    >>> key2camelot(None, 'H-Flat Minor')
    ''
    >>> key2camelot(None, '1-Flat Minor')
    ''
    >>> key2camelot(None, 'A-Flat')
    ''
    >>> key2camelot(None, 'A♭')
    ''
    >>> key2camelot(None, '0a')
    ''
    >>> key2camelot(None, '13a')
    ''
    >>> key2camelot(None, '0m')
    ''
    >>> key2camelot(None, '13m')
    ''
    >>> key2camelot(None, '1x')
    ''
    """
    return _matcher(text, 'camelot')


def key2openkey(parser, text):
    """Any key to open key format converter.

    Args:
        parser (object): Picard parser object
        text (str): Key to convert

    Returns:
        str: Converted key value

    Tests:

    >>> key2openkey(None, '1A')
    '6m'
    >>> key2openkey(None, '6m')
    '6m'
    >>> key2openkey(None, 'A♭ Minor')
    '6m'
    >>> key2openkey(None, 'A-Flat Minor')
    '6m'
    >>> key2openkey(None, '1a')
    '6m'
    >>> key2openkey(None, '6M')
    '6m'
    >>> key2openkey(None, 'A-FLAT MINOR')
    '6m'
    >>> key2openkey(None, 'a-flat minor')
    '6m'
    >>> key2openkey(None, ' 1A')
    '6m'
    >>> key2openkey(None, '1A ')
    '6m'
    >>> key2openkey(None, '')
    ''
    >>> key2openkey(None, 'A-Flat Minor x')
    ''
    >>> key2openkey(None, 'H-Flat Minor')
    ''
    >>> key2openkey(None, '1-Flat Minor')
    ''
    >>> key2openkey(None, 'A-Flat')
    ''
    >>> key2openkey(None, 'A♭')
    ''
    >>> key2openkey(None, '0a')
    ''
    >>> key2openkey(None, '13a')
    ''
    >>> key2openkey(None, '0m')
    ''
    >>> key2openkey(None, '13m')
    ''
    >>> key2openkey(None, '1x')
    ''
    """
    return _matcher(text, 'open')


def key2standard(parser, text, use_symbol=''):
    """Any key to standard key format converter.

    Args:
        parser (object): Picard parser object
        text (str): Key to convert
        use_symbol (str, optional): Use '♭' and '#' symbols. Defaults to False.

    Returns:
        str: Converted key value

    Tests:

    >>> key2standard(None, '1A')
    'A-Flat Minor'
    >>> key2standard(None, '6m')
    'A-Flat Minor'
    >>> key2standard(None, 'A♭ Minor')
    'A-Flat Minor'
    >>> key2standard(None, 'A-Flat Minor')
    'A-Flat Minor'
    >>> key2standard(None, '1a')
    'A-Flat Minor'
    >>> key2standard(None, '6M')
    'A-Flat Minor'
    >>> key2standard(None, 'A-FLAT MINOR')
    'A-Flat Minor'
    >>> key2standard(None, 'a-flat minor')
    'A-Flat Minor'
    >>> key2standard(None, ' 1A')
    'A-Flat Minor'
    >>> key2standard(None, '1A ')
    'A-Flat Minor'
    >>> key2standard(None, '')
    ''
    >>> key2standard(None, 'A-Flat Minor x')
    ''
    >>> key2standard(None, 'H-Flat Minor')
    ''
    >>> key2standard(None, '1-Flat Minor')
    ''
    >>> key2standard(None, 'A-Flat')
    ''
    >>> key2standard(None, 'A♭')
    ''
    >>> key2standard(None, '0a')
    ''
    >>> key2standard(None, '13a')
    ''
    >>> key2standard(None, '0m')
    ''
    >>> key2standard(None, '13m')
    ''
    >>> key2standard(None, '1x')
    ''

    >>> key2standard(None, '1A', 'x')
    'A♭ Minor'
    >>> key2standard(None, '6m', 'x')
    'A♭ Minor'
    >>> key2standard(None, 'A♭ Minor', 'x')
    'A♭ Minor'
    >>> key2standard(None, 'A-Flat Minor', 'x')
    'A♭ Minor'
    >>> key2standard(None, '1a', 'x')
    'A♭ Minor'
    >>> key2standard(None, '6M', 'x')
    'A♭ Minor'
    >>> key2standard(None, 'A-FLAT MINOR', 'x')
    'A♭ Minor'
    >>> key2standard(None, 'a-flat minor', 'x')
    'A♭ Minor'
    >>> key2standard(None, ' 1A', 'x')
    'A♭ Minor'
    >>> key2standard(None, '1A ', 'x')
    'A♭ Minor'
    >>> key2standard(None, '1A ', ' ')
    'A♭ Minor'
    >>> key2standard(None, '', 'x')
    ''
    >>> key2standard(None, 'A-Flat Minor x', 'x')
    ''
    >>> key2standard(None, 'H-Flat Minor', 'x')
    ''
    >>> key2standard(None, '1-Flat Minor', 'x')
    ''
    >>> key2standard(None, 'A-Flat', 'x')
    ''
    >>> key2standard(None, 'A♭', 'x')
    ''
    >>> key2standard(None, '0a', 'x')
    ''
    >>> key2standard(None, '13a', 'x')
    ''
    >>> key2standard(None, '0m', 'x')
    ''
    >>> key2standard(None, '13m', 'x')
    ''
    >>> key2standard(None, '1x', 'x')
    ''

    >>> key2standard(None, 'A Flat Minor')
    'A-Flat Minor'
    >>> key2standard(None, 'F Sharp Major')
    'F-Sharp Major'
    >>> key2standard(None, 'G♭ Major')
    'F-Sharp Major'
    >>> key2standard(None, 'D# Minor')
    'E-Flat Minor'
    """
    if use_symbol:
        return _matcher(text, 'standard_s')
    return _matcher(text, 'standard_t')


register_script_function(key2camelot, name='key2camelot',
    documentation="""`$key2camelot(key)`

Returns the key string `key` in camelot key format.

The `key` argument can be entered in any of the supported formats, such as
'2B' (camelot), '6d' (open key), 'A♭ Minor' (standard with symbols) or
'A-Flat Minor' (standard with text).  If the `key` argument is not recognized
as one of the standard keys in the circle of fifths, then an empty string will
be returned.""")

register_script_function(key2openkey, name='key2openkey',
    documentation="""`$key2openkey(key)`

Returns the key string `key` in open key format.

The `key` argument can be entered in any of the supported formats, such as
'2B' (camelot), '6d' (open key), 'A♭ Minor' (standard with symbols) or
'A-Flat Minor' (standard with text).  If the `key` argument is not recognized
as one of the standard keys in the circle of fifths, then an empty string will
be returned.""")

register_script_function(key2standard, name='key2standard',
    documentation="""`$key2standard(key[,symbols])`

Returns the key string `key` in standard key format.  If the optional argument
`symbols` is set, then the '♭' and '#' symbols will be used, rather than
spelling out '-Flat' and '-Sharp'.

The `key` argument can be entered in any of the supported formats, such as
'2B' (camelot), '6d' (open key), 'A♭ Minor' (standard with symbols) or
'A-Flat Minor' (standard with text).  If the `key` argument is not recognized
as one of the standard keys in the circle of fifths, then an empty string will
be returned.""")

if __name__ == "__main__":
    import doctest
    doctest.testmod()
