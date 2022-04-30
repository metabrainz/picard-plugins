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

# "Persistent variables display" context is based on the code from
# the "View Script Variables" plugin.

PLUGIN_NAME = 'Persistent Variables'
PLUGIN_AUTHOR = 'Bob Swift (rdswift)'
PLUGIN_DESCRIPTION = '''
<p>
This plugin provides the ability to store and retrieve script variables that persist across tracks and albums.
This allows things like finding and storing the earliest recording date of all of the tracks on an album.
</p><p>
There are two types of persistent variables maintained - album variables and session variables. Album variables
persist across all tracks on an album.  Each album's information is stored separately, and is reset when the
album is refreshed. The information is cleared when an album is removed.  Session variables persist across all
albums and tracks, and are cleared when Picard is shut down or restarted.
</p><p>
This plugin adds eight new scripting functions to allow management of persistent script variables:
<ul>
<li>$set_a(name,value) : Sets the album persistent variable name to value.</li>
<li>$unset_a(name) : Unsets the album persistent variable name.</li>
<li>$get_a(name) : Gets the album persistent variable name.</li>
<li>$clear_a() : Clears all album persistent variables.</li>
<li>$set_s(name,value) : Sets the session persistent variable name to value.</li>
<li>$unset_s(name) : Unsets the session persistent variable name.</li>
<li>$get_s(name) : Gets the session persistent variable name.</li>
<li>$clear_s() : Clears all session persistent variables.</li>
</ul>
</p><p>
Please see the <a href="https://github.com/rdswift/picard-plugins/blob/2.0_RDS_Plugins/plugins/persistent_variables/docs/README.md">user guide</a> on GitHub for more information.
</p>
'''
PLUGIN_VERSION = '1.1'
PLUGIN_API_VERSIONS = ['2.0', '2.1', '2.2', '2.3', '2.4', '2.6', '2.7']
PLUGIN_LICENSE = 'GPL-2.0-or-later'
PLUGIN_LICENSE_URL = 'https://www.gnu.org/licenses/gpl-2.0.html'

PLUGIN_USER_GUIDE_URL = 'https://github.com/rdswift/picard-plugins/blob/2.0_RDS_Plugins/plugins/persistent_variables/docs/README.md'

from PyQt5 import QtWidgets

from picard import log
from picard.album import (
    Album,
    register_album_post_removal_processor,
)
from picard.file import File
from picard.metadata import register_album_metadata_processor
from picard.plugin import PluginPriority
from picard.plugins.persistent_variables.ui_variables_dialog import (
    Ui_VariablesDialog,
)
from picard.script import register_script_function
from picard.script.parser import normalize_tagname
from picard.track import Track

from picard.ui.itemviews import (
    BaseAction,
    register_album_action,
    register_file_action,
    register_track_action,
)


class PersistentVariables:
    album_variables = {}
    session_variables = {}

    @classmethod
    def clear_album_vars(cls, album):
        if album:
            cls.album_variables[album] = {}

    @classmethod
    def set_album_var(cls, album, key, value):
        if album:
            if album not in cls.album_variables:
                cls.clear_album_vars(album)
            if key:
                cls.album_variables[album][key] = value

    @classmethod
    def unset_album_var(cls, album, key):
        if album and album in cls.album_variables:
            cls.album_variables[album].pop(key, None)

    @classmethod
    def unset_album_dict(cls, album):
        if album:
            cls.album_variables.pop(album, None)

    @classmethod
    def get_album_var(cls, album, key):
        if album in cls.album_variables:
            return cls.album_variables[album][key] if key in cls.album_variables[album] else ""
        return ""

    @classmethod
    def clear_session_vars(cls):
        cls.session_variables = {}

    @classmethod
    def set_session_var(cls, key, value):
        if key:
            cls.session_variables[key] = value

    @classmethod
    def unset_session_var(cls, key):
        cls.session_variables.pop(key, None)

    @classmethod
    def get_session_var(cls, key):
        return cls.session_variables[key] if key in cls.session_variables else ""

    @classmethod
    def get_album_dict(cls, album):
        if album and album in cls.album_variables:
            return cls.album_variables[album]
        return {}

    @classmethod
    def get_session_dict(cls):
        return cls.session_variables


def _get_album_id(parser):
    file = parser.file
    if file:
        if file.parent and hasattr(file.parent, 'album') and file.parent.album:
            return str(file.parent.album.id)
        else:
            return ""
    # Fall back to parser context to allow processing on albums newly retrieved from MusicBrainz
    return parser.context['musicbrainz_albumid']


def func_set_s(parser, name, value):
    if value:
        PersistentVariables.set_session_var(normalize_tagname(name), value)
    else:
        func_unset_s(parser, name)
    return ""


def func_unset_s(parser, name):
    PersistentVariables.unset_session_var(normalize_tagname(name))
    return ""


def func_get_s(parser, name):
    return PersistentVariables.get_session_var(normalize_tagname(name))


def func_clear_s(parser):
    PersistentVariables.clear_session_vars()
    return ""


def func_unset_a(parser, name):
    album_id = _get_album_id(parser)
    log.debug("{0}: Unsetting album '{1}' variable '{2}'".format(PLUGIN_NAME, album_id, normalize_tagname(name),))
    if album_id:
        PersistentVariables.unset_album_var(album_id, normalize_tagname(name))
    return ""


def func_set_a(parser, name, value):
    album_id = _get_album_id(parser)
    log.debug("{0}: Setting album '{1}' persistent variable '{2}' to '{3}'".format(PLUGIN_NAME, album_id, normalize_tagname(name), value,))
    if album_id:
        PersistentVariables.set_album_var(album_id, normalize_tagname(name), value)
    return ""


def func_get_a(parser, name):
    album_id = _get_album_id(parser)
    log.debug("{0}: Getting album '{1}' persistent variable '{2}'".format(PLUGIN_NAME, album_id, normalize_tagname(name),))
    if album_id:
        return PersistentVariables.get_album_var(album_id, normalize_tagname(name))
    return ""


def func_clear_a(parser):
    album_id = _get_album_id(parser)
    log.debug("{0}: Clearing album '{1}' persistent variables dictionary".format(PLUGIN_NAME, album_id,))
    if album_id:
        PersistentVariables.clear_album_vars(album_id)
    return ""


def initialize_album_dict(album, album_metadata, release_metadata):
    album_id = str(album.id)
    log.debug("{0}: Initializing album '{1}' persistent variables dictionary".format(PLUGIN_NAME, album_id,))
    PersistentVariables.clear_album_vars(album_id)


def destroy_album_dict(album):
    album_id = str(album.id)
    log.debug("{0}: Destroying album '{1}' persistent variables dictionary".format(PLUGIN_NAME, album_id,))
    PersistentVariables.unset_album_dict(album_id)


class ViewVariables(BaseAction):
    NAME = 'View persistent variables'

    def callback(self, objs):
        obj = objs[0]
        files = self.tagger.get_files_from_objects(objs)
        if files:
            obj = files[0]
        dialog = ViewVariablesDialog(obj)
        dialog.exec_()


class ViewVariablesDialog(QtWidgets.QDialog):

    def __init__(self, obj, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.ui = Ui_VariablesDialog()
        self.ui.setupUi(self)
        self.ui.buttonBox.accepted.connect(self.accept)
        self.album_id = ""
        self.setWindowTitle("Persistent Variables")
        if isinstance(obj, Album):
            self.album_id = str(obj.id)
        if isinstance(obj, File):
            if obj.parent and hasattr(obj.parent, 'album') and obj.parent.album:
                self.album_id = str(obj.parent.album.id)
        elif isinstance(obj, Track):
            if obj.album:
                self.album_id = str(obj.album.id)
        album_dict = PersistentVariables.get_album_dict(self.album_id)
        album_count = len(album_dict)
        session_dict = PersistentVariables.get_session_dict()
        session_count = len(session_dict)

        table = self.ui.metadata_table
        key_example, value_example = self.get_table_items(table, 0)
        self.key_flags = key_example.flags()
        self.value_flags = value_example.flags()
        table.setRowCount(album_count + session_count + 2)
        i = 0
        self.add_separator_row(table, i, "Album Variables", album_count)
        i += 1
        for key in sorted(album_dict.keys()):
            key_item, value_item = self.get_table_items(table, i)
            key_item.setText(key)
            value_item.setText(album_dict[key])
            i += 1
        self.add_separator_row(table, i, "Session Variables", session_count)
        i += 1
        for key in sorted(session_dict.keys()):
            key_item, value_item = self.get_table_items(table, i)
            key_item.setText(key)
            value_item.setText(session_dict[key])
            i += 1

    def add_separator_row(self, table, i, title, count):
        key_item, value_item = self.get_table_items(table, i)
        font = key_item.font()
        font.setBold(True)
        key_item.setFont(font)
        key_item.setText(title)
        value_item.setText("{0} item{1}".format(count, "" if count == 1 else "s",))

    def get_table_items(self, table, i):
        key_item = table.item(i, 0)
        value_item = table.item(i, 1)
        if not key_item:
            key_item = QtWidgets.QTableWidgetItem()
            key_item.setFlags(self.key_flags)
            table.setItem(i, 0, key_item)
        if not value_item:
            value_item = QtWidgets.QTableWidgetItem()
            value_item.setFlags(self.value_flags)
            table.setItem(i, 1, value_item)
        return key_item, value_item

viewer = ViewVariables()


# Register the new functions
register_script_function(func_set_a, name='set_a',
    documentation="""`$set_a(name,value)`

Sets the album persistent variable `name` to `value`.""")

register_script_function(func_unset_a, name='unset_a',
    documentation="""`$unset_a(name)`

Unsets the album persistent variable `name`.""")

register_script_function(func_get_a, name='get_a',
    documentation="""`$get_a(name)`

Gets the album persistent variable `name`.""")

register_script_function(func_clear_a, name='clear_a',
    documentation="""`$clear_a()`

Clears all album persistent variables.""")

register_script_function(func_set_s, name='set_s',
    documentation="""`$set_s(name,value)`

Sets the session persistent variable `name` to `value`.""")

register_script_function(func_unset_s, name='unset_s',
    documentation="""`$unset_s(name)`

Unsets the session persistent variable `name`.""")

register_script_function(func_get_s, name='get_s',
    documentation="""`$get_s(name)`

Gets the session persistent variable `name`.""")

register_script_function(func_clear_s, name='clear_s',
    documentation="""`$clear_s()`

Clears all session persistent variables.""")


# Register the processers
register_album_metadata_processor(initialize_album_dict, priority=PluginPriority.HIGH)
register_album_post_removal_processor(destroy_album_dict)


# Register context actions
register_file_action(viewer)
register_track_action(viewer)
register_album_action(viewer)
