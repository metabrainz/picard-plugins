# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets, QtCore
from picard import config, log
from picard import metadata
from picard.script import register_script_function
from picard.ui.options import register_options_page

from .constants import CONFIG_NAME_FILTER_TAGS, CONFIG_NAME_PER_TAG_TABLES, CONFIG_NAME_CHAR_TABLE

PLUGIN_NAME = "Replace Unwanted Characters"
PLUGIN_AUTHOR = "nrth3rnlb"
PLUGIN_VERSION = "1.0"
PLUGIN_API_VERSIONS = ["2.7", "2.8"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"
PLUGIN_DESCRIPTION = '''
## Replace Unwanted Characters

The *Replace Unwanted Characters* Plugin replaces unwanted characters in tags.

### Features

- Replace specified characters in configurable tags (default: `album`, `artist`, `title`, `albumartist`, `releasetype`, `label`).
- Configurable default character mapping table.
- Per-tag mappings: enable either the default mapping or a custom selection for each tag.
- Tagger script function: `$replace_unwanted()` for use in Picard scripts.

The plugin is based on an idea and the implementation in the "Replace Forbidden Symbols" plugin by Alex Rustler
<alex_rustler@rambler.ru>
'''

from .settings_ui import ReplaceUnwantedCharactersOptionsPage as _ReplaceUnwantedCharactersOptionsPage

# Wrapper classes to ensure proper plugin registration
class ReplaceUnwantedCharactersOptionsPage(_ReplaceUnwantedCharactersOptionsPage):
    """Wrapper class for the ShelvesOptionsPage to ensure proper plugin registration."""


def get_config_settings():
    """Load settings from config: returns (filter_tags, default_table, per_tag_tables)"""

    filter_tags = config.setting[CONFIG_NAME_FILTER_TAGS]
    default_table = config.setting[CONFIG_NAME_CHAR_TABLE]
    per_tag_tables = config.setting[CONFIG_NAME_PER_TAG_TABLES]

    return filter_tags, default_table, per_tag_tables

def _replace_with_table(value, table):
    """Apply a mapping table to a tag value list"""

    def sanitize_char(c):
        return table.get(c, c)

    return ["".join(sanitize_char(ch) for ch in item) for item in value]

def replace_unwanted_characters(tagger, metadata, *args):
    filter_tags, default_table, per_tag_tables = get_config_settings()

    for name, value in metadata.rawitems():
        if name not in filter_tags:
            continue

        entry = per_tag_tables.get(name)
        # default: apply full default_table
        if entry is None:
            table = default_table
        else:
            # support both legacy list form and new dict form
            if isinstance(entry, dict):
                active = entry.get("active", True)
                keys_list = entry.get("keys", [])
            else:
                # legacy list -> active by default
                active = True
                keys_list = entry

            if not active:
                # skip applying any replacements for this tag
                continue

            # build a per-tag mapping from default_table filtered to selected keys
            table = {k: v for k, v in default_table.items() if k in set(keys_list)}

        metadata[name] = _replace_with_table(value, table)

def script_replace_unwanted(parser, value):
    # Tagger function: use configured default mapping
    default_table = config.setting[CONFIG_NAME_CHAR_TABLE]

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

log.debug(PLUGIN_NAME + ": registration" )

register_options_page(ReplaceUnwantedCharactersOptionsPage)

metadata.register_track_metadata_processor(replace_unwanted_characters)
metadata.register_album_metadata_processor(replace_unwanted_characters)

register_script_function(script_replace_unwanted, name="replace_unwanted")
