import os
from typing import List, Optional

from PyQt5 import uic, QtWidgets, QtCore
from PyQt5.QtWidgets import QHeaderView
from picard import log
from picard.config import Option
from picard.ui.options import OptionsPage

from . import PLUGIN_NAME
from .constants import DEFAULT_TAGS, DEFAULT_CHAR_MAPPING

class ReplaceUnwantedCharactersOptionsPage(OptionsPage):
    NAME = "replace_unwanted_characters"
    TITLE = "Replace Unwanted Characters"
    PARENT = "plugins"

    options = [
        Option("setting", "replace_unwanted_characters_filter_tags",
               DEFAULT_TAGS),
        Option("setting", "replace_unwanted_characters_char_table",
               DEFAULT_CHAR_MAPPING),
        Option("setting", "replace_unwanted_characters_per_tag_tables",
               {}),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), 'replace_unwanted_characters_config.ui')
        uic.loadUi(ui_file, self)

        # header resize modes
        if hasattr(self, "filter_tags_table"):
            self.filter_tags_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.filter_tags_table.itemChanged.connect(self.on_filter_tags_changed)
            log.debug(f"{PLUGIN_NAME}: Connected filter_tags_table itemChanged signal")
        if hasattr(self, "replacement_table"):
            self.replacement_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.replacement_table.cellChanged.connect(self.on_mapping_changed)
            log.debug(f"{PLUGIN_NAME}: Connected replacement_table itemChanged signal")
        if hasattr(self, "per_tag_table"):
            header = self.per_tag_table.horizontalHeader()
            cols = self.per_tag_table.columnCount()
            for idx in range(cols):
                if idx == cols - 1:
                    header.setSectionResizeMode(idx, QHeaderView.Stretch)
                else:
                    header.setSectionResizeMode(idx, QHeaderView.ResizeToContents)

        # filter tag add/remove buttons
        if hasattr(self, "filter_tags_table"):
            if hasattr(self, "add_filter_tag_button"):
                self.add_filter_tag_button.clicked.connect(self.add_tag_row)
            if hasattr(self, "remove_filter_tag_button"):
                self.remove_filter_tag_button.clicked.connect(self.remove_tags_row)

        # replacement table buttons
        if hasattr(self, "add_row_button"):
            self.add_row_button.clicked.connect(self.add_mapping_row)
        if hasattr(self, "remove_row_button"):
            self.remove_row_button.clicked.connect(self.remove_mapping_rows)

        # in-memory per-tag selections:
        # maps tag -> set(enabled_keys)
        self._per_tag_selection = {}
        # saved selection used when Use Default is toggled on (to restore later)
        self._per_tag_saved = {}
        # per-tag active state (Is Active checkbox)
        self._per_tag_active = {}
        # per-tag default state (Use Default checkbox)
        self._per_tag_default = {}

    # ---------- filter tags table helpers ----------
    def add_tag_row(self):
        if not hasattr(self, "filter_tags_table"):
            return
        row = self.filter_tags_table.rowCount()
        self.filter_tags_table.insertRow(row)
        self.filter_tags_table.setItem(row, 0, QtWidgets.QTableWidgetItem(""))

    def remove_tags_row(self):
        if not hasattr(self, "filter_tags_table"):
            return

        # collect selected rows from filter_tags_table (may contain duplicates)
        rows = set(index.row() for index in self.filter_tags_table.selectedIndexes())
        if not rows:
            return

        # remove rows from the bottom up to keep indices valid and clear per-tag state
        for row in sorted(rows, reverse=True):
            item = self.filter_tags_table.item(row, 0)
            if item:
                tag = item.text()
                self._per_tag_selection.pop(tag, None)
                self._per_tag_saved.pop(tag, None)
                self._per_tag_active.pop(tag, None)
                self._per_tag_default.pop(tag, None)
            self.filter_tags_table.removeRow(row)

        # rebuild per-tag table to reflect removed tags
        self.rebuild_per_tag_table()

    def _refresh_per_tag_data(self):
        rows = set(index.row() for index in self.filter_tags_table.selectedIndexes())
        for row in sorted(rows, reverse=True):
            # remove selection state for tag if present
            item = self.filter_tags_table.item(row, 0)
            if item:
                tag = item.text()
                self._per_tag_selection.pop(tag, None)
                self._per_tag_saved.pop(tag, None)
                self._per_tag_active.pop(tag, None)
                self._per_tag_default.pop(tag, None)
            self.filter_tags_table.removeRow(row)

    def on_filter_tags_changed(self):
        # user edited a row - rebuild the per-tag table preserving selections where possible
        self.rebuild_per_tag_table()

    # ---------- default replacement table helpers ----------
    def add_mapping_row(self):
        if not hasattr(self, "replacement_table"):
            return
        row = self.replacement_table.rowCount()
        self.replacement_table.insertRow(row)
        self.replacement_table.setItem(row, 0, QtWidgets.QTableWidgetItem(""))
        self.replacement_table.setItem(row, 1, QtWidgets.QTableWidgetItem(""))

    def remove_mapping_rows(self):
        if not hasattr(self, "replacement_table"):
            return

        # collect selected rows from replacement_table (may contain duplicates)
        rows = set(index.row() for index in self.replacement_table.selectedIndexes())
        if not rows:
            return

        # remove rows from the bottom up to keep indices valid
        for row in sorted(rows, reverse=True):
            self.replacement_table.removeRow(row)

        # update in-memory per-tag selections to remove keys that no longer exist
        remaining_keys = set(self._current_default_keys())
        for tag in list(self._per_tag_selection.keys()):
            self._per_tag_selection[tag] = self._per_tag_selection[tag] & remaining_keys
            self._per_tag_saved[tag] = self._per_tag_saved.get(tag, set()) & remaining_keys

        # rebuild per-tag table to reflect changes
        self.rebuild_per_tag_table()

    def on_mapping_changed(self):
        # user edited a row - rebuild the per-tag table preserving selections where possible
        self.rebuild_per_tag_table()

    def _current_default_keys(self):
        keys = []
        if hasattr(self, "replacement_table"):
            for row in range(self.replacement_table.rowCount()):
                item = self.replacement_table.item(row, 0)
                if item:
                    k = item.text()
                    if k:
                        keys.append(k)
        return keys

    # ---------- per-tag table creation and updates ----------
    def rebuild_per_tag_table(self):
        if not hasattr(self, "per_tag_table"):
            return

        tags = self._get_configured_filter_tags()

        self.per_tag_table.setRowCount(0)
        # convert available keys to a set for containment checks
        all_keys = set(self._current_default_keys())

        per_tag_saved = self.config.setting["replace_unwanted_characters_per_tag_tables"]

        for tag in tags:
            row = self.per_tag_table.rowCount()
            self.per_tag_table.insertRow(row)
            self.per_tag_table.setRowHeight(row, self.per_tag_table.fontMetrics().height() + 10)
            explicit = tag in per_tag_saved
            log.debug(f"{PLUGIN_NAME}: Building per-tag table row for tag '{tag}': explicit={explicit}")

            # UI widget stuff
            # Is Active checkbox
            active_chk = QtWidgets.QCheckBox()
            active_chk_container = QtWidgets.QWidget()
            active_chk_layout = QtWidgets.QHBoxLayout(active_chk_container)
            active_chk_layout.addWidget(active_chk)
            # noinspection PyUnresolvedReferences
            active_chk_layout.setAlignment(QtCore.Qt.AlignCenter)
            active_chk_layout.setContentsMargins(0, 0, 0, 0)
            self.per_tag_table.setCellWidget(row, 0, active_chk_container)

            # Tag name item
            tag_item = QtWidgets.QTableWidgetItem(tag)
            # noinspection PyUnresolvedReferences
            tag_item.setFlags(tag_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.per_tag_table.setItem(row, 1, tag_item)

            # Use default checkbox
            default_chk = QtWidgets.QCheckBox()
            default_chk_container = QtWidgets.QWidget()
            default_chk_layout = QtWidgets.QHBoxLayout(default_chk_container)
            default_chk_layout.addWidget(default_chk)
            # noinspection PyUnresolvedReferences
            default_chk_layout.setAlignment(QtCore.Qt.AlignCenter)
            default_chk_layout.setContentsMargins(0, 0, 0, 0)
            self.per_tag_table.setCellWidget(row, 2, default_chk_container)

            # Store selection and active state (support both legacy list and new dict)
            log.debug(f"{PLUGIN_NAME}: Restoring saved selection for tag'{tag}', explicit={explicit}")
            if explicit:
                entry = per_tag_saved.get(tag)
                keys_list = entry.get("keys", [])
                active = entry.get("active", True)
                default = entry.get("default", True)
                # if using default, set selection to all keys
                if default:
                    keys_list = all_keys
                else:
                    # prune saved keys to current available keys
                    keys_list = [k for k in keys_list if k in all_keys]
                self._per_tag_selection[tag] = set(keys_list)
                self._per_tag_saved[tag] = set(keys_list)
                self._per_tag_active[tag] = active
                self._per_tag_default[tag] = default
            else:
                self._per_tag_selection[tag] = set(all_keys)
                self._per_tag_saved[tag] = self._per_tag_selection[tag].copy()
                self._per_tag_active[tag] = True
                self._per_tag_default[tag] = True

            active_chk.setChecked(self._per_tag_active[tag])
            default_chk.setChecked(self._per_tag_default[tag])

            # Mapping button
            btn = QtWidgets.QPushButton()
            self.per_tag_table.setCellWidget(row, 3, btn)
            self._update_mapping_button_text(btn, tag)
            btn.setEnabled(not default_chk.isChecked())

            # Connect signals
            default_chk.toggled.connect(self._make_use_default_handler(tag, btn))
            btn.clicked.connect(self._make_mapping_button_handler(tag, btn))
            # update in-memory active flag when toggled
            active_chk.toggled.connect(lambda checked, t=tag: self._per_tag_active.__setitem__(t, checked))

    def _is_use_default_for_tag(self, tag):
        """Return True if the 'Use Default' checkbox for tag is checked."""
        if not hasattr(self, "per_tag_table"):
            return False
        for row in range(self.per_tag_table.rowCount()):
            item = self.per_tag_table.item(row, 1)  # tag is in column 1
            if item and item.text() == tag:
                widget = self.per_tag_table.cellWidget(row, 2)  # Use Default checkbox is in column 2
                if widget:
                    layout = widget.layout()
                    if layout and layout.count() > 0:
                        chk = layout.itemAt(0).widget()
                        if isinstance(chk, QtWidgets.QCheckBox):
                            return chk.isChecked()
        return False

    def _update_mapping_button_text(self, button, tag):
        """
        Update the text of the mapping button to reflect the current selection of mapped characters for a given tag.
        Shows an indicator when 'Use Default' is active.
        """
        log.debug(f"{PLUGIN_NAME}: Updating mapping button text for tag '{tag}'")

        selected_keys = sorted(list(self._per_tag_selection.get(tag, set())))
        log.debug(f"{PLUGIN_NAME}: Selected keys for tag '{tag}': {selected_keys}")
        num_selected = len(selected_keys)

        if num_selected == 0:
            button.setText("none selected")
            return

        # Create a preview string of selected characters
        preview_str = " ".join(selected_keys)

        # Truncate the preview string if it's too long
        preview_limit = 20  # Max length of the character preview
        if len(preview_str) > preview_limit:
            # Truncate the string at the last space before the limit, if possible
            truncated = preview_str[:preview_limit]
            if ' ' in truncated:
                truncated = truncated.rsplit(' ', 1)[0]
            preview_str = truncated + "…"

        log.debug(f"{PLUGIN_NAME}: Mapping button text for tag '{tag}': {preview_str}")
        button.setText(f"{preview_str}")

    def _make_mapping_button_handler(self, tag, button):
        """
        Factory method that creates a handler function for the mapping button of a specific tag.
        """

        def on_button_clicked():
            all_keys = self._current_default_keys()
            current_selection = self._per_tag_selection.get(tag, set())

            dialog = MultiSelectDialog(self, f"Edit Mapping for '{tag}'", all_keys, current_selection)
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                new_selection = dialog.get_selected_items()
                self._per_tag_selection[tag] = new_selection
                self._per_tag_saved[tag] = new_selection.copy()
                self._update_mapping_button_text(button, tag)

        return on_button_clicked

    def on_default_table_changed(self, *args):
        self.rebuild_per_tag_table()

    def _make_use_default_handler(self, tag, button):
        """
        Creates a handler function for the 'use default' checkbox for a given tag.

        When the checkbox is toggled, this handler updates the per-tag selection state:
        - If checked, saves the current selection, selects all available keys, and disables the mapping button.
        - If unchecked, restores the saved selection and enables the mapping button.
        The handler also updates the button text to reflect the current selection.
        """

        def on_toggled(checked):
            all_keys = self._current_default_keys()
            if checked:
                # Save current selection
                self._per_tag_saved[tag] = self._per_tag_selection.get(tag, set()).copy()
                # Set to all selected (visual)
                self._per_tag_selection[tag] = set(all_keys)
                button.setEnabled(False)
            else:
                # Restore saved selection (or empty set if none)
                self._per_tag_selection[tag] = self._per_tag_saved.get(tag, set()).copy()
                button.setEnabled(True)

            self._update_mapping_button_text(button, tag)

        return on_toggled

    # ---------- load / save ----------
    def load(self):
        # Load filter tags
        filter_tags = self.config.setting["replace_unwanted_characters_filter_tags"]

        # Populate filter_tags_table if present in UI
        if hasattr(self, "filter_tags_table"):
            self.filter_tags_table.setRowCount(0)
            for tag in filter_tags:
                row = self.filter_tags_table.rowCount()
                self.filter_tags_table.insertRow(row)
                self.filter_tags_table.setItem(row, 0, QtWidgets.QTableWidgetItem(tag))

        char_table = self.config.setting["replace_unwanted_characters_char_table"]

        if hasattr(self, "replacement_table"):
            self.replacement_table.setRowCount(0)
            for search, replace in char_table.items():
                row = self.replacement_table.rowCount()
                self.replacement_table.insertRow(row)
                self.replacement_table.setItem(row, 0, QtWidgets.QTableWidgetItem(search))
                self.replacement_table.setItem(row, 1, QtWidgets.QTableWidgetItem(replace))

        # Load per-tag tables (optional)
        per_tag = self.config.setting["replace_unwanted_characters_per_tag_tables"]

        # Initialize in-memory selection dicts from config (per_tag maps tag -> list of enabled keys or dict)
        self._per_tag_selection = {}
        self._per_tag_saved = {}
        self._per_tag_active = {}
        for tag, val in per_tag.items():
            if isinstance(val, dict):
                keys = val.get("keys", [])
                active = val.get("active", True)
                default = val.get("default", True)
            else:
                keys = val or []
                active = True
                default = True
            self._per_tag_selection[tag] = set(keys)
            self._per_tag_saved[tag] = set(keys)
            self._per_tag_active[tag] = active
            self._per_tag_default[tag] = default

        # Build per_tag_table rows
        self.rebuild_per_tag_table()

    def save(self):
        self._save_filter_tags()
        self._save_replacement_table()
        self._save_per_tag_tables()

    def _save_filter_tags(self):
        filter_tags = self._get_configured_filter_tags()
        self.config.setting["replace_unwanted_characters_filter_tags"] = filter_tags

    def _get_configured_filter_tags(self) -> List[str]:
        filter_tags = []
        if hasattr(self, "filter_tags_table"):
            for row in range(self.filter_tags_table.rowCount()):
                item = self.filter_tags_table.item(row, 0)
                if item and item.text().strip():
                    filter_tags.append(item.text().strip())
        return filter_tags

    def _save_replacement_table(self):
        char_table = {}
        if hasattr(self, "replacement_table"):
            for row in range(self.replacement_table.rowCount()):
                search_item = self.replacement_table.item(row, 0)
                replace_item = self.replacement_table.item(row, 1)
                if search_item and replace_item:
                    search = search_item.text()
                    replace = replace_item.text()
                    if search:
                        char_table[search] = replace
        self.config.setting["replace_unwanted_characters_char_table"] = char_table

    def _save_per_tag_tables(self):
        per_tag_tables = {}
        if hasattr(self, "per_tag_table"):
            for row in range(self.per_tag_table.rowCount()):
                active_chk = self._get_checkbox_from_cell(row, 0)
                tag_item = self.per_tag_table.item(row, 1)
                use_default_chk = self._get_checkbox_from_cell(row, 2)

                if not tag_item:
                    continue

                tag = tag_item.text()
                use_default = isinstance(use_default_chk, QtWidgets.QCheckBox) and use_default_chk.isChecked()
                is_active = isinstance(active_chk, QtWidgets.QCheckBox) and active_chk.isChecked()

                selected_keys = self._per_tag_selection.get(tag, set())
                per_tag_tables[tag] = {
                    "keys": list(selected_keys),
                    "active": bool(is_active),
                    "default": bool(use_default)
                }

                log.debug(
                    f"{PLUGIN_NAME}: Saving per-tag table for tag '{tag}': use_default={use_default}, "
                    f"active={is_active}, keys={selected_keys}")

        self.config.setting["replace_unwanted_characters_per_tag_tables"] = per_tag_tables

    def _get_checkbox_from_cell(self, row: int, column: int) -> Optional[QtWidgets.QCheckBox]:
        """
        Helper to get the QCheckBox from a per_tag_table cell.
        Args:
            row: The row index.
            column: The column index.
        Returns:
            The checkbox widget if found, else None.
        """
        container = self.per_tag_table.cellWidget(row, column)
        if container and isinstance(container, QtWidgets.QWidget):
            layout = container.layout()
            if layout and layout.count() > 0:
                widget = layout.itemAt(0).widget()
                if isinstance(widget, QtWidgets.QCheckBox):
                    return widget
        return None

class MultiSelectDialog(QtWidgets.QDialog):
    """A dialog for selecting multiple items from a list."""

    def __init__(self, parent, title, items, selected_items):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(300)

        self.list_widget = QtWidgets.QListWidget()
        for item_text in items:
            item = QtWidgets.QListWidgetItem(item_text)
            # noinspection PyUnresolvedReferences
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            is_checked = item_text in selected_items
            # noinspection PyUnresolvedReferences
            item.setCheckState(QtCore.Qt.Checked if is_checked else QtCore.Qt.Unchecked)
            self.list_widget.addItem(item)

        # noinspection PyUnresolvedReferences
        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.list_widget)
        layout.addWidget(self.buttons)

    def get_selected_items(self):
        """Returns a set of the text of all checked items."""
        selected = set()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            # noinspection PyUnresolvedReferences
            if item.checkState() == QtCore.Qt.Checked:
                selected.add(item.text())
        return selected
