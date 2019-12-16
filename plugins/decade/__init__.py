# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Philipp Wolfer
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

PLUGIN_NAME = 'Decade function'
PLUGIN_AUTHOR = 'Philipp Wolfer'
PLUGIN_DESCRIPTION = ('Add a $decade(date) function to get the decade '
                      'from a year. E.g. $decade(1994-04-05) will give "90s". '
                      'By default decades between 1920 and 2000 will be '
                      'shortened to two digits. You can disable this with '
                      'setting the second parameter to 0, e.g. '
                      '$decade(1994,0) will give "1990s".')
PLUGIN_VERSION = "1.0"
PLUGIN_API_VERSIONS = ["2.0", "2.1", "2.2", "2.3"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"


from picard.script import register_script_function


def decade(date, shorten=True):
    """
    >>> decade("1970-09-18")
    '70s'
    >>> decade("1994")
    '90s'
    >>> decade("1994-04")
    '90s'
    >>> decade("1994-04-05")
    '90s'
    >>> decade("1994-04-05", shorten=False)
    '1990s'
    >>> decade("1901")
    '1900s'
    >>> decade("1917-08-22")
    '1910s'
    >>> decade("1921-10-10")
    '20s'
    >>> decade("1770-12-16")
    '1770s'
    >>> decade("2017-07-20")
    '2010s'
    >>> decade("2020")
    '2020s'
    >>> decade("992")
    '990s'
    >>> decade("992-01")
    '990s'
    >>> decade("")
    ''
    >>> decade(None)
    ''
    >>> decade("foo")
    ''
    """
    try:
        year = int(date.split('-')[0])
    except (AttributeError, ValueError):
        return ""
    decade = year // 10 * 10
    if shorten and 1920 <= decade < 2000:
        decade -= 1900
    return "%ds" % decade


def script_decade(parser, value, shorten=True):
    return decade(value, shorten and shorten != '0')


register_script_function(script_decade, name="decade")
