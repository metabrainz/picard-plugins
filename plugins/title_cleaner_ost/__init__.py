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
PLUGIN_VERSION = "1.3.3"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

import re
import threading
import unicodedata
from typing import List, Dict, Any, Pattern, Optional

from PyQt5 import uic  # type: ignore
from picard import config, log
from picard.metadata import register_album_metadata_processor
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

# from .options_page import RemoveReleaseTitleOstIndicatorOptionsPage

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


from .options_page import RemoveReleaseTitleOstIndicatorOptionsPage as _RemoveReleaseTitleOstIndicatorOptionsPage


class RemoveReleaseTitleOstIndicatorOptionsPage(_RemoveReleaseTitleOstIndicatorOptionsPage):
    """Wrapper class for the ShelvesOptionsPage to ensure proper plugin registration."""

    def __init__(self, parent=None) -> None:
        """Initialize with the global shelf_manager instance."""
        super().__init__(parent)


# Register the plugin
register_options_page(RemoveReleaseTitleOstIndicatorOptionsPage)
register_album_metadata_processor(title_cleaner_ost)
