# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2019-2023 Philipp Wolfer
# Copyright (C) 2020-2021 Laurent Monin
# Copyright (C) 2021 Bob Swift
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


import importlib
import logging
import os
import shutil
import sys
import unittest
from os import PathLike
from tempfile import mkdtemp, mkstemp
from types import ModuleType
from typing import Any, Callable, Optional
from unittest.mock import Mock, patch

import picard
from picard import config, log
from picard.i18n import setup_gettext
from picard.plugin import _PLUGIN_MODULE_PREFIX, _unregister_module_extensions
from picard.pluginmanager import PluginManager, plugin_dirs
from picard.releasegroup import ReleaseGroup
from PyQt5 import QtCore


class FakeThreadPool(QtCore.QObject):

    def start(self, runnable, priority):
        runnable.run()


class FakeTagger(QtCore.QObject):

    tagger_stats_changed = QtCore.pyqtSignal()

    def __init__(self):
        QtCore.QObject.__init__(self)
        QtCore.QObject.config = config
        QtCore.QObject.log = log
        self.tagger_stats_changed.connect(self.emit)
        self.exit_cleanup = []
        self.files = {}
        self.stopping = False
        self.thread_pool = FakeThreadPool()
        self.priority_thread_pool = FakeThreadPool()
        self.save_thread_pool = FakeThreadPool()
        self.mb_api = Mock()

    def register_cleanup(self, func: Callable[[], Any]) -> None:
        self.exit_cleanup.append(func)

    def run_cleanup(self) -> None:
        for f in self.exit_cleanup:
            f()

    def emit(self, *args) -> None:
        pass

    def get_release_group_by_id(self, rg_id: str) -> ReleaseGroup:
        return ReleaseGroup(rg_id)


class PluginTestCase(unittest.TestCase):
    def setUp(self) -> None:
        log.set_level(logging.DEBUG)
        setup_gettext(None, "C")
        self.tagger = FakeTagger()
        QtCore.QObject.tagger = self.tagger
        QtCore.QCoreApplication.instance = lambda: self.tagger
        self.addCleanup(self.tagger.run_cleanup)
        self.init_config()

        self.tmp_directory = self.mktmpdir()
        # return tmp_directory from pluginmanager.plugin_dirs
        self.patchers = [
            patch(
                "picard.pluginmanager.plugin_dirs", return_value=[self.tmp_directory]
            ).start(),
            patch(
                "picard.util.thread.to_main",
                side_effect=lambda func, *args, **kwargs: func(*args, **kwargs),
            ).start(),
        ]

    def tearDown(self) -> None:
        for patcher in self.patchers:
            patcher.stop()

    @staticmethod
    def init_config() -> None:
        fake_config = Mock()
        fake_config.setting = {}
        fake_config.persist = {}
        fake_config.profiles = {}
        # Make config object available for legacy use
        config.config = fake_config
        config.setting = fake_config.setting
        config.persist = fake_config.persist
        config.profiles = fake_config.profiles

    @staticmethod
    def set_config_values(
        setting: Optional[dict] = None,
        persist: Optional[dict] = None,
        profiles: Optional[dict] = None,
    ) -> None:
        if setting:
            for key, value in setting.items():
                config.config.setting[key] = value
        if persist:
            for key, value in persist.items():
                config.config.persist[key] = value
        if profiles:
            for key, value in profiles.items():
                config.config.profiles[key] = value

    def mktmpdir(self, ignore_errors: bool = False) -> None:
        tmpdir = mkdtemp(suffix=self.__class__.__name__)
        self.addCleanup(shutil.rmtree, tmpdir, ignore_errors=ignore_errors)
        return tmpdir

    def copy_file_tmp(self, filepath: str, ext: Optional[str] = None) -> str:
        fd, copy = mkstemp(suffix=ext)
        os.close(fd)
        self.addCleanup(self.remove_file_tmp, copy)
        shutil.copy(filepath, copy)
        return copy

    @staticmethod
    def remove_file_tmp(filepath: str) -> None:
        if os.path.isfile(filepath):
            os.unlink(filepath)

    def _test_plugin_install(self, name: str, module: str) -> ModuleType:
        self.unload_plugin(module)
        with self.assertRaises(ImportError):
            importlib.import_module(f"picard.plugins.{module}")

        pm = PluginManager(plugins_directory=self.tmp_directory)

        msg = f"install_plugin: {name} from {module}"
        pm.install_plugin(os.path.join("plugins", module))
        self.assertEqual(len(pm.plugins), 1, msg)
        self.assertEqual(pm.plugins[0].name, name, msg)

        self.set_config_values(setting={"enabled_plugins": [module]})

        # if module is properly loaded, this should work
        return importlib.import_module(f"picard.plugins.{module}")

    def unload_plugin(self, plugin_name: str) -> None:
        """for testing purposes"""
        _unregister_module_extensions(plugin_name)
        if hasattr(picard.plugins, plugin_name):
            delattr(picard.plugins, plugin_name)
        key = _PLUGIN_MODULE_PREFIX + plugin_name
        if key in sys.modules:
            del sys.modules[key]
