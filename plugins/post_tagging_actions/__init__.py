# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 Giorgio Fontanive (twodoorcoupe)
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

PLUGIN_NAME = "Post Tagging Actions"
PLUGIN_AUTHOR = "Giorgio Fontanive"
PLUGIN_DESCRIPTION = """
This plugin lets you set up actions that run with a context menu click. 
An action consists in a command line executed for each album or each track along
with a few options to tweak the behaviour. 
This can be used to run external programs and pass some variables to it. 
"""
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["2.10", "2.11"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"
PLUGIN_USER_GUIDE_URL = "https://github.com/metabrainz/picard-plugins/tree/2.0/plugins/post_tagging_actions/docs/guide.md"

from picard.album import Album
from picard.track import Track
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.itemviews import BaseAction, register_album_action, register_track_action
from picard import log, config
from picard.const import sys
from picard.util import thread
from picard.script import parser

from .options_post_tagging_actions import Ui_PostTaggingActions
from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject

from collections import namedtuple
from queue import PriorityQueue
from threading import Thread
from concurrent import futures
from os import path, cpu_count
import re
import shlex
import subprocess  # nosec B404

# Additional special variables.
TRACK_SPECIAL_VARIABLES = {
    "filepath": lambda file: file,
    "folderpath": lambda file: path.dirname(file),  # pylint: disable=unnecessary-lambda
    "filename": lambda file: path.splitext(path.basename(file))[0],
    "filename_ext": lambda file: path.basename(file),  # pylint: disable=unnecessary-lambda
    "directory": lambda file: path.basename(path.dirname(file))
}
ALBUM_SPECIAL_VARIABLES = {
    "get_num_matched_tracks",
    "get_num_unmatched_files",
    "get_num_total_files",
    "get_num_unsaved_files",
    "is_complete",
    "is_modified"
}

# Settings.
CANCEL = "pta_cancel"
MAX_WORKERS = "pta_max_workers"
OPTIONS = ["pta_command", "pta_wait_for_exit", "pta_execute_for_tracks", "pta_refresh_tags"]

Options = namedtuple("Options", ("variables", *[option[4:] for option in OPTIONS]))
Action = namedtuple("Action", ("commands", "album", "options"))
PriorityAction = namedtuple("PriorityAction", ("priority", "counter", "action"))
action_queue = PriorityQueue()
variables_pattern = re.compile(r'%.*?%')


class ActionLoader:
    """Adds actions to the execution queue.

    Attributes:
        action_options (list): Stores the actions' information loaded from the options page.
        action_counter (int): The count of actions that have been added to the queue, used for priority.
    """

    def __init__(self):
        self.action_options = []
        self.action_counter = 0
        self.load_actions()

    def _create_options(self, command, *other_options):
        """Finds the variables in the command and adds the options to the action options list.
        """
        variables = [parser.normalize_tagname(variable[1:-1]) for variable in variables_pattern.findall(command)]
        command = variables_pattern.sub('{}', command)
        options = Options(variables, command, *other_options)
        self.action_options.append(options)

    def _create_action(self, priority, commands, album, options):
        """Adds an action with the given parameters to the execution queue.

        If the os is not windows, the command is split as suggested by the subprocess
        module documentation.
        """
        if not sys.IS_WIN:
            commands = [shlex.split(command) for command in commands]
        action = Action(commands, album, options)
        priority_action = PriorityAction(priority, self.action_counter, action)
        action_queue.put(priority_action)
        self.action_counter += 1

    def _replace_variables(self, variables, item):
        """Returns a list where each variable is replaced with its value.

        Item is either an album or a track. For track special variables,
        it uses the path of the first file of the given item.
        If the variable is not found anywhere, it remains as in the original text.
        """
        values = []
        album = item.album if isinstance(item, Track) else item
        first_file_path = next(item.iterfiles()).filename
        for variable in variables:
            if variable in ALBUM_SPECIAL_VARIABLES:
                values.append(getattr(album, variable)())
            elif variable in TRACK_SPECIAL_VARIABLES:
                values.append(TRACK_SPECIAL_VARIABLES[variable](first_file_path))
            else:
                values.append(item.metadata.get(variable, f"%{variable}%"))
        return values

    def add_actions(self, album, tracks):
        """Adds one action to the execution queue for each tuple in the action options list.

        Actions meant to be executed once for each track are considered as a single
        action. This way, the other options are more consistent.
        """
        for priority, options in enumerate(self.action_options):
            if options.execute_for_tracks:
                values_list = [self._replace_variables(options.variables, track) for track in tracks]
            else:
                values_list = [self._replace_variables(options.variables, album)]
            commands = [options.command.format(*values) for values in values_list]
            self._create_action(priority, commands, album, options)

    def load_actions(self):
        """Loads the information from the options and saves it in the action options list.

        This gets called when the plugin is loaded or when the user saves the options.
        """
        self.action_options = []
        option_tuples = zip(*[config.setting[name] for name in OPTIONS])
        for option_tuple in option_tuples:
            command = option_tuple[0]
            other_options = [eval(option) for option in option_tuple[1:]]  # nosec B307
            self._create_options(command, *other_options)


class ActionRunner:
    """Runs actions in the execution queue.

    Attributes:
        action_thread_pool (ThreadPoolExecutor): Pool used to run processes with the subprocess module.
        refresh_tags_pool (ThreadPoolExecutor): Pool used to reload tags from files and refresh albums.
        worker (Thread): Worker thread that picks actions from the execution queue.
    """

    def __init__(self):
        self.action_thread_pool = futures.ThreadPoolExecutor(config.setting[MAX_WORKERS])
        self.refresh_tags_pool = futures.ThreadPoolExecutor(1)
        self.worker = Thread(target = self._execute)
        self.worker.start()

        # This is used to register functions that run when the application is being closed.
        # action_runner.stop makes the background threads stop.
        QObject.tagger.register_cleanup(self.stop)

    def _refresh_tags(self, future_objects, album):
        """Reloads tags from the album's files and refreshes the album.

        First, it makes sure that the action has finished running. This is used for
        when an external process changes a file's tags.
        """
        futures.wait(future_objects, return_when = futures.ALL_COMPLETED)
        for file in album.iterfiles():
            file.set_pending()
            file.load(lambda file: None)
        thread.to_main(album.load, priority = True, refresh = True)

    def _run_process(self, command):
        """Runs the process and waits for it to finish.
        """
        process = subprocess.Popen(
            command,
            text = True,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE
        )  # nosec B603
        answer = process.communicate()
        if answer[0]:
            log.info("Action output:\n%s", answer[0])
        if answer[1]:
            log.error("Action error:\n%s", answer[1])

    def _execute(self):
        """Takes actions from the execution queue and runs them.

        If it finds an action with priority -1, the loop stops. When the loop
        stops, both ThreadPoolExecutors are shutdown.
        """
        while True:
            priority_action = action_queue.get()
            if priority_action.priority == -1:
                break
            next_action = priority_action.action
            commands = next_action.commands
            future_objects = {self.action_thread_pool.submit(self._run_process, command) for command in commands}

            if next_action.options.wait_for_exit:
                futures.wait(future_objects, return_when = futures.ALL_COMPLETED)
            if next_action.options.refresh_tags:
                self.refresh_tags_pool.submit(self._refresh_tags, future_objects, next_action.album)
            action_queue.task_done()

        self.action_thread_pool.shutdown(wait = False, cancel_futures = True)
        self.refresh_tags_pool.shutdown(wait = False, cancel_futures = True)

    def stop(self):
        """Makes the worker thread exit its loop.

        This gets called when Picard is closed. It waits for the processes that
        are still executing to finish before exiting.
        """
        if not config.setting[CANCEL]:
            action_queue.join()
        action_queue.put(PriorityAction(-1, -1, None))
        self.worker.join()


class ExecuteAlbumActions(BaseAction):

    NAME = "Run actions for highlighted albums"

    def callback(self, objs):
        albums = {obj for obj in objs if isinstance(obj, Album)}
        for album in albums:
            action_loader.add_actions(album, album.tracks)


class ExecuteTrackActions(BaseAction):

    NAME = "Run actions for highlighted tracks"

    def callback(self, objs):
        tracks = {obj for obj in objs if isinstance(obj, Track)}
        albums = {track.album for track in tracks}
        for album in albums:
            album_tracks = tracks.intersection(album.tracks)
            action_loader.add_actions(album, album_tracks)


class PostTaggingActionsOptions(OptionsPage):
    """Options page found under the "plugins" page.
    """

    NAME = "post_tagging_actions"
    TITLE = "Post Tagging Actions"
    PARENT = "plugins"

    action_options = [config.ListOption("setting", name, []) for name in OPTIONS]
    options = [
        config.BoolOption("setting", CANCEL, True),
        config.IntOption("setting", MAX_WORKERS, min(32, cpu_count() + 4)),
        *action_options
    ]

    def __init__(self, parent = None):
        super(PostTaggingActionsOptions, self).__init__(parent)
        self.ui = Ui_PostTaggingActions()
        self.ui.setupUi(self)
        self._reset_ui()

        header = self.ui.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        for column in range(1, header.count()):
            header.setSectionResizeMode(column, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        self.ui.add_file_path.clicked.connect(self._open_file_dialog)
        self.ui.add_action.clicked.connect(self._add_action_to_table)
        self.ui.remove_action.clicked.connect(self._remove_action_from_table)
        self.ui.up.clicked.connect(self._move_action_up)
        self.ui.down.clicked.connect(self._move_action_down)

        self.get_table_columns_values = [
            self.ui.action.text,
            self.ui.wait.isChecked,
            self.ui.tracks.isChecked,
            self.ui.refresh.isChecked
        ]

    def _open_file_dialog(self):
        """Adds the selected file's path to the command line text box.
        """
        file = QtWidgets.QFileDialog.getOpenFileName(self)[0]
        cursor_position = self.ui.action.cursorPosition()
        current_text = self.ui.action.text()
        if not sys.IS_WIN:
            file = shlex.quote(file)
        new_text = current_text[:cursor_position] + file + current_text[cursor_position:]
        self.ui.action.setText(new_text)

    def _reset_ui(self):
        self.ui.action.setText("")
        self.ui.wait.setChecked(False)
        self.ui.refresh.setChecked(False)
        self.ui.albums.setChecked(True)

    def _add_action_to_table(self):
        if not self.ui.action.text():
            return
        row_position = self.ui.table.rowCount()
        self.ui.table.insertRow(row_position)
        for column in range(self.ui.table.columnCount()):
            value = self.get_table_columns_values[column]()
            value = str(value)
            widget = QtWidgets.QTableWidgetItem(value)
            self.ui.table.setItem(row_position, column, widget)
        self._reset_ui()

    def _remove_action_from_table(self):
        current_row = self.ui.table.currentRow()
        if current_row != -1:
            self.ui.table.removeRow(current_row)

    def _move_action_up(self):
        current_row = self.ui.table.currentRow()
        new_row = current_row - 1
        if current_row > 0:
            self._swap_table_rows(current_row, new_row)
            self.ui.table.setCurrentCell(new_row, 0)

    def _move_action_down(self):
        current_row = self.ui.table.currentRow()
        new_row = current_row + 1
        if current_row < self.ui.table.rowCount() - 1:
            self._swap_table_rows(current_row, new_row)
            self.ui.table.setCurrentCell(new_row, 0)

    def _swap_table_rows(self, row1, row2):
        for column in range(self.ui.table.columnCount()):
            item1 = self.ui.table.takeItem(row1, column)
            item2 = self.ui.table.takeItem(row2, column)
            self.ui.table.setItem(row1, column, item2)
            self.ui.table.setItem(row2, column, item1)

    def load(self):
        """Puts the plugin's settings into the actions table.
        """
        settings = zip(*[config.setting[name] for name in OPTIONS])
        for row, values in enumerate(settings):
            self.ui.table.insertRow(row)
            for column in range(self.ui.table.columnCount()):
                widget = QtWidgets.QTableWidgetItem(values[column])
                self.ui.table.setItem(row, column, widget)
        self.ui.cancel.setChecked(config.setting[CANCEL])
        self.ui.max_workers.setValue(config.setting[MAX_WORKERS])

    def save(self):
        """Saves the actions table items in the settings.
        """
        settings = []
        for column in range(self.ui.table.columnCount()):
            settings.append([])
            for row in range(self.ui.table.rowCount()):
                setting = self.ui.table.item(row, column).text()
                settings[column].append(setting)
            config.setting[OPTIONS[column]] = settings[column]
        config.setting[CANCEL] = self.ui.cancel.isChecked()
        config.setting[MAX_WORKERS] = self.ui.max_workers.value()
        action_loader.load_actions()


action_loader = ActionLoader()
action_runner = ActionRunner()
register_album_action(ExecuteAlbumActions())
register_track_action(ExecuteTrackActions())
register_options_page(PostTaggingActionsOptions)
