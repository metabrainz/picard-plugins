# -*- coding: utf-8 -*-

"""
Title Cleaner OST Plugin for MusicBrainz Picard.
Removes soundtrack-related information from album titles using regex.
"""

__version__ = "1.2.0"

PLUGIN_NAME = "Title Cleaner OST"
PLUGIN_AUTHOR = "nrth3rnlb"
PLUGIN_DESCRIPTION = """
The Plugin “Title Cleaner OST” removes soundtrack-related information (e.g., "OST", "Soundtrack") from album titles.
Supports custom regex patterns, a whitelist and a test field via the plugin settings.
Regular expressions are a powerful tool. They can therefore also cause serious damage.
Use https://regex101.com/ to test your pattern.
Use at your own risk.
"""
PLUGIN_VERSION = __version__
PLUGIN_API_VERSIONS = ["2.7", "2.8"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard.ui.options import register_options_page
from picard import config, log
from picard.config import BoolOption, TextOption
from picard.ui.options import OptionsPage
from .ui_title_cleaner_ost_config import Ui_RemoveReleaseTitleOstIndicatorSettings

from picard.metadata import register_album_metadata_processor
import re
import unicodedata

class RemoveReleaseTitleOstIndicatorOptionsPage(OptionsPage):
    """
    Options page for the Title Cleaner OST plugin.
    """
    NAME = "title_cleaner_ost"
    ui: Ui_RemoveReleaseTitleOstIndicatorSettings
    TITLE = "Title Cleaner OST"
    PARENT = "plugins"

    DEFAULT_REGEX = r'(\s*(?:(?::|-|–|—|\(|\[)\s*)?(\b(?:Original|Album|Movie|Motion|Picture|Soundtrack|Score|OST|Music|Edition|Inspired|by|from|the|TV|Series|Video|Game|Film|Show)\b)+(?:\)|\])?\s*)+$'
    DEFAULT_WHITELIST = ""


    options = [
        TextOption("setting", "title_cleaner_ost_regex", DEFAULT_REGEX),
        BoolOption("setting", "title_cleaner_ost_only_soundtrack", True),
        TextOption("setting", "title_cleaner_ost_whitelist", DEFAULT_WHITELIST),
    ]

    def __init__(self, parent=None):
        super(RemoveReleaseTitleOstIndicatorOptionsPage, self).__init__(parent)
        self.ui = Ui_RemoveReleaseTitleOstIndicatorSettings()
        self.ui.setupUi(self)

        # Compiled regex cache for preview
        self.compiled_regex = None

        # Error label for regex status
        from PyQt5.QtWidgets import QLabel
        self.regex_error_label = QLabel(self)
        self.regex_error_label.setStyleSheet("color: red")
        self.regex_error_label.setVisible(False)
        self.ui.vboxlayout1.addWidget(self.regex_error_label)

        # Test field logic
        self.ui.test_input.textChanged.connect(self.update_test_output)
        self.ui.regex_pattern.textChanged.connect(self.update_test_output)
        self.ui.whitelist_text.textChanged.connect(self.update_test_output)
        self.ui.only_soundtrack_checkbox.stateChanged.connect(self.update_only_applies_to)

        # Reset button for Regex
        self.ui.reset_button.clicked.connect(self.reset_to_default)

        # Regex validation with every change
        self.ui.regex_pattern.textChanged.connect(self.on_regex_changed)

    def on_regex_changed(self):
        self.validate_regex_pattern()


    def load(self):
        """Loads the current regex, whitelist or default and settings."""
        try:
            current_regex = config.setting["title_cleaner_ost_regex"]
        except KeyError:
            current_regex = self.DEFAULT_REGEX
        self.ui.regex_pattern.setPlainText(current_regex)
        self.validate_regex_pattern()

        try:
            only_soundtrack = config.setting["title_cleaner_ost_only_soundtrack"]
        except KeyError:
            only_soundtrack = True
        self.ui.only_soundtrack_checkbox.setChecked(only_soundtrack)

        if self.ui.only_soundtrack_checkbox.isChecked():
            self.ui.only_applies_to.setText("soundtracks")
        else:
            self.ui.only_applies_to.clear()

        try:
            whitelist = config.setting["title_cleaner_ost_whitelist"]
        except KeyError:
            whitelist = self.DEFAULT_WHITELIST
        self.ui.whitelist_text.setPlainText(whitelist)


        # Testfeld leeren
        self.ui.test_input.setText("")
        self.ui.test_output.setText("")

    def save(self):
        """Saves the current regex, whitelist to config, validates regex, and saves checkbox."""
        pattern = self.ui.regex_pattern.toPlainText()
        # Try to compile the regex again on save with graceful fallback
        try:
            re.compile(pattern, flags=re.IGNORECASE)
            config.setting["title_cleaner_ost_regex"] = pattern
            config.setting["title_cleaner_ost_only_soundtrack"] = self.ui.only_soundtrack_checkbox.isChecked()
            config.setting["title_cleaner_ost_whitelist"] = self.ui.whitelist_text.toPlainText()
        except re.error as e:
            log.error(PLUGIN_NAME + ": Failed to save regex pattern: %s", e)
            # Fall back to not saving invalid regex
            config.setting["remove_releasetitle_ost_indicator_only_soundtrack"] = self.ui.only_soundtrack_checkbox.isChecked()
            config.setting["remove_releasetitle_ost_indicator_whitelist"] = self.ui.whitelist_text.toPlainText()

    def reset_to_default(self):
        """Resets the regex to the default pattern."""
        self.ui.regex_pattern.setPlainText(self.DEFAULT_REGEX)

    def validate_regex_pattern(self):
        """Validates the regex pattern, compiles it for caching, and updates UI accordingly."""
        pattern = self.ui.regex_pattern.toPlainText()
        try:
            self.compiled_regex = re.compile(pattern, flags=re.IGNORECASE)
            self.ui.regex_pattern.setStyleSheet("")
            self.regex_error_label.setVisible(False)
            return True
        except re.error as e:
            log.debug(PLUGIN_NAME + ": Regex validation error: %s", e)
            self.compiled_regex = None
            self.ui.regex_pattern.setStyleSheet("background-color: #ffcccc;")
            self.regex_error_label.setText(f"Regex error: {e}")
            self.regex_error_label.setVisible(True)
            return False

    def update_only_applies_to(self):
        only_soundtrack = self.ui.only_soundtrack_checkbox.isChecked()
        if only_soundtrack:
            self.ui.only_applies_to.setText("soundtracks")
        else:
            self.ui.only_applies_to.clear()

    def update_test_output(self):
        """
        Applies the current regex/whitelist/setting to the test input and shows the result.
        Always shows a preview but indicates when only_soundtrack is enabled.
        """
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
    try:
        regex = config.setting["title_cleaner_ost_regex"]
    except KeyError:
        regex = RemoveReleaseTitleOstIndicatorOptionsPage.DEFAULT_REGEX

    try:
        only_soundtrack = config.setting["title_cleaner_ost_only_soundtrack"]
    except KeyError:
        only_soundtrack = True

    try:
        whitelist = config.setting["title_cleaner_ost_whitelist"]
    except KeyError:
        whitelist = RemoveReleaseTitleOstIndicatorOptionsPage.DEFAULT_WHITELIST

    # Normalise whitelist titles using Unicode NFC normalization
    whitelist_titles = [
        unicodedata.normalize('NFC', line.strip()).lower()
        for line in whitelist.splitlines() if line.strip()
    ]

    log.debug(PLUGIN_NAME + ": Using regex pattern %r, only_soundtrack=%r, whitelist=%r", regex, only_soundtrack, whitelist_titles)

    if "album" in metadata:
        album_title = metadata["album"].strip()
        normalized_title = unicodedata.normalize('NFC', album_title).lower()

        if normalized_title in whitelist_titles:
            log.debug(PLUGIN_NAME + ": Album '%s' is whitelisted, skipping removal", album_title)
            return

        if (
            not only_soundtrack or (
                "releasetype" in metadata and "soundtrack" in metadata["releasetype"]
            )
        ):
            try:
                compiled_regex = re.compile(regex, flags=re.IGNORECASE)
                new_title = compiled_regex.sub('', album_title)
                # Normalise whitespace and strip leading/trailing whitespace
                new_title = ' '.join(new_title.split()).strip()
                metadata["album"] = new_title
                log.debug(PLUGIN_NAME + ": Changed album title from '%s' to '%s'", album_title, new_title)
            except re.error as e:
                log.error(PLUGIN_NAME + ": Regex application error: %s", e)

log.debug(PLUGIN_NAME + ": registration" )
register_options_page(RemoveReleaseTitleOstIndicatorOptionsPage)
register_album_metadata_processor(title_cleaner_ost)
