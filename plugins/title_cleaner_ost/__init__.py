# -*- coding: utf-8 -*-

"""
Title Cleaner OST Plugin for MusicBrainz Picard.
Removes soundtrack-related information from album titles using regex.
"""

from PyQt5.QtWidgets import QCheckBox

PLUGIN_NAME = "Title Cleaner OST"
PLUGIN_AUTHOR = "nrth3rnlb"
PLUGIN_DESCRIPTION = """
The Plugin “Title Cleaner OST” removes soundtrack-related information (e.g., "OST", "Soundtrack") from album titles.
Supports custom regex patterns, a whitelist and a test field via the plugin settings.
Regular expressions are a powerful tool. They can therefore also cause serious damage.
Use https://regex101.com/ to test your pattern.
Use at your own risk.
"""
PLUGIN_VERSION = "1.3.3"
PLUGIN_API_VERSIONS = ["2.7", "2.8"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

import re
import unicodedata

from typing import List, Dict, Any

from PyQt5.QtCore import Qt

from picard import config, log
from picard.config import BoolOption, TextOption, ListOption, IntOption
from picard.metadata import register_album_metadata_processor
from picard.ui.options import OptionsPage
from picard.ui.options import register_options_page
from picard.ui.options import OptionsCheckError

from .ui_title_cleaner_ost_config import Ui_RemoveReleaseTitleOstIndicatorSettings

# No longer used, but kept for config compatibility
# ONLY_SOUNDTRACK = "title_cleaner_ost_only_soundtrack"
OST_WHITELIST = "title_cleaner_ost_whitelist"
OST_REGEX = "title_cleaner_ost_regex"
LIVE_UPDATES = "title_cleaner_ost_live_updates"
APPLY_OPTIONS = "title_cleaner_ost_apply_options"
SCHEMA_VERSION = "title_cleaner_ost_schema_version"

def get_setting_with_default(key, default) -> Any:
    """Helper to get a setting with a default fallback."""
    return config.setting[key] if key in config.setting else default

class RemoveReleaseTitleOstIndicatorOptionsPage(OptionsPage):
    """
    Options page for the Title Cleaner OST plugin.
    """
    NAME = "title_cleaner_ost"
    ui: Ui_RemoveReleaseTitleOstIndicatorSettings
    TITLE = "Title Cleaner OST"
    PARENT = "plugins"


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

    DEFAULT_REGEX = r'(\s*(?:(?::|：|∶|-|–|—|\(|\[)\s*)?(\b(?:Original|Album|Movie|Motion|Picture|Soundtrack|Score|OST|Music|Edition|Inspired|by|from|the|TV|Series|Video|Game|Film|Show)\b)+(?:\)|\])?\s*)+$'
    DEFAULT_WHITELIST = ""

    APPLY_OPTIONS_SCHEMA_VERSION = 1

    DEFAULT_APPLY_OPTIONS: List[Dict[str, Any]] = [
        {
            "releasetype": "all",
            "text": "All Release Types",
            "tooltip": "The pattern is applied to all albums.",
            "enabled": False,    # use a clear name for the actual enabled state
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


    options = [
        TextOption("setting", OST_REGEX, DEFAULT_REGEX),
        TextOption("setting", OST_WHITELIST, DEFAULT_WHITELIST),
        BoolOption("setting", LIVE_UPDATES, False),
        ListOption("setting", APPLY_OPTIONS, DEFAULT_APPLY_OPTIONS),
        IntOption("setting", SCHEMA_VERSION, APPLY_OPTIONS_SCHEMA_VERSION),

    ]

    def __init__(self, parent=None):
        super(RemoveReleaseTitleOstIndicatorOptionsPage, self).__init__(parent)
        self.ui = Ui_RemoveReleaseTitleOstIndicatorSettings()
        self.ui.setupUi(self)

        markdown_fmt = getattr(Qt, "MarkdownText", Qt.PlainText)
        self.ui.regex_help.setTextFormat(markdown_fmt)
        self.ui.regex_help.setWordWrap(True)
        self.ui.regex_help.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse
        )

        # Compiled regex cache for preview
        self.compiled_regex = None

        self.ui.regex_help.setVisible(False)
        self.ui.regex_help.setText(self.REGEX_DESCRIPTION_MD)

        # Test field logic
        self.ui.test_input.textChanged.connect(self.update_test_output)
        self.ui.regex_pattern.textChanged.connect(self.update_test_output)
        self.ui.whitelist_text.textChanged.connect(self.update_test_output)
        self.ui.enable_live_updates.stateChanged.connect(self.update_test_output)
        self.ui.enable_live_updates.stateChanged.connect(self.update_run_button_state)

        # Reset button for Regex
        self.ui.reset_button.clicked.connect(self.reset_regex_to_default)

        # Regex validation with every change
        self.ui.regex_pattern.textChanged.connect(self.on_regex_changed)

        # Run Update button
        self.ui.run_update.clicked.connect(self.force_update_test_output)

        # Release type checkboxes logic
        self.ui.chk_all_release_types.stateChanged.connect(self.update_release_type_chks)

        self.update_test_output_forced = False


    def update_release_type_chks(self):
        """Updates the state of release type checkboxes."""
        deactivate_selection_option = self.ui.chk_all_release_types.isChecked()
        for i in range(self.ui.gridLayout_2.count()):
            if i > 0:  # Skip the first checkbox (All Release Types)
                self.ui.gridLayout_2.itemAt(i).widget().setDisabled(deactivate_selection_option)

    def force_update_test_output(self):
        """Forces an update of the test output when the 'Run Update' button is clicked."""
        self.update_test_output_forced = True
        self.update_test_output()

    def on_regex_changed(self):
        self.validate_regex_pattern()

    def load(self):
        """Loads the regex, whitelist, and checkbox state from config into the UI."""
        # Clear dynamic checkboxes (keep the first "all" checkbox)
        layout = self.ui.gridLayout_2
        while layout.count() > 1:
            item = layout.takeAt(layout.count() - 1)
            if item:
                w = item.widget()
                if w:
                    w.setParent(None)

        # Read options directly (no migration)
        options = get_setting_with_default(APPLY_OPTIONS, self.DEFAULT_APPLY_OPTIONS)

        for option in options:
            log.debug("%s: Processing option for releasetype '%s'", PLUGIN_NAME, option.get("releasetype"))
            if option.get("releasetype") == "all":
                self.ui.chk_all_release_types.setText(option.get("text", self.ui.chk_all_release_types.text()))
                self.ui.chk_all_release_types.setToolTip(option.get("tooltip", self.ui.chk_all_release_types.toolTip()))
                self.ui.chk_all_release_types.setChecked(bool(option.get("enabled", False)))
                self.ui.chk_all_release_types.stateChanged.connect(self.update_release_type_chks)
                continue

            chk = QCheckBox(option.get("releasetype", ""))
            chk.setText(option.get("text", ""))
            chk.setToolTip(option.get("tooltip", ""))
            chk.setChecked(bool(option.get("enabled", False)))
            self.ui.gridLayout_2.addWidget(chk)

        self.update_release_type_chks()

        # Load other settings
        self.ui.regex_pattern.setPlainText(get_setting_with_default(OST_REGEX, self.DEFAULT_REGEX))
        self.validate_regex_pattern()
        self.ui.whitelist_text.setPlainText(get_setting_with_default(OST_WHITELIST, self.DEFAULT_WHITELIST))
        self.ui.enable_live_updates.setChecked(get_setting_with_default(LIVE_UPDATES, False))
        self.ui.run_update.setEnabled(not self.ui.enable_live_updates.isChecked())

        self.ui.test_input.setText("")
        self.ui.test_output.setText("")


    def save(self):
        """Saves the configuration settings (no migration)."""
        if not self.validate_regex_pattern():
            raise OptionsCheckError(
                "Invalid Regex Pattern",
                "The regex pattern you have entered is invalid. Please correct it before saving."
            )

        original_options = get_setting_with_default(APPLY_OPTIONS, self.DEFAULT_APPLY_OPTIONS)
        saved_apply_options = []

        layout = self.ui.gridLayout_2
        layout_index = 1  # itemAt(0) is the "All Release Types" checkbox

        for option in original_options:
            if option.get("releasetype") == "all":
                checked = bool(self.ui.chk_all_release_types.isChecked())
            else:
                item = layout.itemAt(layout_index)
                if item is None or item.widget() is None:
                    checked = bool(option.get("enabled", False))
                else:
                    checked = bool(item.widget().isChecked())
                layout_index += 1

            saved_apply_options.append({
                "releasetype": option.get("releasetype"),
                "text": option.get("text", ""),
                "tooltip": option.get("tooltip", ""),
                "enabled": checked,
                "condition": option.get("condition")
            })

        config.setting[APPLY_OPTIONS] = saved_apply_options

        # Save other settings
        config.setting[OST_REGEX] = self.ui.regex_pattern.toPlainText()  # type: ignore[index]
        config.setting[OST_WHITELIST] = self.ui.whitelist_text.toPlainText()  # type: ignore[index]
        config.setting[LIVE_UPDATES] = self.ui.enable_live_updates.isChecked()  # type: ignore[index]


    def reset_regex_to_default(self):
        """Resets the regex to the default pattern."""
        self.ui.regex_pattern.setPlainText(self.DEFAULT_REGEX)

    def validate_regex_pattern(self) -> bool:
        """Validates the regex pattern, compiles it for caching, and updates UI accordingly."""
        pattern = self.ui.regex_pattern.toPlainText()
        try:
            self.compiled_regex = re.compile(pattern, flags=re.IGNORECASE)
            self.ui.regex_pattern.setStyleSheet("")
            self.ui.regex_error_message.setVisible(False)

            return True
        except re.error as e:
            log.debug(PLUGIN_NAME + ": Regex validation error: %s", e)
            self.compiled_regex = None
            self.ui.regex_pattern.setStyleSheet("background-color: #ffcccc;")
            self.ui.regex_error_message.setText(f"Regex error: {e}")
            self.ui.regex_error_message.setVisible(True)
            return False

    def update_run_button_state(self):
        """Enables or disables the 'Run Update' button based on live updates checkbox."""
        self.ui.run_update.setEnabled(not self.ui.enable_live_updates.isChecked())

    def update_test_output(self):
        """
        Applies the current regex/whitelist/setting to the test input and shows the result.
        Always shows a preview but indicates when only_soundtrack is enabled.
        """
        if not self.update_test_output_forced and not self.ui.enable_live_updates.isChecked():
            return

        self.update_test_output_forced = False

        album_title = self.ui.test_input.text().strip()
        whitelist = self.ui.whitelist_text.toPlainText()

        # Normalise whitelist titles using Unicode NFC normalization
        whitelist_titles = [
            unicodedata.normalize('NFC', line.strip()).lower()
            for line in whitelist.splitlines() if line.strip()
        ]

        # Normalise album title for comparison
        normalized_title = unicodedata.normalize('NFC', album_title).lower()

        # Whitelist check
        if normalized_title in whitelist_titles:
            self.ui.test_output.setText("Whitelisted – will not be changed!")
            return

        # Always allow preview but use compiled regex if available
        if self.compiled_regex:
            try:
                new_title = self.compiled_regex.sub('', album_title)
                # Normalise whitespace and strip leading/trailing whitespace
                new_title = ' '.join(new_title.split()).strip()
                self.ui.test_output.setText(new_title)
            except Exception as e:
                log.debug(PLUGIN_NAME + ": Preview error: %s", e)
                self.ui.test_output.setText(f"Regex error: {e}")
        else:
            self.ui.test_output.setText("Invalid regex pattern")

def title_cleaner_ost(album, metadata, release):
    log.debug("%s: title_cleaner_ost called for album '%s'", PLUGIN_NAME, metadata.get("album", "<no album>"))
    regex = config.setting[OST_REGEX]  # type: ignore[index]
    whitelist = config.setting[OST_WHITELIST]  # type: ignore[index]
    apply_options = config.setting[APPLY_OPTIONS]  # type: ignore[index]

    # Normalise whitelist titles using Unicode NFC normalization
    whitelist_titles = [
        unicodedata.normalize('NFC', line.strip()).lower()
        for line in whitelist.splitlines() if line.strip()
    ]

    # Example apply_options structure:
    # {
    #     "releasetype": "soundtrack",
    #     "text": "Soundtracks",
    #     "tooltip": "The pattern is only applied to albums with release type soundtrack.",
    #     "enabled": True,
    #     "condition": {"tag": "releasetype", "value": "soundtrack"}
    # }
    # Determine if we should process this album based on release type
    should_process: bool = False

    try:
        for option in apply_options:
            if option.get("enabled"):
                if option.get("releasetype") == "all":
                    log.debug("%s: Applying to all release types", PLUGIN_NAME)
                    should_process = True
                    continue
                elif option.get("condition").get("tag") in metadata and option.get("condition").get("value") in metadata[option.get("condition").get("tag")]:
                    log.debug("%s: Applying to release type '%s'", PLUGIN_NAME, option.get("condition").get("value"))
                    should_process = True
                    continue
    except AttributeError as e:
        log.error("%s: Error processing apply options: %s", PLUGIN_NAME, e)

    if not should_process:
        log.debug("%s: No matching releasetype found", PLUGIN_NAME)
        return

    log.debug("%s: Processing album title with regex '%s'", PLUGIN_NAME, regex)

    if "album" in metadata:
        album_title = metadata["album"].strip()
        normalized_title = unicodedata.normalize('NFC', album_title).lower()

        if normalized_title in whitelist_titles:
            log.debug("%s: Album '%s' is whitelisted, skipping removal", PLUGIN_NAME, album_title)
            return

        if should_process:
            try:
                compiled_regex = re.compile(regex, flags=re.IGNORECASE)
                new_title = compiled_regex.sub('', album_title)
                # Normalise whitespace and strip leading/trailing whitespace
                new_title = ' '.join(new_title.split()).strip()
                metadata["album"] = new_title
                log.debug("%s: Changed album title from '%s' to '%s'", PLUGIN_NAME, album_title, new_title)
            except re.error as e:
                log.error("%s: Regex application error: %s", PLUGIN_NAME, e)

log.debug("%s: registration", PLUGIN_NAME)
register_options_page(RemoveReleaseTitleOstIndicatorOptionsPage)
register_album_metadata_processor(title_cleaner_ost)
