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
Adds functions to convert between 'standard', 'camelot', 'open key' and 'traktor' key formats.
'''
PLUGIN_VERSION = '1.1'
PLUGIN_API_VERSIONS = ['2.3', '2.4', '2.6', '2.7']
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.txt"

import re

# pylint: disable=E0402     (import-error)
from picard import log
from picard.script import register_script_function


# pylint: disable=R0903     (too-few-public-methods)
class KeyMap():
    """
        Class to hold the mapping dictionary.  The dictionary is
        stored as a class variable so that it is only generated once.
    """

    # Key Wheel references:
    # https://i.imgur.com/p9Kdevi.jpg
    # http://www.quanta.com.br/wp-content/uploads/2013/07/traktor-key-wheel_alta.jpg

    # List of tuples of:
    #   'camelot key',
    #   'open key',
    #   'standard key /w symbols',
    #   'standard key /w text'
    #   'traktor key'
    _keys = [
        ('1A', '6m', 'A♭ Minor', 'A-Flat Minor', 'G#m'),
        ('1B', '6d', 'B Major', 'B Major', 'B'),
        ('2A', '7m', 'E♭ Minor', 'E-Flat Minor', 'D#m'),
        ('2B', '7d', 'F# Major', 'F-Sharp Major', 'F#'),
        ('3A', '8m', 'B♭ Minor', 'B-Flat Minor', 'A#m'),
        ('3B', '8d', 'D♭ Major', 'D-Flat Major', 'C#'),
        ('4A', '9m', 'F Minor', 'F Minor', 'Fm'),
        ('4B', '9d', 'A♭ Major', 'A-Flat Major', 'G#'),
        ('5A', '10m', 'C Minor', 'C Minor', 'Cm'),
        ('5B', '10d', 'E♭ Major', 'E-Flat Major', 'D#'),
        ('6A', '11m', 'G Minor', 'G Minor', 'Gm'),
        ('6B', '11d', 'B♭ Major', 'B-Flat Major', 'A#'),
        ('7A', '12m', 'D Minor', 'D Minor', 'Dm'),
        ('7B', '12d', 'F Major', 'F Major', 'F'),
        ('8A', '1m', 'A Minor', 'A Minor', 'Am'),
        ('8B', '1d', 'C Major', 'C Major', 'C'),
        ('9A', '2m', 'E Minor', 'E Minor', 'Em'),
        ('9B', '2d', 'G Major', 'G Major', 'G'),
        ('10A', '3m', 'B Minor', 'B Minor', 'Bm'),
        ('10B', '3d', 'D Major', 'D Major', 'D'),
        ('11A', '4m', 'G♭ Minor', 'G-Flat Minor', 'F#m'),
        ('11B', '4d', 'A Major', 'A Major', 'A'),
        ('12A', '5m', 'D♭ Minor', 'D-Flat Minor', 'C#m'),
        ('12B', '5d', 'E Major', 'E Major', 'E'),
    ]

    # Build mapping dictionary with 'camelot', 'standard with text'
    # and 'traktor' keys.
    keys = {}
    for item in _keys:
        for i in [0, 3, 4]:
            keys[item[i]] = {
                'camelot': item[0],
                'open': item[1],
                'standard_s': item[2],
                'standard_t': item[3],
                'traktor': item[4],
            }

    # Alternate mapping for standard keys
    s_alt = {
        'G-Flat Major': 'F-Sharp Major',
        'D-Sharp Minor': 'E-Flat Minor',
    }

    # Alternate mapping for traktor keys
    t_alt = {
        'Ab': 'G#',
        'Bb': 'A#',
        'Db': 'C#',
        'Eb': 'D#',
        'Abm': 'G#m',
        'Bbm': 'A#m',
        'Dbm': 'C#m',
        'Ebm': 'D#m',
        'Gbm': 'F#m',
    }


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
        if 0 < temp < 13:
            _num = ((temp + 6) % 12) + 1
            _char = text[-1:].lower().replace('m', 'A').replace('d', 'B')
            return "{0}{1}".format(_num, _char,)

    if re.match("[a-g][#bB♭]?[mM]?$", text):
        # Matches Traktor key format.  Fix capitalization for lookup.
        temp = text[0:1].upper() + text[1:].replace('♭', 'b').lower()
        # Handle cases where there are multiple entries for the item
        if temp in KeyMap.t_alt:
            return KeyMap.t_alt[temp]
        return temp

    # Parse as standard key
    # Add missing hyphens before 'Flat' and 'Sharp'
    text = text.lower().replace(' s', '-s').replace(' f', '-f')
    # Convert symbols to text for lookup.
    parts = text.replace('♭', '-Flat').replace('#', '-Sharp').split()
    for (i, part) in enumerate(parts):
        parts[i] = part[0:1].upper() + part[1:]
    temp = ' '.join(parts).replace('-s', '-S').replace('-f', '-F')
    # Handle cases where there are multiple entries for the item
    if temp in KeyMap.s_alt:
        return KeyMap.s_alt[temp]
    return temp


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

    >>> key2camelot(None, 'c')
    '8B'
    >>> key2camelot(None, 'dB')
    '3B'
    >>> key2camelot(None, 'd#M')
    '2A'
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


def key2traktor(parser, text):
    """Any key to traktor key format converter.

    Args:
        parser (object): Picard parser object
        text (str): Key to convert

    Returns:
        str: Converted key value

    Tests:

    >>> key2traktor(None, '1A')
    'G#m'
    >>> key2traktor(None, '6m')
    'G#m'
    >>> key2traktor(None, 'A♭ Minor')
    'G#m'
    >>> key2traktor(None, 'A-Flat Minor')
    'G#m'
    >>> key2traktor(None, 'c#')
    'C#'
    >>> key2traktor(None, 'gBM')
    'F#m'
    >>> key2traktor(None, 'g♭M')
    'F#m'
    >>> key2traktor(None, '')
    ''
    """
    return _matcher(text, 'traktor')


register_script_function(key2camelot, name='key2camelot',
    documentation="""`$key2camelot(key)`

Returns the key string `key` in camelot key format.

The `key` argument can be entered in any of the supported formats, such as
'2B' (camelot), '6d' (open key), 'A♭ Minor' (standard with symbols),
'A-Flat Minor' (standard with text) or 'C#' (traktor).  If the `key` argument
is not recognized as one of the standard keys in the supported formats, then
an empty string will be returned.""")

register_script_function(key2openkey, name='key2openkey',
    documentation="""`$key2openkey(key)`

Returns the key string `key` in open key format.

The `key` argument can be entered in any of the supported formats, such as
'2B' (camelot), '6d' (open key), 'A♭ Minor' (standard with symbols),
'A-Flat Minor' (standard with text) or 'C#' (traktor).  If the `key` argument
is not recognized as one of the standard keys in the supported formats, then
an empty string will be returned.""")

register_script_function(key2standard, name='key2standard',
    documentation="""`$key2standard(key[,symbols])`

Returns the key string `key` in standard key format.  If the optional argument
`symbols` is set, then the '♭' and '#' symbols will be used, rather than
spelling out '-Flat' and '-Sharp'.

The `key` argument can be entered in any of the supported formats, such as
'2B' (camelot), '6d' (open key), 'A♭ Minor' (standard with symbols),
'A-Flat Minor' (standard with text) or 'C#' (traktor).  If the `key` argument
is not recognized as one of the standard keys in the supported formats, then
an empty string will be returned.""")

register_script_function(key2traktor, name='key2traktor',
    documentation="""`$key2traktor(key)`

Returns the key string `key` in traktor key format.

The `key` argument can be entered in any of the supported formats, such as
'2B' (camelot), '6d' (open key), 'A♭ Minor' (standard with symbols),
'A-Flat Minor' (standard with text) or 'C#' (traktor).  If the `key` argument
is not recognized as one of the standard keys in the supported formats, then
an empty string will be returned.""")

if __name__ == "__main__":
    import doctest
    doctest.testmod()
