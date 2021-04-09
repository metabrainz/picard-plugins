# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Philipp Wolfer
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

PLUGIN_NAME = 'Release tag aggregation functions'
PLUGIN_AUTHOR = 'Philipp Wolfer'
PLUGIN_DESCRIPTION = ('Add functions to aggregate tags on a release:'
                      '<ul>'
                      '<li>$album_all(name)</li>'
                      '<li>‎$album_avg(name, precision=2)</li>'
                      '<li>‎$album_max(name, precision=2)</li>'
                      '<li>‎$album_min(name, precision=2)</li>'
                      '<li>‎$album_mode(name)</li>'
                      '<li>‎$album_distinct(name, separator=; )</li>'
                      '<li>‎$album_multi_avg(name, precision=2)</li>'
                      '<li>‎$album_multi_max(name, precision=2)</li>'
                      '<li>‎$album_multi_min(name, precision=2)</li>'
                      '<li>‎$album_multi_mode(name)</li>'
                      '<li>‎$album_multi_distinct(name, separator=; )</li>'
                      '</ul>'
                      '<b>The functions work only in file naming scripts and '
                      'the files should either be part of a release or cluster!</b>')
PLUGIN_VERSION = "0.4"
PLUGIN_API_VERSIONS = ["2.5", "2.6"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from functools import partial

from picard.cluster import Cluster
from picard.metadata import MULTI_VALUED_JOINER
from picard.script import script_function
from picard.script.parser import normalize_tagname


def get_parent_release(file):
    if file.parent:
        if isinstance(file.parent, Cluster):
            return file.parent
        elif hasattr(file.parent, 'album') and file.parent.album:
            return file.parent.album
    return None


def iter_release_values(name, file):
    parent = get_parent_release(file)
    if parent:
        for file in parent.iterfiles(save=True):
            yield file.metadata.get(name, '')
    else:
        yield file.metadata.get(name, '')


def iter_release_values_multi(name, file):
    parent = get_parent_release(file)
    if parent:
        for file in parent.iterfiles(save=True):
            yield from file.metadata.getall(name)
    else:
        yield from file.metadata.getall(name)


def try_iter_numeric(values, skip_non_numeric=False):
    for value in values:
        # First try treating the value as an integer, if this fails try float
        try:
            yield int(value)
        except (TypeError, ValueError):
            try:
                yield float(value)
            except (TypeError, ValueError):
                if not skip_non_numeric:
                    yield value


def aggregate_release_tags(parser, name, aggregate_func, multi=False):
    name = normalize_tagname(name)
    file = parser.file
    if file:
        iter_func = iter_release_values_multi if multi else iter_release_values
        return aggregate_func(iter_func(name, file))
    else:  # Nothing to aggregate, return base value
        return parser.context.get(name, '')


def format_number(value, precision=2):
    try:
        precision = int(precision)
    except (TypeError, ValueError):
        precision = 0
    if isinstance(value, int):
        return str(value)
    elif isinstance(value, float):
        fmt = '{:.' + str(precision) + 'f}'
        return fmt.format(value)
    elif not value:
        return ''
    else:
        return str(value)


def mode(values):
    """Returns the mode, the value with the most occurrences, from values."""
    l = list(values)
    if not l:
        return ''
    return max(set(l), key=l.count)


def average(values, precision=2):
    """Returns the arithmetic average of all numeric elements in values.

    Non-numeric elements are ignored.
    """
    numbers = list(try_iter_numeric(values, skip_non_numeric=True))
    if not numbers:
        return ''
    return format_number(sum(numbers) / len(numbers), precision=precision)


def natsort_min(values, precision=2):
    """Returns the smallest value from values, treats numeric strings as numbers."""
    return format_number(max(try_iter_numeric(values)), precision=precision)


def natsort_max(values, precision=2):
    """Returns the largest value from values, treats numeric strings as numbers."""
    return format_number(max(try_iter_numeric(values)), precision=precision)


def distinct(values, separator=MULTI_VALUED_JOINER):
    return separator.join(set(values))


@script_function(documentation="""`$album_all(name)`

Returns the value of the tag name if all files on the album have the same
value for this tag. Otherwise returns empty.
**Only works in File Naming scripts.**""")
def func_album_all(parser, name):
    def aggregate_func(values):
        common_value = ''
        for value in values:
            if not common_value:
                common_value = value
            if common_value != value:
                return ''
        return common_value

    return aggregate_release_tags(parser, name, aggregate_func)


@script_function(documentation="""`$album_mode(name)`

Returns the value with the most occurrences over all the files on the release for the given tag.
**Only works in File Naming scripts.**""")
def func_album_mode(parser, name):
    return aggregate_release_tags(parser, name, mode)


@script_function(documentation="""`$album_multi_mode(name)`

Returns the value with the most occurrences over all the files on the release for the given tag.
Similar to $album_mode(), but considers each value of multi-value tags separately.
**Only works in File Naming scripts.**""")
def func_album_multi_mode(parser, name):
    return aggregate_release_tags(parser, name, mode, multi=True)


@script_function(documentation="""`$album_min(name, precision=2)`

Returns the minimum value of all the files on the release for the given tag.
**Only works in File Naming scripts.**""")
def func_album_min(parser, name, precision="2"):
    aggregate_func = partial(natsort_min, precision=precision)
    return aggregate_release_tags(parser, name, aggregate_func)


@script_function(documentation="""`$album_multi_min(name, precision=2)`

Returns the minimum value of all the files on the release for the given tag.
Similar to $album_min(), but considers each value of multi-value tags separately.
**Only works in File Naming scripts.**""")
def releasetag_multi_min(parser, name, precision="2"):
    aggregate_func = partial(natsort_min, precision=precision)
    return aggregate_release_tags(parser, name, aggregate_func, multi=True)


@script_function(documentation="""`$album_max(name, precision=2)`

Returns the maximum value of all the files on the release for the given tag.
**Only works in File Naming scripts.**""")
def func_album_max(parser, name, precision="2"):
    aggregate_func = partial(natsort_max, precision=precision)
    return aggregate_release_tags(parser, name, aggregate_func)


@script_function(documentation="""`$album_multi_max(name, precision=2)`

Returns the maximum value of all the files on the release for the given tag.
Similar to $album_max(), but considers each value of multi-value tags separately.
**Only works in File Naming scripts.**""")
def releasetag_multi_max(parser, name, precision="2"):
    aggregate_func = partial(natsort_max, precision=precision)
    return aggregate_release_tags(parser, name, aggregate_func, multi=True)


@script_function(documentation="""`$album_avg(name, precision=2)`

Returns the arithmetical average value of all the files on the release for the given tag.
Non-numeric values are ignored. Returns empty if no numeric value is present.
**Only works in File Naming scripts.**""")
def func_album_avg(parser, name, precision="2"):
    aggregate_func = partial(average, precision=precision)
    return aggregate_release_tags(parser, name, aggregate_func)


@script_function(documentation="""`$album_multi_avg(name, precision=2)`

Returns the arithmetical average value of all the files on the release for the given tag.
Non-numeric values are ignored. Returns empty if no numeric value is present.
Similar to $album_avg(), but considers each value of multi-value tags separately.
**Only works in File Naming scripts.**""")
def func_album_multi_avg(parser, name, precision="2"):
    aggregate_func = partial(average, precision=precision)
    return aggregate_release_tags(parser, name, aggregate_func, multi=True)


@script_function(documentation="""`$album_distinct(name, separator=; )`

Returns a multi-value tag with all distinct values of tag across all the files on the release.
**Only works in File Naming scripts.**""")
def func_album_distinct(parser, name, separator=MULTI_VALUED_JOINER):
    aggregate_func = partial(distinct, separator=separator)
    return aggregate_release_tags(parser, name, aggregate_func)


@script_function(documentation="""`$album_multi_distinct(name, separator=; )`

Returns a multi-value tag with all distinct values of tag across all the files on the release.
Similar to $album_distinct(), but considers each value of multi-value tags separately.
**Only works in File Naming scripts.**""")
def func_album_multi_distinct(parser, name, separator=MULTI_VALUED_JOINER):
    aggregate_func = partial(distinct, separator=separator)
    return aggregate_release_tags(parser, name, aggregate_func, multi=True)
