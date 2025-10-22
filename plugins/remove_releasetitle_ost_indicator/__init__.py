# -*- coding: utf-8 -*-

"""
Remove Release Title OST Indicator Plugin for MusicBrainz Picard.
Removes soundtrack-related information from album titles using regex.
"""

__version__ = "2.1.0"

PLUGIN_NAME = "Remove release title OST indicator"
PLUGIN_AUTHOR = "nrth3rnlb"
PLUGIN_DESCRIPTION = """
The Plugin “Remove Release Title OST Indicator” removes soundtrack-related information (e.g., "OST", "Soundtrack") from album titles.
Supports custom regex patterns, a whitelist, a test field, and multi-step undo via the plugin settings.
Regular expressions are a powerful tool. They can therefore also cause serious damage.
Use https://regex101.com/ to test your pattern.
Use at your own risk.
"""
PLUGIN_VERSION = __version__
PLUGIN_API_VERSIONS = ["2.0", "2.1", "2.2", "2.3"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard.ui.options import register_options_page
from picard.config import TextOption, BoolOption, config
from picard.ui.options import OptionsPage
from .ui_options_remove_releasetitle_ost_indicator import Ui_RemoveReleaseTitleOstIndicatorSettings

from picard import log
from picard.metadata import register_album_metadata_processor
import re

class RemoveReleaseTitleOstIndicatorOptionsPage(OptionsPage):
    """
    Options page for the Remove Release Title OST Indicator plugin.
    """
    NAME = "remove_releasetitle_ost_indicator"
    TITLE = "Remove Release Title OST Indicator"
    PARENT = "plugins"

    DEFAULT_REGEX = r'(\s*(?:(?::|-|–|—|\(|\[)\s*)?(\b(?:Original|Album|Movie|Motion|Picture|Soundtrack|Score|OST|Music|Edition|Inspired|by|from|the|TV|Series|Video|Game|Film|Show)\b)+(?:\)|\])?\s*)+$'
    DEFAULT_WHITELIST = ""
    DEFAULT_UNDO_STACK_SIZE = 5

    options = [
        TextOption("setting", "remove_releasetitle_ost_indicator_regex", DEFAULT_REGEX),
        BoolOption("setting", "remove_releasetitle_ost_indicator_only_soundtrack", True),
        TextOption("setting", "remove_releasetitle_ost_indicator_whitelist", DEFAULT_WHITELIST),
    ]

    def __init__(self, parent=None):
        super(RemoveReleaseTitleOstIndicatorOptionsPage, self).__init__(parent)
        self.ui = Ui_RemoveReleaseTitleOstIndicatorSettings()
        self.ui.setupUi(self)

        # Initialize undo stacks
        self.regex_undo_stack = []
        self.whitelist_undo_stack = []

        # Error label for regex status
        from PyQt5.QtWidgets import QLabel
        self.regex_error_label = QLabel(self)
        self.regex_error_label.setStyleSheet("color: red")
        self.regex_error_label.setVisible(False)
        self.ui.vboxlayout1.addWidget(self.regex_error_label)

        # Undo buttons
        self.ui.undo_regex_button.clicked.connect(self.undo_regex)
        self.ui.undo_whitelist_button.clicked.connect(self.undo_whitelist)

        # Test field logic
        self.ui.test_input.textChanged.connect(self.update_test_output)
        self.ui.regex_pattern.textChanged.connect(self.update_test_output)
        self.ui.whitelist_text.textChanged.connect(self.update_test_output)
        self.ui.only_soundtrack_checkbox.stateChanged.connect(self.update_test_output)

        # Reset button for Regex
        self.ui.reset_button.clicked.connect(self.reset_to_default)

        # Regex validation with every change + undo stack
        self.ui.regex_pattern.textChanged.connect(self.on_regex_changed)
        self.ui.whitelist_text.textChanged.connect(self.on_whitelist_changed)

    def push_undo_stack(self, stack, value):
        # Appends value to stack
        if stack and stack[-1] == value:
            return
        stack.append(value)
        if len(stack) > self.DEFAULT_UNDO_STACK_SIZE:
            stack.pop(0)

    def pop_undo_stack(self, stack, current_value):
        # Returns the last value, removes it from the stack if present and not equal to the current value
        if not stack:
            return current_value
        if stack and stack[-1] == current_value:
            stack.pop()
        if not stack:
            return current_value
        return stack.pop()

    def on_regex_changed(self):
        self.push_undo_stack(self.regex_undo_stack, self.ui.regex_pattern.toPlainText())
        self.validate_regex_pattern()

    def on_whitelist_changed(self):
        self.push_undo_stack(self.whitelist_undo_stack, self.ui.whitelist_text.toPlainText())

    def undo_regex(self):
        prev = self.pop_undo_stack(self.regex_undo_stack, self.ui.regex_pattern.toPlainText())
        self.ui.regex_pattern.blockSignals(True)
        self.ui.regex_pattern.setPlainText(prev)
        self.ui.regex_pattern.blockSignals(False)
        self.validate_regex_pattern()
        self.update_test_output()

    def undo_whitelist(self):
        prev = self.pop_undo_stack(self.whitelist_undo_stack, self.ui.whitelist_text.toPlainText())
        self.ui.whitelist_text.blockSignals(True)
        self.ui.whitelist_text.setPlainText(prev)
        self.ui.whitelist_text.blockSignals(False)
        self.update_test_output()

    def load(self):
        """Loads the current regex, whitelist or default and settings."""
        try:
            current_regex = config.setting["remove_releasetitle_ost_indicator_regex"]
        except KeyError:
            current_regex = self.DEFAULT_REGEX
        self.ui.regex_pattern.setPlainText(current_regex)
        self.validate_regex_pattern()
        self.regex_undo_stack = [current_regex]

        try:
            only_soundtrack = config.setting["remove_releasetitle_ost_indicator_only_soundtrack"]
        except KeyError:
            only_soundtrack = True
        self.ui.only_soundtrack_checkbox.setChecked(only_soundtrack)

        try:
            whitelist = config.setting["remove_releasetitle_ost_indicator_whitelist"]
        except KeyError:
            whitelist = self.DEFAULT_WHITELIST
        self.ui.whitelist_text.setPlainText(whitelist)
        self.whitelist_undo_stack = [whitelist]

        # Testfeld leeren
        self.ui.test_input.setText("")
        self.ui.test_output.setText("")

    def save(self):
        """Saves the current regex, whitelist to config, validates regex and saves checkbox."""
        pattern = self.ui.regex_pattern.toPlainText()
        if self.validate_regex_pattern():
            config.setting["remove_releasetitle_ost_indicator_regex"] = pattern
            config.setting["remove_releasetitle_ost_indicator_only_soundtrack"] = self.ui.only_soundtrack_checkbox.isChecked()
            config.setting["remove_releasetitle_ost_indicator_whitelist"] = self.ui.whitelist_text.toPlainText()

    def reset_to_default(self):
        """Resets the regex to the default pattern."""
        self.ui.regex_pattern.setPlainText(self.DEFAULT_REGEX)

    def validate_regex_pattern(self):
        """Validates the regex pattern and updates UI accordingly."""
        pattern = self.ui.regex_pattern.toPlainText()
        try:
            re.compile(pattern)
            self.ui.regex_pattern.setStyleSheet("")
            self.regex_error_label.setVisible(False)
            return True
        except re.error as e:
            self.ui.regex_pattern.setStyleSheet("background-color: #ffcccc;")
            self.regex_error_label.setText(f"Regex error: {e}")
            self.regex_error_label.setVisible(True)
            return False

    def update_test_output(self):
        """
        Applies the current regex/whitelist/setting to the test input and shows the result.
        """
        album_title = self.ui.test_input.text().strip()
        regex = self.ui.regex_pattern.toPlainText()
        only_soundtrack = self.ui.only_soundtrack_checkbox.isChecked()
        whitelist = self.ui.whitelist_text.toPlainText()
        whitelist_titles = [line.strip().lower() for line in whitelist.splitlines() if line.strip()]
        # Whitelist check
        if album_title.lower() in whitelist_titles:
            self.ui.test_output.setText("Whitelisted – will not be changed!")
            return
        # Assume test input is treated as a soundtrack for preview purposes
        if not only_soundtrack or True:
            try:
                new_title = re.sub(regex, '', album_title, flags=re.IGNORECASE).strip()
                self.ui.test_output.setText(new_title)
            except Exception as e:
                self.ui.test_output.setText(f"Regex error: {e}")
        else:
            self.ui.test_output.setText(album_title)

def remove_releasetitle_ost_indicator(album, metadata, release):
    try:
        regex = config.setting["remove_releasetitle_ost_indicator_regex"]
    except KeyError:
        regex = RemoveReleaseTitleOstIndicatorOptionsPage.DEFAULT_REGEX

    try:
        only_soundtrack = config.setting["remove_releasetitle_ost_indicator_only_soundtrack"]
    except KeyError:
        only_soundtrack = True

    try:
        whitelist = config.setting["remove_releasetitle_ost_indicator_whitelist"]
    except KeyError:
        whitelist = RemoveReleaseTitleOstIndicatorOptionsPage.DEFAULT_WHITELIST

    whitelist_titles = [line.strip().lower() for line in whitelist.splitlines() if line.strip()]
    log.debug(PLUGIN_NAME + ": Using regex pattern %r, only_soundtrack=%r, whitelist=%r", regex, only_soundtrack, whitelist_titles)
    if "album" in metadata:
        album_title = metadata["album"].strip()
        if album_title.lower() in whitelist_titles:
            log.debug(PLUGIN_NAME + ": Album '%s' is whitelisted, skipping removal", album_title)
            return
        if (
            not only_soundtrack or (
                "releasetype" in metadata and "soundtrack" in metadata["releasetype"]
            )
        ):
            new_title = re.sub(regex, '', album_title, flags=re.IGNORECASE).strip()
            metadata["album"] = new_title

log.debug(PLUGIN_NAME + ": registration" )
register_options_page(RemoveReleaseTitleOstIndicatorOptionsPage)
register_album_metadata_processor(remove_releasetitle_ost_indicator)
