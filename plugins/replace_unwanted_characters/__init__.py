# -*- coding: utf-8 -*-

import os

from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtWidgets import QHeaderView
from picard import metadata
from picard.config import Option
from picard.script import register_script_function
from picard.ui.options import OptionsPage, register_options_page

__version__ = '1.0.0'

DEFAULT_TAGS = ["album", "artist", "title", "albumartist", "releasetype", "label"]

DEFAULT_CHAR_MAPPING = {
    ":": "∶", "/": "⁄", "*": "∗", "?": "？", '"': '″',
    '\\': '⧵', '.': '․', '|': 'ǀ', '<': '‹', '>': '›'
}

PLUGIN_NAME = "Replace Unwanted Characters"
PLUGIN_AUTHOR = "nrth3rnlb"
PLUGIN_VERSION = __version__
PLUGIN_API_VERSIONS = ["2.7", "2.8"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"
PLUGIN_DESCRIPTION = '''
    The "Replace Unwanted Characters" Plugin replaces unwanted characters in tags.
    Also add $replace_unwanted() function for Tagger.

    The plugin is based on an idea and the implementation in the "Replace Forbidden Symbols" plugin by Alex Rustler 
    <alex_rustler@rambler.ru>
'''

def get_config_settings():
    """Load settings from config: returns (filter_tags, default_table, per_tag_tables)"""
    from picard import config

    try:
        filter_tags = config.setting["replace_unwanted_characters_filter_tags"]
    except KeyError:
        filter_tags = DEFAULT_TAGS

    try:
        default_table = config.setting["replace_unwanted_characters_char_table"]
    except KeyError:
        default_table = DEFAULT_CHAR_MAPPING

    try:
        per_tag_tables = config.setting["replace_unwanted_characters_per_tag_tables"]
    except KeyError:
        per_tag_tables = {}

    return filter_tags, default_table, per_tag_tables

def _replace_with_table(value, table):
    """Apply a mapping table to a tag value list"""

    def sanitize_char(c):
        return table.get(c, c)

    return ["".join(sanitize_char(ch) for ch in item) for item in value]

def replace_unwanted_characters(tagger, metadata, *args):
    filter_tags, default_table, per_tag_tables = get_config_settings()

    for name, value in metadata.rawitems():
        if name in filter_tags:
            table = per_tag_tables.get(name, default_table)
            metadata[name] = _replace_with_table(value, table)

def script_replace_unwanted(parser, value):
    # Tagger function: use configured default mapping
    from picard import config
    try:
        default_table = config.setting["replace_unwanted_characters_char_table"]
    except KeyError:
        default_table = DEFAULT_CHAR_MAPPING

    if isinstance(value, list):
        return _replace_with_table(value, default_table)
    else:
        # single string
        return "".join(default_table.get(ch, ch) for ch in value)

class MultiSelectDialog(QtWidgets.QDialog):
    """A dialog for selecting multiple items from a list."""

    def __init__(self, parent, title, items, selected_items):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(300)

        self.list_widget = QtWidgets.QListWidget()
        for item_text in items:
            item = QtWidgets.QListWidgetItem(item_text)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            is_checked = item_text in selected_items
            item.setCheckState(QtCore.Qt.Checked if is_checked else QtCore.Qt.Unchecked)
            self.list_widget.addItem(item)

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
            if item.checkState() == QtCore.Qt.Checked:
                selected.add(item.text())
        return selected

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
        if hasattr(self, "replacement_table"):
            self.replacement_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.replacement_table.cellChanged.connect(self.on_default_table_changed)
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
                self.add_filter_tag_button.clicked.connect(self.add_filter_tag)
            if hasattr(self, "remove_filter_tag_button"):
                self.remove_filter_tag_button.clicked.connect(self.remove_selected_filter_tags)

        # replacement table buttons
        if hasattr(self, "add_row_button"):
            self.add_row_button.clicked.connect(self.add_row)
        if hasattr(self, "remove_row_button"):
            self.remove_row_button.clicked.connect(self.remove_selected_rows)

        # in-memory per-tag selections:
        # maps tag -> set(enabled_keys)
        self._per_tag_selection = {}
        # saved selection used when Use Default is toggled on (to restore later)
        self._per_tag_saved = {}

    # ---------- filter tags table helpers ----------
    def add_filter_tag(self):
        if not hasattr(self, "filter_tags_table"):
            return
        row = self.filter_tags_table.rowCount()
        self.filter_tags_table.insertRow(row)
        self.filter_tags_table.setItem(row, 0, QtWidgets.QTableWidgetItem(""))

    def remove_selected_filter_tags(self):
        if not hasattr(self, "filter_tags_table"):
            return
        rows = set(index.row() for index in self.filter_tags_table.selectedIndexes())
        for row in sorted(rows, reverse=True):
            # remove selection state for tag if present
            item = self.filter_tags_table.item(row, 0)
            if item:
                tag = item.text()
                self._per_tag_selection.pop(tag, None)
                self._per_tag_saved.pop(tag, None)
            self.filter_tags_table.removeRow(row)
        # rebuild per-tag table to reflect new tags
        self.rebuild_per_tag_table()

    def on_filter_tags_changed(self, item):
        # user edited a tag name - rebuild the per-tag table preserving selections where possible
        self.rebuild_per_tag_table()

    # ---------- default replacement table helpers ----------
    def add_row(self):
        row = self.replacement_table.rowCount()
        self.replacement_table.insertRow(row)
        self.replacement_table.setItem(row, 0, QtWidgets.QTableWidgetItem(""))
        self.replacement_table.setItem(row, 1, QtWidgets.QTableWidgetItem(""))

    def remove_selected_rows(self):
        rows = set(index.row() for index in self.replacement_table.selectedIndexes())
        for row in sorted(rows, reverse=True):
            self.replacement_table.removeRow(row)
        # trigger update manually (cellChanged won't be called for removed rows)
        self.on_default_table_changed()

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

        tags = []
        if hasattr(self, "filter_tags_table"):
            for row in range(self.filter_tags_table.rowCount()):
                item = self.filter_tags_table.item(row, 0)
                if item and item.text().strip():
                    tags.append(item.text().strip())

        self.per_tag_table.setRowCount(0)
        all_keys = self._current_default_keys()

        try:
            per_tag_saved = self.config.setting["replace_unwanted_characters_per_tag_tables"]
        except KeyError:
            per_tag_saved = {}

        for tag in tags:
            row = self.per_tag_table.rowCount()
            self.per_tag_table.insertRow(row)
            self.per_tag_table.setRowHeight(row, self.per_tag_table.fontMetrics().height() + 10)

            tag_item = QtWidgets.QTableWidgetItem(tag)
            tag_item.setFlags(tag_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.per_tag_table.setItem(row, 0, tag_item)

            chk = QtWidgets.QCheckBox()
            explicit = tag in per_tag_saved
            chk.setChecked(not explicit)

            # Center the checkbox in the cell
            container = QtWidgets.QWidget()
            layout = QtWidgets.QHBoxLayout(container)
            layout.addWidget(chk)
            layout.setAlignment(QtCore.Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)

            self.per_tag_table.setCellWidget(row, 1, container)

            # Store selection state
            if explicit:
                self._per_tag_selection[tag] = set(per_tag_saved.get(tag, []))
            else:
                self._per_tag_selection[tag] = set(all_keys)
            self._per_tag_saved[tag] = self._per_tag_selection[tag].copy()

            # Mapping button
            btn = QtWidgets.QPushButton()
            self.per_tag_table.setCellWidget(row, 2, btn)
            self._update_mapping_button_text(btn, tag, all_keys)

            # Connect signals
            chk.toggled.connect(self._make_use_default_handler(tag, btn, chk))
            btn.clicked.connect(self._make_mapping_button_handler(tag, btn))

            # Initial state
            btn.setEnabled(not chk.isChecked())

    def _update_mapping_button_text(self, button, tag, all_keys):
        selected_keys = sorted(list(self._per_tag_selection.get(tag, set())))
        num_selected = len(selected_keys)

        if num_selected == 0:
            button.setText(f"none selected")
            return

        # Create a preview string of selected characters
        preview_str = " ".join(selected_keys)

        # I'm unsure whether this might make sense after all.
        # Therefore, commented out.
        # preview_limit = 20  # Max length of the character preview
        # if len(preview_str) > preview_limit:
        #     # Truncate the string if it's too long
        #     preview_str = preview_str[:preview_limit].rsplit(' ', 1)[0] + "…"

        button.setText(f"{preview_str}")

    def _make_mapping_button_handler(self, tag, button):
        def on_button_clicked():
            all_keys = self._current_default_keys()
            current_selection = self._per_tag_selection.get(tag, set())

            dialog = MultiSelectDialog(self, f"Edit Mapping for '{tag}'", all_keys, current_selection)
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                new_selection = dialog.get_selected_items()
                self._per_tag_selection[tag] = new_selection
                self._per_tag_saved[tag] = new_selection.copy()
                self._update_mapping_button_text(button, tag, all_keys)

        return on_button_clicked

    def on_default_table_changed(self, *args):
        if not hasattr(self, "per_tag_table"):
            return

        new_keys = self._current_default_keys()
        new_keys_set = set(new_keys)

        for row in range(self.per_tag_table.rowCount()):
            tag_item = self.per_tag_table.item(row, 0)
            if not tag_item:
                continue
            tag = tag_item.text()

            # Update selection sets by intersecting with new keys
            if tag in self._per_tag_selection:
                self._per_tag_selection[tag] &= new_keys_set
            if tag in self._per_tag_saved:
                self._per_tag_saved[tag] &= new_keys_set

            # Update button text and state
            use_default_widget = self.per_tag_table.cellWidget(row, 1)
            use_default = isinstance(use_default_widget, QtWidgets.QCheckBox) and use_default_widget.isChecked()
            if use_default:
                self._per_tag_selection[tag] = new_keys_set

            button = self.per_tag_table.cellWidget(row, 2)
            if isinstance(button, QtWidgets.QPushButton):
                self._update_mapping_button_text(button, tag, new_keys)

    def _make_use_default_handler(self, tag, button, chk):
        def on_toggled(checked):
            all_keys = self._current_default_keys()
            if checked:
                # Save current selection
                self._per_tag_saved[tag] = self._per_tag_selection[tag].copy()
                # Set to all selected
                self._per_tag_selection[tag] = set(all_keys)
                button.setEnabled(False)
            else:
                # Restore saved selection
                self._per_tag_selection[tag] = self._per_tag_saved.get(tag, set()).copy()
                button.setEnabled(True)

            self._update_mapping_button_text(button, tag, all_keys)

        return on_toggled

    def _make_list_item_changed_handler(self, tag, list_w):
        def on_item_changed(item):
            # update selection set for this tag only if list is enabled (not use-default)
            if list_w.isEnabled():
                checked = {list_w.item(i).text() for i in range(list_w.count()) if
                           list_w.item(i).checkState() == QtCore.Qt.Checked}
                self._per_tag_selection[tag] = set(checked)
                # also update saved selection so toggling Use Default later restores this
                self._per_tag_saved[tag] = set(checked)

        return on_item_changed

    # ---------- load / save ----------
    def load(self):
        config = self.config.setting

        # Load filter tags
        try:
            filter_tags = config["replace_unwanted_characters_filter_tags"]
        except KeyError:
            filter_tags = DEFAULT_TAGS

        # Populate filter_tags_table if present in UI
        if hasattr(self, "filter_tags_table"):
            self.filter_tags_table.setRowCount(0)
            for tag in filter_tags:
                row = self.filter_tags_table.rowCount()
                self.filter_tags_table.insertRow(row)
                self.filter_tags_table.setItem(row, 0, QtWidgets.QTableWidgetItem(tag))

        # Load default replacement table
        try:
            char_table = config["replace_unwanted_characters_char_table"]
        except KeyError:
            char_table = DEFAULT_CHAR_MAPPING

        if hasattr(self, "replacement_table"):
            self.replacement_table.setRowCount(0)
            for search, replace in char_table.items():
                row = self.replacement_table.rowCount()
                self.replacement_table.insertRow(row)
                self.replacement_table.setItem(row, 0, QtWidgets.QTableWidgetItem(search))
                self.replacement_table.setItem(row, 1, QtWidgets.QTableWidgetItem(replace))

        # Load per-tag tables (optional)
        try:
            per_tag = config["replace_unwanted_characters_per_tag_tables"]
        except KeyError:
            per_tag = {}

        # Initialize in-memory selection dicts from config (per_tag maps tag -> list of enabled keys)
        self._per_tag_selection = {}
        self._per_tag_saved = {}
        for tag, keys in per_tag.items():
            self._per_tag_selection[tag] = set(keys)
            self._per_tag_saved[tag] = set(keys)

        # Build per_tag_table rows
        self.rebuild_per_tag_table()

    def save(self):
        config = self.config.setting

        # Save filter tags
        filter_tags = []
        if hasattr(self, "filter_tags_table"):
            for row in range(self.filter_tags_table.rowCount()):
                item = self.filter_tags_table.item(row, 0)
                if item:
                    t = item.text().strip()
                    if t:
                        filter_tags.append(t)
        config["replace_unwanted_characters_filter_tags"] = filter_tags

        # Save default replacement table
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
        config["replace_unwanted_characters_char_table"] = char_table

        # Save per-tag tables
        per_tag_tables = {}
        if hasattr(self, "per_tag_table"):
            for row in range(self.per_tag_table.rowCount()):
                tag_item = self.per_tag_table.item(row, 0)
                use_default_container = self.per_tag_table.cellWidget(row, 1)
                use_default_chk = use_default_container.layout().itemAt(0).widget() if use_default_container else None

                if not tag_item:
                    continue
                tag = tag_item.text()
                use_default = isinstance(use_default_chk, QtWidgets.QCheckBox) and use_default_chk.isChecked()

                if not use_default:
                    selected_keys = self._per_tag_selection.get(tag, set())
                    if selected_keys:
                        per_tag_tables[tag] = list(selected_keys)

        config["replace_unwanted_characters_per_tag_tables"] = per_tag_tables

register_options_page(ReplaceUnwantedCharactersOptionsPage)

metadata.register_track_metadata_processor(replace_unwanted_characters)
metadata.register_album_metadata_processor(replace_unwanted_characters)

register_script_function(script_replace_unwanted, name="replace_unwanted")
