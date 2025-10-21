# -*- coding: utf-8 -*-
"""
Remove Soundtrack Plugin for MusicBrainz Picard.
Removes soundtrack-related information from album titles using regex.
Supports custom patterns via the plugin settings.
"""
__all__ = []
__version__ = "1.1.0"

PLUGIN_NAME = "Remove Soundtrack"
PLUGIN_AUTHOR = "nrth3rnlb"
PLUGIN_DESCRIPTION = """
**Remove Soundtrack** removes soundtrack-related information (e.g., "OST", "Soundtrack") from album titles.
Supports custom regex patterns via the plugin settings.
Regular expressions are a powerful tool. They can therefore also cause serious damage.
Use regex101.com to test your pattern.
Use at your own risk.
"""
PLUGIN_VERSION = __version__
PLUGIN_API_VERSIONS = ["2.0", "2.1", "2.2", "2.3"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard.ui.options import register_options_page
from picard.config import TextOption, config
from picard.ui.options import OptionsPage
from .ui_options_remove_soundtrack import Ui_RemoveSoundtrackOptionsPage

from picard import log
from picard.metadata import register_album_metadata_processor
import re

def remove_soundtrack(album, metadata, release):
    custom_regex = config.setting["remove_soundtrack_regex"]
    log.debug(custom_regex)
    if "album" in metadata and "soundtrack" in metadata["releasetype"]:
        metadata["album"] = re.sub(
            custom_regex,
            '',
            metadata["album"],
            flags=re.IGNORECASE
        ).strip()

class RemoveSoundtrackOptionsPage(OptionsPage):
    """Options page for the Remove Soundtrack plugin."""
    NAME = "remove_soundtrack"
    TITLE = "Remove Soundtrack"
    PARENT = "plugins"

    DEFAULT_REGEX = r"(\s*(?::|-|–|—|\(|\[)(?:\s*(?:Original|Album|Movie|Motion|Picture|Soundtrack|Score|OST|Music|Edition|Inspired|by|from|the|TV|Series|Video|Game|Film|Show)){1,}(?:\)|\])?){1,}"


    options = [
        TextOption("setting", "remove_soundtrack_regex", DEFAULT_REGEX),
    ]

    def __init__(self, parent=None):
        super(RemoveSoundtrackOptionsPage, self).__init__(parent)
        self.ui = Ui_RemoveSoundtrackOptionsPage()
        self.ui.setupUi(self)

        # Connect reset button
        self.ui.reset_button.clicked.connect(self.reset_to_default)

    def load(self):
        """Loads the current regex or default."""
        try:
            current_regex = config.setting["remove_soundtrack_regex"]
        except KeyError:
            current_regex = self.DEFAULT_REGEX
        self.ui.regex_pattern.setPlainText(current_regex)

    def save(self):
        """Saves the current regex to config."""
        config.setting["remove_soundtrack_regex"] = self.ui.regex_pattern.toPlainText()

    def reset_to_default(self):
        """Resets the regex to the default pattern."""
        self.ui.regex_pattern.setPlainText(self.DEFAULT_REGEX)


log.debug(PLUGIN_NAME)


register_options_page(RemoveSoundtrackOptionsPage)
register_album_metadata_processor(remove_soundtrack)
