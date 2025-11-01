# -*- coding: utf-8 -*-

"""
Options page for the Shelves plugin.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Set

from PyQt5 import QtWidgets
from picard import config, log
from picard.config import BoolOption, ListOption, TextOption
from picard.ui.options import OptionsPage

from .constants import DEFAULT_SHELVES, ShelfConstants
from .ui_shelves_config import Ui_ShelvesConfigPage
from .utils import get_known_shelves
from .validators import validate_shelf_name


PLUGIN_NAME = "Shelves"


class ShelvesOptionsPage(OptionsPage):
    """
    Options page for the Shelves plugin.
    """

    NAME = "shelves"
    ui: Ui_ShelvesConfigPage
    TITLE = "Shelves"
    PARENT = "plugins"

    options = [
        ListOption(
            "setting",
            ShelfConstants.CONFIG_SHELVES_KEY,
            list(DEFAULT_SHELVES.values()),
        ),
        TextOption("setting", ShelfConstants.CONFIG_ALBUM_SHELF_KEY, ""),
        TextOption(
            "setting",
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_KEY,
            DEFAULT_SHELVES[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_KEY],
        ),
        TextOption(
            "setting",
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_KEY,
            DEFAULT_SHELVES[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_KEY],
        ),
        BoolOption("setting", ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY, True),
    ]

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        """
        Initialise the option page.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.ui = Ui_ShelvesConfigPage()
        self.ui.setupUi(self)

        # Connect signals
        self.ui.b_add_shelf.clicked.connect(self.add_shelf)
        self.ui.b_remove_shelf.clicked.connect(self.remove_shelf)
        self.ui.b_scan_4_shelves.clicked.connect(self.scan_music_directory)
        self.ui.shelf_list.itemSelectionChanged.connect(
            self.on_shelf_list_selection_changed
        )
        self.ui.workflow_enabled.stateChanged.connect(self.on_workflow_enabled_changed)
        self.ui.workflow_stage_1.currentTextChanged.connect(
            self.on_workflow_stage_changed
        )
        self.ui.workflow_stage_2.currentTextChanged.connect(
            self.on_workflow_stage_changed
        )

    def load(self) -> None:
        """Load already known shelves from config."""
        shelves = sorted(get_known_shelves())
        self.ui.shelf_list.clear()
        self.ui.shelf_list.addItems(shelves)

        self.ui.workflow_transitions.setEnabled(self.ui.workflow_enabled.isChecked())

        self.ui.workflow_stage_1.clear()
        self.ui.workflow_stage_1.addItems(shelves)
        try:
            self.ui.workflow_stage_1.setCurrentText(
                config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_KEY])  # type: ignore[index]
        except KeyError:
            self.ui.workflow_stage_1.setCurrentText(ShelfConstants.DEFAULT_INCOMING_SHELF)

        self.ui.workflow_stage_2.clear()
        self.ui.workflow_stage_2.addItems(shelves)
        try:
            self.ui.workflow_stage_2.setCurrentText(
                config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_KEY])  # type: ignore[index]
        except KeyError:
            self.ui.workflow_stage_2.setCurrentText(ShelfConstants.DEFAULT_SHELF)

        try:
            self.ui.workflow_enabled.setChecked(
                config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY])  # type: ignore[index]
        except KeyError:
            self.ui.workflow_enabled.setChecked(False)

        # Update preview with current values
        snippet = self.rebuild_rename_snippet()
        self.ui.naming_script_code.setPlainText(snippet)

    def save(self) -> None:
        """Save shelves list to config."""
        shelves = []
        for i in range(self.ui.shelf_list.count()):
            item_text = self.ui.shelf_list.item(i).text()
            shelves.append(item_text)

        config.setting[ShelfConstants.CONFIG_SHELVES_KEY] = shelves  # type: ignore[index]
        config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_KEY] = (  # type: ignore[index]
            self.ui.workflow_stage_1.currentText()
        )
        config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_KEY] = (  # type: ignore[index]
            self.ui.workflow_stage_2.currentText()
        )
        config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY] = (  # type: ignore[index]
            self.ui.workflow_enabled.isChecked()
        )

        log.debug("%s: Saved %d shelves to config", PLUGIN_NAME, len(shelves))

    def add_shelf(self) -> None:
        """Add a new shelf."""
        shelf_name, ok = QtWidgets.QInputDialog.getText(
            self, "Add Shelf", "Enter shelf name:"
        )

        if not ok or not shelf_name:
            return

        shelf_name = shelf_name.strip()
        is_valid, message = validate_shelf_name(shelf_name)

        if not is_valid:
            QtWidgets.QMessageBox.warning(self, "Invalid Name", message)
            return

        # Check if already exists
        existing_shelves = self._get_existing_shelves()
        if shelf_name in existing_shelves:
            QtWidgets.QMessageBox.information(
                self, "Already Exists", f"Shelf '{shelf_name}' already exists."
            )
            return

        self.ui.shelf_list.addItem(shelf_name)
        self.ui.workflow_stage_1.addItem(shelf_name)
        self.ui.workflow_stage_2.addItem(shelf_name)
        self.ui.shelf_list.sortItems()

    def remove_shelf(self) -> None:
        """Remove the selected shelf."""
        current_item = self.ui.shelf_list.currentItem()
        if not current_item:
            return

        shelf_name = current_item.text()

        # Warn if it's a workflow shelf
        if shelf_name in [
            self.ui.workflow_stage_1.currentText(),
            self.ui.workflow_stage_2.currentText(),
        ]:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Remove Workflow Shelf?",
                f"'{shelf_name}' is a workflow stage shelf. "
                "Are you sure you want to remove it?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            )
            if reply == QtWidgets.QMessageBox.No:
                return

        self.ui.shelf_list.takeItem(self.ui.shelf_list.row(current_item))

    def scan_music_directory(self) -> None:
        """Scan Picard's target directory for shelves."""
        try:
            music_dir_str = config.setting["move_files_to"]  # type: ignore[index]
        except KeyError:
            QtWidgets.QMessageBox.warning(
                self,
                "No Directory Configured",
                "Please configure 'Move files to' directory in Picard settings first.",
            )
            return

        music_dir = Path(music_dir_str)
        if not music_dir.exists():
            QtWidgets.QMessageBox.warning(
                self,
                "Directory Not Found",
                f"The directory '{music_dir}' does not exist.",
            )
            return

        try:
            shelves_found = [entry.name for entry in music_dir.iterdir() if entry.is_dir()]

            if not shelves_found:
                QtWidgets.QMessageBox.information(
                    self,
                    "No Shelves Found",
                    "No subdirectories found in the selected directory.",
                )
                return

            existing_shelves = self._get_existing_shelves()
            # added = 0

            for shelf in shelves_found:
                if shelf not in existing_shelves:
                    is_valid, _ = validate_shelf_name(shelf)
                    if is_valid:
                        self.ui.shelf_list.addItem(shelf)
                        self.ui.workflow_stage_1.addItem(shelf)
                        self.ui.workflow_stage_2.addItem(shelf)
                        # added += 1

            self.ui.shelf_list.sortItems()

            # if added > 0:
            #     QtWidgets.QMessageBox.information(
            #         self,
            #         "Scan Complete",
            #         f"Found {len(shelves_found)} directories.\nAdded {added} new shelf(s).",
            #     )

        except (OSError, PermissionError) as e:
            log.error("%s: Error scanning directory: %s", PLUGIN_NAME, e)
            QtWidgets.QMessageBox.critical(
                self, "Scan Error", f"Error scanning directory: {e}"
            )

    @staticmethod
    def rebuild_rename_snippet() -> str:
        """
        Build the rename snippet

        Returns:
            The complete rename snippet
        """

        # noinspection SpellCheckingInspection
        return """$set(_shelffolder,$shelf())
$set(_shelffolder,$if($not($eq(%_shelffolder%,)),%_shelffolder%/))

%_shelffolder%
$if2(%albumartist%,%artist%)/%album%/%title%"""


    def on_shelf_list_selection_changed(self) -> None:
        """ Enable / disable the remove button based on selection. """
        self.ui.b_remove_shelf.setEnabled(
            self.ui.shelf_list.currentItem() is not None
        )

    def on_workflow_enabled_changed(self) -> None:
        """ Handle workflow-enabled state change. """
        is_enabled = self.ui.workflow_enabled.isChecked()
        log.debug("%s: on_workflow_enabled_changed: %s", PLUGIN_NAME, is_enabled)
        self.ui.workflow_transitions.setEnabled(is_enabled)

        # Update preview when workflow is toggled
        snippet = self.rebuild_rename_snippet()
        self.ui.naming_script_code.setPlainText(snippet)

    def on_workflow_stage_changed(self) -> None:
        """Handle workflow stage change."""
        log.debug(
            "%s: on_workflow_stage_changed: stage_1='%s', stage_2='%s'",
            PLUGIN_NAME,
            self.ui.workflow_stage_1.currentText(),
            self.ui.workflow_stage_2.currentText(),
        )
        snippet = self.rebuild_rename_snippet()
        self.ui.naming_script_code.setPlainText(snippet)

    def _get_existing_shelves(self) -> Set[str]:
        """
        Get a set of currently listed shelves.

        Returns: Set of shelf names
        """
        return {
            self.ui.shelf_list.item(i).text()
            for i in range(self.ui.shelf_list.count())
        }
