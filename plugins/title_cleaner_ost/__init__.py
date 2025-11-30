# -*- coding: utf-8 -*-

PLUGIN_NAME = "Title Cleaner OST"
PLUGIN_AUTHOR = "nrth3rnlb"
PLUGIN_DESCRIPTION = """
The Plugin “Title Cleaner OST” removes soundtrack-related information (e.g., "OST", "Soundtrack") from album titles.
Supports custom regex patterns, a whitelist and a test field via the plugin settings.
Regular expressions are a powerful tool. They can therefore also cause serious damage.
Use [regex101](https://regex101.com/) or [regex101](https://regex101.com/r/3XS83D/) to test your pattern.
Use at your own risk.
"""
PLUGIN_VERSION = "1.4.0"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

import os
import re
import threading
import unicodedata
from typing import List, Dict, Any, Pattern, Optional

from PyQt5 import uic  # type: ignore
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import (
    QCheckBox,
    QPlainTextEdit,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
    QGridLayout,
)
from picard import config, log
from picard.config import BoolOption, TextOption, ListOption
from picard.metadata import register_album_metadata_processor
from picard.ui.options import OptionsCheckError
from picard.ui.options import OptionsPage
from picard.ui.options import register_options_page

REGEX_DESCRIPTION_MD = """
**Regex explanation (end‑based removal; re.IGNORECASE):**

- Aim: Removes one or more phrases like "Original ... Soundtrack" at the end of the string,
including any preceding separator.
- Separators (optional, incl. spaces): ` : | ： | ∶ | - | – | — | ( | [ `
- Keywords (as whole words, one or more): `Original|Album|Movie|Motion|Picture|Soundtrack|Score|OST|Music|Edition|Inspired|by|from|the|TV|Series|Video|Game|Film|Show`
- Optional closing bracket: `)` or `]`
- Repeats until the end of the string `(…)+$`
- Example: "Title∶ Music From the Original Soundtrack" » "Title"
- Note: After replacement, multiple spaces are collapsed and leading/trailing whitespace is trimmed.
""".lstrip("\n")

MODULE_DEFAULT_REGEX = r'''(\s*(?:(?::|：|∶|-|–|—|\(|\[)\s*)?(\b(?:Original|Album|Movie|Motion|Picture|Soundtrack|Score|OST|Music|Edition|Inspired|by|from|the|TV|Series|Video|Game|Film|Show)\b)+(?:\)|\])?\s*)+$'''
MODULE_DEFAULT_REGEX_N = r''

# List of additional regexes
# {"pattern": DEFAULT_REGEX, "enabled": True, "name": ""}
MODULE_DEFAULT_REGEX_LIST: List[Dict[str, Any]] = [
    {"pattern": MODULE_DEFAULT_REGEX, "enabled": True, "name": ""}
]

MODULE_DEFAULT_WHITELIST = ""

MODULE_DEFAULT_APPLY_OPTIONS: List[Dict[str, Any]] = [
    {
        "releasetype": "all",
        "text": "All Release Types",
        "tooltip": "The pattern is applied to all albums.",
        "enabled": False,
        "condition": None
    },
    {
        "releasetype": "soundtrack",
        "text": "Soundtracks",
        "tooltip": "The pattern is only applied to albums with release type soundtrack.",
        "enabled": True,
        "condition": {"tag": "releasetype", "value": "soundtrack"}
    }
]

# The standard regex remains as a single definition for reasons of Downward compatibility
SETTING_NAME_REGEX = "title_cleaner_ost_regex"
SETTING_NAME_DEFINED_REGEXES = "title_cleaner_ost_regex_list"
SETTING_NAME_LIVE_UPDATES = "title_cleaner_ost_live_updates"
SETTING_NAME_APPLY_OPTIONS = "title_cleaner_ost_apply_options"
SETTING_NAME_WHITELIST = "title_cleaner_ost_whitelist"
SETTING_NAME_TEST_VALUE = "title_cleaner_ost_test_value"


class RemoveReleaseTitleOstIndicatorOptionsPage(OptionsPage):
    """
    Options page for the Title Cleaner OST plugin.
    """
    NAME = "title_cleaner_ost"
    TITLE = "Title Cleaner OST"
    PARENT = "plugins"

    # UI attributes created by uic.loadUi — declare types for mypy
    test_input: QLineEdit
    whitelist_text: QPlainTextEdit
    enable_live_updates: QCheckBox
    run_update: QPushButton
    chk_all_release_types: QCheckBox
    regex_containers: QWidget
    regex_containers_layout: QVBoxLayout
    gridLayout_2: QGridLayout

    # Defaults used by the UI code (map to module defaults)
    DEFAULT_REGEX: str = MODULE_DEFAULT_REGEX
    DEFAULT_REGEX_N: str = MODULE_DEFAULT_REGEX_N

    # Runtime attributes
    regex_widgets: List[Dict[str, Any]]
    compiled_regexes: List[Optional[Pattern[Any]]]
    configured_regexes: List[Dict[str, Any]] = []
    test_output: QLabel
    apply_option_checkboxes: Dict[str, QCheckBox]

    options = [
        ListOption("setting", SETTING_NAME_DEFINED_REGEXES, MODULE_DEFAULT_REGEX_LIST),
        TextOption("setting", SETTING_NAME_REGEX, MODULE_DEFAULT_REGEX),
        TextOption("setting", SETTING_NAME_WHITELIST, MODULE_DEFAULT_WHITELIST),
        BoolOption("setting", SETTING_NAME_LIVE_UPDATES, False),
        ListOption("setting", SETTING_NAME_APPLY_OPTIONS, MODULE_DEFAULT_APPLY_OPTIONS),
        TextOption("setting", SETTING_NAME_TEST_VALUE, "")
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), 'title_cleaner_ost_config.ui')
        uic.loadUi(ui_file, self)

        # UI has a container named regex_containers_layout_layout for dynamic widgets
        self.regex_widgets: List[Dict[str, Any]] = []
        self.apply_option_checkboxes = {}

        # ToDo: I'll have to come up with something else for that.
        # self.regex_help.setText(self.REGEX_DESCRIPTION_MD)
        # markdown_fmt = getattr(Qt, "MarkdownText", Qt.PlainText)
        # self.regex_help.setTextFormat(markdown_fmt)
        # self.regex_help.setWordWrap(True)
        # self.regex_help.setTextInteractionFlags(
        #     Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse
        # )
        # self.regex_help.setVisible(False)

        # Compiled regex cache for preview
        # self.compiled_regexes = []

        # Test field logic
        self.test_input.textChanged.connect(self.update_test_output)
        self.whitelist_text.textChanged.connect(self.update_test_output)
        self.enable_live_updates.stateChanged.connect(self.update_test_output)
        self.enable_live_updates.stateChanged.connect(self.update_run_button_state)

        # Run Update button
        self.run_update.clicked.connect(self.force_update_test_output)

        # Release type checkboxes logic
        self.chk_all_release_types.stateChanged.connect(self.update_release_type_chks)

        self.update_test_output_forced = False

        self.compiled_regexes = []

    def add_regex_container_at_index(self, index: int):
        """Adds a new regex widget dynamically at the specified position."""
        position = index + 1  # Einfügen nach dem aktuellen Container
        log.debug("%s: Adding regex container at position %d", PLUGIN_NAME, position)
        regex_dict = self._create_regex_container(container=self.regex_containers, index=position)
        self.regex_containers_layout.insertWidget(position, regex_dict["container"])
        self.regex_widgets.insert(position, regex_dict)
        self.on_regex_changed()

    def _create_regex_container(self, container: QWidget, index: int) -> Dict[str, Any]:
        """Creates a new regex container and returns a dict with widget references."""
        log.debug("%s: Creating regex container %d", PLUGIN_NAME, index)
        container_regex_n = QWidget(container)
        container_regex_n.setObjectName(f"container_regex_{index}")

        layout_container_regex_n = QVBoxLayout(container_regex_n)
        layout_container_regex_n.setSpacing(6)
        layout_container_regex_n.setObjectName(f"layout_container_regex_{index}")

        # name_regex_n = QLabel(container_regex_n)
        # name_regex_n.setObjectName(f"name_regex_{index}")
        # # one-based, for display
        # name_regex_n.setText(f"Regex {index + 1}")
        #
        # layout_container_regex_n.addWidget(name_regex_n)

        pattern_and_buttons_regex_n = QWidget(container_regex_n)
        pattern_and_buttons_regex_n.setObjectName(f"pattern_and_buttons_regex_{index}")
        layout_pattern_and_buttons_regex_n = QHBoxLayout(pattern_and_buttons_regex_n)
        layout_pattern_and_buttons_regex_n.setSpacing(6)
        layout_pattern_and_buttons_regex_n.setObjectName(f"layout_pattern_and_buttons_regex_{index}")
        pattern_regex_n = QPlainTextEdit(pattern_and_buttons_regex_n)
        pattern_regex_n.setObjectName(f"pattern_regex_{index}")

        pattern_regex_n.setMinimumHeight(20)
        pattern_regex_n.setMaximumHeight(100)

        layout_pattern_and_buttons_regex_n.addWidget(pattern_regex_n)

        buttons_regex_n = QWidget(pattern_and_buttons_regex_n)
        buttons_regex_n.setObjectName(f"buttons_regex_{index}")

        layout_buttons_regex_n = QVBoxLayout(buttons_regex_n)
        layout_buttons_regex_n.setObjectName(f"layout_buttons_regex_{index}")

        # v_space_regex_n = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)

        # layout_buttons_regex_n.addItem(v_space_regex_n)

        enable_regex_n = QCheckBox(buttons_regex_n)
        enable_regex_n.setObjectName(f"enable_regex_{index}")
        enable_regex_n.setText("activated")
        enable_regex_n.setChecked(False)

        layout_buttons_regex_n.addWidget(enable_regex_n)

        reset_regex_n = QPushButton(buttons_regex_n)
        reset_regex_n.setObjectName(f"reset_regex_{index}")
        reset_regex_n.setText("Restore Default")
        reset_regex_n.setToolTip("Resets the regex pattern.")

        reset_regex_n.clicked.connect(lambda: self.reset_regex_n_to_default(index))

        layout_buttons_regex_n.addWidget(reset_regex_n)

        # Button to remove a regex but not for the first
        if index > 0:
            remove_regex_n = QPushButton(buttons_regex_n)
            remove_regex_n.setObjectName(f"remove_regex_{index}")
            remove_regex_n.setText("Remove Regex")
            remove_regex_n.setToolTip("Removes the regex completely.")
            remove_regex_n.clicked.connect(
                lambda: self.remove_regex_container_by_name(f"container_regex_{index}"))

            layout_buttons_regex_n.addWidget(remove_regex_n)

        log.debug("%s: index: %s, len: %s", PLUGIN_NAME, index, len(self.regex_widgets))
        add_regex_n = QPushButton(buttons_regex_n)
        add_regex_n.setObjectName(f"add_regex_{index}")
        add_regex_n.setText("Add Regex")
        add_regex_n.setToolTip("Add another regex definition.")
        add_regex_n.clicked.connect(lambda: self.add_regex_container_at_index(index))

        layout_buttons_regex_n.addWidget(add_regex_n)

        layout_pattern_and_buttons_regex_n.addWidget(buttons_regex_n)

        layout_container_regex_n.addWidget(pattern_and_buttons_regex_n)

        error_message_regex_n = QLabel(container_regex_n)
        error_message_regex_n.setObjectName(f"error_message_regex_{index}")
        error_message_regex_n.setMinimumSize(QSize(0, 30))
        error_message_regex_n.setStyleSheet("color: red;")
        error_message_regex_n.setFrameShape(QFrame.Panel)
        error_message_regex_n.setFrameShadow(QFrame.Sunken)
        error_message_regex_n.setTextFormat(Qt.PlainText)
        error_message_regex_n.setTextInteractionFlags(
            Qt.LinksAccessibleByKeyboard | Qt.LinksAccessibleByMouse | Qt.TextBrowserInteraction | Qt.TextSelectableByKeyboard | Qt.TextSelectableByMouse)

        layout_container_regex_n.addWidget(error_message_regex_n)

        enable_regex_n.stateChanged.connect(self.on_regex_changed)
        enable_regex_n.stateChanged.connect(self.update_test_output)
        pattern_regex_n.textChanged.connect(self.on_regex_changed)
        pattern_regex_n.textChanged.connect(self.update_test_output)

        # Todo entfernen
        container_regex_n.dumpObjectTree()

        return {
            "container": container_regex_n,
            "text": pattern_regex_n,
            "checkbox": enable_regex_n,
            "error_label": error_message_regex_n
        }

    def remove_regex_container_by_name(self, name: str):
        """Removes a regex widget."""
        for regex_dict in self.regex_widgets:
            if regex_dict["container"].objectName() == name:
                self.regex_widgets.remove(regex_dict)
                regex_dict["container"].setParent(None)
                break
        self.on_regex_changed()
        self.update_test_output()

    def update_release_type_chks(self):
        """Updates the state of release type checkboxes."""
        deactivate_selection_option = self.chk_all_release_types.isChecked()
        for i in range(self.gridLayout_2.count()):
            if i > 0:  # Skip the first checkbox (All Release Types)
                item = self.gridLayout_2.itemAt(i)
                if item is not None and item.widget() is not None:
                    widget = item.widget()
                    if widget is not None and isinstance(widget, QCheckBox):
                        widget.setEnabled(not deactivate_selection_option)

    def force_update_test_output(self):
        """Forces an update of the test output when the 'Run Update' button is clicked."""
        self.update_test_output_forced = True
        self.update_test_output()

    def on_regex_changed(self):
        self.validate_regex_patterns()

    def load(self):
        """Loads the regex list, whitelist, and checkbox state from config into the UI."""
        self.configured_regexes: List[Dict[str, Any]] = config.setting[SETTING_NAME_DEFINED_REGEXES]

        if config.setting[SETTING_NAME_REGEX] and config.setting[SETTING_NAME_REGEX] != self.DEFAULT_REGEX:
            self.configured_regexes[0].update({"pattern": config.setting[SETTING_NAME_REGEX]})

        for i, regex_definition in enumerate(self.configured_regexes, start=0):
            regex_dict = self._create_regex_container(self.regex_containers, i)
            self.regex_containers_layout.addWidget(regex_dict["container"])
            self.regex_widgets.append(regex_dict)
            # Set initial values from config
            regex_dict["text"].setPlainText(regex_definition.get("pattern", ""))
            regex_dict["checkbox"].setChecked(regex_definition.get("enabled", False))

        self.validate_regex_patterns()

        # Clear dynamic checkboxes (keep the first "all" checkbox)
        layout = self.gridLayout_2
        while layout.count() > 1:
            item = layout.takeAt(1)  # Always remove the item after "all"
            if item and item.widget():
                item.widget().deleteLater()

        self.apply_option_checkboxes.clear()

        apply_options = config.setting[SETTING_NAME_APPLY_OPTIONS]

        for apply_option in apply_options:
            log.debug("%s: Processing option for releasetype '%s'", PLUGIN_NAME, apply_option.get("releasetype"))
            releasetype = apply_option.get("releasetype")
            if releasetype == "all":
                self.chk_all_release_types.setText(apply_option.get("text", self.chk_all_release_types.text()))
                self.chk_all_release_types.setToolTip(apply_option.get("tooltip", self.chk_all_release_types.toolTip()))
                self.chk_all_release_types.setChecked(bool(apply_option.get("enabled", False)))
                self.chk_all_release_types.stateChanged.connect(self.update_release_type_chks)
                self.apply_option_checkboxes["all"] = self.chk_all_release_types
                continue

            chk = QCheckBox(apply_option.get("releasetype", ""))
            chk.setText(apply_option.get("text", ""))
            chk.setToolTip(apply_option.get("tooltip", ""))
            chk.setChecked(bool(apply_option.get("enabled", False)))
            self.gridLayout_2.addWidget(chk)
            self.apply_option_checkboxes[releasetype] = chk

        self.update_release_type_chks()

        # Load other settings
        self.whitelist_text.setPlainText(config.setting[SETTING_NAME_WHITELIST])
        self.enable_live_updates.setChecked(config.setting[SETTING_NAME_LIVE_UPDATES])
        self.run_update.setEnabled(not self.enable_live_updates.isChecked())

        self.test_input.setText(config.setting[SETTING_NAME_TEST_VALUE])

    def save(self):
        """Saves the configuration settings."""
        if not self.validate_regex_patterns():
            raise OptionsCheckError(
                "Invalid Regex Pattern",
                "One or more regex patterns you have entered are invalid. Please correct them before saving."
            )

        self.configured_regexes.clear()
        for i, regex_dict in enumerate(self.regex_widgets, start=1):
            self.configured_regexes.append({
                "pattern": regex_dict["text"].toPlainText(),
                "enabled": regex_dict["checkbox"].isChecked(),
                "name": f"Regex {i}"
            })

        config.setting[SETTING_NAME_DEFINED_REGEXES] = self.configured_regexes

        original_options = config.setting[SETTING_NAME_APPLY_OPTIONS]
        saved_apply_options = []

        for option in original_options:
            releasetype = option.get("releasetype")
            checkbox = self.apply_option_checkboxes.get(releasetype)

            saved_apply_options.append({
                "releasetype": releasetype,
                "text": option.get("text", ""),
                "tooltip": option.get("tooltip", ""),
                "enabled": checkbox.isChecked() if checkbox else option.get("enabled", False),
                "condition": option.get("condition")
            })

        config.setting[SETTING_NAME_APPLY_OPTIONS] = saved_apply_options

        # Save other settings
        config.setting[SETTING_NAME_WHITELIST] = self.whitelist_text.toPlainText()
        config.setting[SETTING_NAME_LIVE_UPDATES] = self.enable_live_updates.isChecked()
        config.setting[SETTING_NAME_TEST_VALUE] = self.test_input.text()

    def reset_regex_n_to_default(self, index):
        """Resets the nth regex to the default pattern (empty string)."""
        if 0 <= index < len(self.regex_widgets):
            if index == 0:
                self.regex_widgets[index]["text"].setPlainText(self.DEFAULT_REGEX)
                return
            self.regex_widgets[index]["text"].setPlainText(self.DEFAULT_REGEX_N)

    def validate_regex_patterns(self) -> bool:
        """Validates all regex patterns, compiles them for caching, and updates the UI accordingly."""
        valid = True
        self.compiled_regexes = []

        # Dynamic regexes
        for regex_dict in self.regex_widgets:
            pattern = regex_dict["text"].toPlainText()
            try:
                compiled = re.compile(pattern, flags=re.IGNORECASE)
                self.compiled_regexes.append(compiled)
                regex_dict["text"].setStyleSheet("")
                regex_dict["error_label"].setVisible(False)
            except re.error as e:
                log.debug(PLUGIN_NAME + ": Regex validation error: %s", e)
                self.compiled_regexes.append(None)
                regex_dict["text"].setStyleSheet("background-color: #ffcccc;")
                regex_dict["error_label"].setText(f"Invalid regex: {e}")
                regex_dict["error_label"].setVisible(True)
                valid = False

        return valid

    def update_run_button_state(self):
        """Enables or disables the 'Run Update' button based on the live updates checkbox."""
        self.run_update.setEnabled(not self.enable_live_updates.isChecked())

    def update_test_output(self):
        """
        Applies the current regex/whitelist/setting to the test input and shows the result.
        """
        if not self.update_test_output_forced and not self.enable_live_updates.isChecked():
            return

        self.update_test_output_forced = False

        album_title = self.test_input.text().strip()
        whitelist = self.whitelist_text.toPlainText()

        # Normalise whitelist titles using Unicode NFC normalization
        whitelist_titles = [
            unicodedata.normalize('NFC', line.strip()).lower()
            for line in whitelist.splitlines() if line.strip()
        ]

        # Normalise album title for comparison
        normalized_title = unicodedata.normalize('NFC', album_title).lower()

        # Whitelist check
        if normalized_title in whitelist_titles:
            self.test_output.setText("Whitelisted – will not be changed!")
            return

        new_title = album_title
        # Apply regexes in order
        for i, regex_dict in enumerate(self.regex_widgets):
            if regex_dict["checkbox"].isChecked() and i < len(self.compiled_regexes) and self.compiled_regexes[i]:
                compiled_regex = self.compiled_regexes[i]
                if not compiled_regex:
                    continue
                try:
                    new_title = compiled_regex.sub('', new_title)
                except Exception as e:
                    log.debug(PLUGIN_NAME + ": Preview error on regex %d: %s", i, e)
                    self.test_output.setText(f"Regex {i} error: {e}")
                    return

        # Normalise whitespace and strip leading/trailing whitespace
        new_title = ' '.join(new_title.split()).strip()
        self.test_output.setText(new_title)


# cache with lock for thread safety
_cache_lock: threading.Lock = threading.Lock()
_regex_cache: Dict[str, Any] = {
    'compiled_regexes': [],
    'last_regex_list': None
}


def title_cleaner_ost(album, metadata, release):
    log.debug("%s: title_cleaner_ost called for album '%s'", PLUGIN_NAME, metadata.get("album", "<no album>"))
    regex_list = config.setting[SETTING_NAME_DEFINED_REGEXES]
    whitelist = config.setting[SETTING_NAME_WHITELIST]
    apply_options = config.setting[SETTING_NAME_APPLY_OPTIONS]

    # Atomic check, compile, and update for regex lists under lock
    with _cache_lock:
        current_patterns = [r["pattern"] for r in regex_list]
        if current_patterns != _regex_cache['last_regex_list']:
            compiled_list: List[Optional[Pattern[Any]]] = []
            for r in regex_list:
                if r.get("pattern"):
                    try:
                        compiled_list.append(re.compile(r["pattern"], flags=re.IGNORECASE))
                    except re.error as e:
                        log.error("%s: Failed to compile regex: %s", PLUGIN_NAME, e)
                        compiled_list.append(None)
                else:
                    compiled_list.append(None)
            _regex_cache['compiled_regexes'] = compiled_list
            _regex_cache['last_regex_list'] = current_patterns
        compiled_regexes: List[Optional[Pattern[Any]]] = _regex_cache['compiled_regexes']

    # Normalise whitelist titles using Unicode NFC normalization
    whitelist_titles = [
        unicodedata.normalize('NFC', line.strip()).lower()
        for line in whitelist.splitlines() if line.strip()
    ]

    # Determine if we should process this album based on release types
    should_process: bool = False

    try:
        for option in apply_options:
            if option.get("enabled"):
                if option.get("releasetype") == "all":
                    log.debug("%s: Applying to all release types", PLUGIN_NAME)
                    should_process = True
                    continue
                elif option.get("condition").get("tag") in metadata and option.get("condition").get("value") in \
                        metadata[option.get("condition").get("tag")]:
                    log.debug("%s: Applying to release type '%s'", PLUGIN_NAME, option.get("condition").get("value"))
                    should_process = True
                    continue
    except AttributeError as e:
        log.error("%s: Error processing apply options: %s", PLUGIN_NAME, e)

    if not should_process:
        log.debug("%s: No matching releasetype found", PLUGIN_NAME)
        return

    if "album" in metadata:
        album_title = metadata["album"].strip()
        normalized_title = unicodedata.normalize('NFC', album_title).lower()

        if normalized_title in whitelist_titles:
            log.debug("%s: Album '%s' is whitelisted, skipping removal", PLUGIN_NAME, album_title)
            return

        if should_process:
            new_title = album_title
            try:
                for i, compiled in enumerate(compiled_regexes):
                    if regex_list[i]["enabled"] and compiled:
                        new_title = compiled.sub('', new_title)
                # Normalise whitespace and strip leading/trailing whitespace once after all substitutions
                new_title = ' '.join(new_title.split()).strip()
                metadata["album"] = new_title
                log.debug("%s: Changed album title from '%s' to '%s'", PLUGIN_NAME, album_title, new_title)
            except Exception as e:
                log.error("%s: Regex application error: %s", PLUGIN_NAME, e)


# Register the plugin
register_options_page(RemoveReleaseTitleOstIndicatorOptionsPage)
register_album_metadata_processor(title_cleaner_ost)
