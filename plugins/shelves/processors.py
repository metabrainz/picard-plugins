# -*- coding: utf-8 -*-

"""
File processors for loading and saving shelf information.

The code in shelves/processors.py processes files after loading, adding or removing
them in Picard to assign shelves based on the file path, and avoids redundant calls
to get_known_shelves() by retrieving known_shelves once and
passing it to ShelfUtils.get_shelf_from_path. This reduces unnecessary calculations
and improves performance when processing multiple files.
The methods file_post_load_processor and file_post_addition_to_track_processor retrieve
known_shelves and use it directly.
"""

from __future__ import annotations

import traceback
from typing import Any, Dict

from picard import log

from . import clear_album, PLUGIN_NAME, vote_for_shelf, get_album_shelf
from .constants import ShelfConstants
from .utils import ShelfUtils

def file_post_save_processor(file: Any) -> None:
    """
    Process a file after Picard has saved it.

    Args:
        file: Picard file object
    """
    try:
        log.debug("%s: Processing file: %s", PLUGIN_NAME, file.filename)

        album_id = file.metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
        if album_id:
            clear_album(album_id)

    except (KeyError, AttributeError, ValueError) as e:
        log.error("%s: Error in file processor: %s", PLUGIN_NAME, e)
        log.error("%s: Traceback: %s", PLUGIN_NAME, traceback.format_exc())

def file_post_load_processor(file: Any) -> None:
    """
    Process a file after Picard has scanned it.
    Args:
        file: Picard file object
    """
    try:
        log.debug("%s: Processing file: %s", PLUGIN_NAME, file.filename)
        known_shelves = ShelfUtils.get_known_shelves()
        shelf = ShelfUtils.get_shelf_from_path(path=file.filename, known_shelves=known_shelves)

        # file.metadata[ShelfConstants.TAG_KEY] = file_shelf
        ShelfUtils.add_known_shelf(shelf)
        log.debug("%s: Set shelf '%s' for: %s", PLUGIN_NAME, shelf, file.filename)

        album_id = file.metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
        if album_id:
            vote_for_shelf(album_id, shelf)

    except (KeyError, AttributeError, ValueError) as e:
        log.error("%s: Error in file processor: %s", PLUGIN_NAME, e)
        log.error("%s: Traceback: %s", PLUGIN_NAME, traceback.format_exc())

def file_post_addition_to_track_processor(track, file) -> None:
    """
    Process a file after it has been added to a track.
    Args:
        track: Track object
        file: Picard file object
    """
    try:

        log.debug("%s: (file_post_addition_to_track_processor) Processing file: %s", PLUGIN_NAME,
                  file.filename)
        known_shelves = ShelfUtils.get_known_shelves()
        shelf = ShelfUtils.get_shelf_from_path(path=file.filename, known_shelves=known_shelves)

        ShelfUtils.add_known_shelf(shelf)
        log.debug("%s: Set shelf '%s' for: %s", PLUGIN_NAME, shelf, file.filename)

        album_id = file.metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
        if album_id:
            vote_for_shelf(album_id, shelf)
            file.metadata[ShelfConstants.TAG_KEY] = shelf
            track.metadata[ShelfConstants.TAG_KEY] = shelf

    except (KeyError, AttributeError, ValueError) as e:
        log.error("%s: Error in file processor: %s", PLUGIN_NAME, e)
        log.error("%s: Traceback: %s", PLUGIN_NAME, traceback.format_exc())

def file_post_removal_from_track_processor(track, file) -> None:
    """
    Process a file after it has been removed from a track.

    Args:
        track: Track object
        file: Picard file object
    """
    log.debug("%s: (file_post_removal_from_track_processor) Processing file: %s", PLUGIN_NAME,
              file.filename)
    album_id = file.metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
    if album_id:
        clear_album(album_id)


def set_shelf_in_metadata(
        _album: Any, metadata: Dict[str, Any], _track: Any, _release: Any
) -> None:
    """
    Set a shelf in track metadata from album assignment.

    Args:
        _album: Album object (unused, required by Picard API)
        metadata: Track metadata dictionary
        _track: Track object (unused, required by Picard API)
        _release: Release object (unused, required by Picard API)
    """
    album_id = metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
    if not album_id:
        return

    log.debug("%s: set_shelf_in_metadata '%s'", PLUGIN_NAME, album_id)

    shelf_name = get_album_shelf(album_id)
    if shelf_name is not None:
        metadata[ShelfConstants.TAG_KEY] = shelf_name
        log.debug("%s: Set shelf '%s' on track", PLUGIN_NAME, shelf_name)
