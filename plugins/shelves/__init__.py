# -*- coding: utf-8 -*-

"""
Shelves Plugin for MusicBrainz Picard.

This plugin adds virtual shelf management to MusicBrainz Picard,
allowing music files to be organised by top-level folders.
"""
from __future__ import annotations

import threading
from collections import Counter
from collections import namedtuple
from typing import Any, Dict

from picard import log
from picard.file import register_file_post_load_processor, \
    register_file_post_addition_to_track_processor, register_file_post_removal_from_track_processor
from picard.metadata import register_track_metadata_processor
from picard.script import register_script_function
from picard.ui.itemviews import register_album_action
from picard.ui.options import register_options_page

# Plugin metadata
PLUGIN_NAME = "Shelves"
PLUGIN_AUTHOR = "nrth3rnlb"
PLUGIN_DESCRIPTION = """
The **Shelves** plugin adds virtual shelf management to MusicBrainz Picard, allowing you to organise your music files by top-level folders (shelves) in your music library.

Think of your music library as a physical library with different shelves — one for your standard collection, one for incoming/unprocessed music, one for Christmas music, etc.

## Features

- **Automatic shelf detection** from file paths during scanning
- **Smart detection** prevents artist/album names from being mistaken as shelves
- **Manual shelf assignment** via context menu
- **Shelf management** in plugin settings (add, remove, scan directory)
- **Workflow automation** automatically moves files between shelves (e.g. "Incoming" > "Standard")
- **Script function `$shelf()`** for file naming integration
- **Visual script preview** in settings shows your file naming snippet
"""
PLUGIN_VERSION = "1.6.1"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from .utils import ShelfUtils

LogData = namedtuple('LogData', ['album_id', 'votes', 'winner'])

class ShelfManager:
    """Class to manage shelf state and ensure thread-safety.

    This class is thread-safe for all operations. All accesses to the internal
    dictionaries (_shelves_by_album and _shelf_votes) are protected by a Lock,
    ensuring atomicity and preventing race conditions. External code should only
    interact with the instance via the provided methods.
    """

    def __init__(self):
        self._shelves_by_album: Dict[str, str] = {}
        self._shelf_votes: Dict[str, Counter] = {}
        self._lock = threading.Lock()

    def vote_for_shelf(self, album_id: str, shelf_name: str) -> None:
        """
        Register a shelf vote for an album (used when multiple files suggest different shelves).

        Args:
            album_id: MusicBrainz album ID
            shelf_name: Name of the shelf to vote for
        """
        if not shelf_name or not shelf_name.strip():
            return

        log_data = None
        with self._lock:
            if album_id not in self._shelf_votes:
                self._shelf_votes[album_id] = Counter()

            self._shelf_votes[album_id][shelf_name] += 1

            # Get the shelf with most votes
            winner = self._shelf_votes[album_id].most_common(1)[0][0]

            # Check for conflicts
            if len(self._shelf_votes[album_id]) > 1:
                all_votes = self._shelf_votes[album_id].most_common()
                log_data = LogData(album_id, dict(all_votes), winner)

            self._shelves_by_album[album_id] = winner

        if log_data:
            log.warning(
                "%s: Album %s has files from different shelves. Votes: %s. Using: '%s'",
                PLUGIN_NAME,
                log_data.album_id,
                log_data.votes,
                log_data.winner,
            )

    def get_album_shelf(self, album_id: str) -> str | None:
        """
        Retrieve the shelf name for an album.
        Args:
            album_id: MusicBrainz album ID
        Returns:
            The shelf name for the album. If the album is not found, it returns the default shelf value.
        """
        with self._lock:
            shelf_name = self._shelves_by_album.get(album_id)
            if shelf_name is None:
                log.warning("%s: The shelf of the album %s could not be identified with certainty.", PLUGIN_NAME,
                            album_id)
            return shelf_name

    def clear_album(self, album_id: str) -> None:
        """
        Clear all data for an album.

        Args:
            album_id: MusicBrainz album ID
        """
        with self._lock:
            self._shelves_by_album.pop(album_id, None)
            self._shelf_votes.pop(album_id, None)

# Global instance - initialized once at module import
_shelf_manager = ShelfManager()

def vote_for_shelf(album_id: str, shelf_name: str) -> None:
    """Wrapper for ShelfManager.vote_for_shelf."""
    _shelf_manager.vote_for_shelf(album_id, shelf_name)

def get_album_shelf(album_id: str) -> str | None:
    """Wrapper for ShelfManager.get_album_shelf."""
    return _shelf_manager.get_album_shelf(album_id)

def clear_album(album_id: str) -> None:
    """Wrapper for ShelfManager.clear_album."""
    _shelf_manager.clear_album(album_id)

from .actions import SetShelfAction as _SetShelfActionBase, DetermineShelfAction as _DetermineShelfActionBase
from .options import ShelvesOptionsPage as _ShelvesOptionsPageBase
from .processors import (
    file_post_load_processor,
    file_post_save_processor,
    file_post_addition_to_track_processor,
    file_post_removal_from_track_processor,
    set_shelf_in_metadata
)
from .script_functions import func_shelf as _func_shelf_base

class ShelvesOptionsPage(_ShelvesOptionsPageBase):
    """Wrapper class for the ShelvesOptionsPage to ensure proper plugin registration."""

    def __init__(self, parent=None) -> None:
        """Initialize with the global shelf_manager instance."""
        super().__init__(parent)

class SetShelfAction(_SetShelfActionBase):
    """Wrapper class for SetShelfAction to ensure proper plugin registration."""

    def __init__(self) -> None:
        """Initialize with the global shelf_manager instance."""
        super().__init__()

class DetermineShelfAction(_DetermineShelfActionBase):
    """Wrapper class for DetermineShelfAction to ensure proper plugin registration."""

    def __init__(self) -> None:
        """Initialize with the global shelf_manager instance."""
        super().__init__()

# Wrapper for script function
def func_shelf(parser: Any) -> str:
    """Wrapper for func_shelf to ensure proper plugin registration."""
    return _func_shelf_base(parser)


# Wrapper functions that pass shelf_manager to processors
def _file_post_load_processor_wrapper(file: Any) -> None:
    """Wrapper for file_post_load_processor."""
    file_post_load_processor(file)

def _file_post_addition_to_track_processor(track, file: Any) -> None:
    """Wrapper for file_post_addition_to_track_processor."""
    file_post_addition_to_track_processor(track, file)


def _file_post_save_processor_wrapper(file: Any) -> None:
    """Wrapper for file_post_save_processor."""
    file_post_save_processor(file)


def _set_shelf_in_metadata_wrapper(
        album: Any, metadata: Dict[str, Any], track: Any, release: Any
) -> None:
    """Wrapper for set_shelf_in_metadata."""
    set_shelf_in_metadata(album, metadata, track, release)

def _file_post_removal_from_track_processor(track, file: Any) -> None:
    """Wrapper for file_post_removal_from_track_processor."""
    file_post_removal_from_track_processor(track, file)


log.debug("%s: Registering plugin components", PLUGIN_NAME)

# Register metadata processors
register_track_metadata_processor(_set_shelf_in_metadata_wrapper)

# Register file processors
register_file_post_load_processor(_file_post_load_processor_wrapper)
register_file_post_addition_to_track_processor(_file_post_addition_to_track_processor)
register_file_post_removal_from_track_processor(_file_post_removal_from_track_processor)

# Register context menu actions
register_album_action(SetShelfAction())
register_album_action(DetermineShelfAction())

# Register options page
register_options_page(ShelvesOptionsPage)

# Register a script function for use in file naming
register_script_function(func_shelf, "shelf")
