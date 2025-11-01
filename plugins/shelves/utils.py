# -*- coding: utf-8 -*-

"""
Utility functions for managing shelves.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from picard import config, log

from .constants import DEFAULT_SHELVES, ShelfConstants
from .validators import is_likely_shelf_name, validate_shelf_name


PLUGIN_NAME = "Shelves"


def get_known_shelves() -> List[str]:
    """
    Retrieve the list of known shelves from config with validation.
    Returns:
        List of unique, validated shelf names
    """
    try:
        shelves = config.setting[ShelfConstants.CONFIG_SHELVES_KEY]  # type: ignore[index]
    except KeyError:
        shelves = list(DEFAULT_SHELVES.values())

    # Handle string format (legacy)
    if isinstance(shelves, str):
        shelves = [s.strip() for s in shelves.split(",") if s.strip()]
    elif not isinstance(shelves, list):
        log.error(
            "%s: Invalid shelf config type (%s), resetting to defaults",
            PLUGIN_NAME,
            type(shelves).__name__,
        )
        shelves = list(DEFAULT_SHELVES.values())

    # Validate each shelf name
    valid_shelves = []
    for shelf in shelves:
        if not isinstance(shelf, str):
            log.warning(
                "%s: Ignoring non-string shelf: %s", PLUGIN_NAME, repr(shelf)
            )
            continue

        is_valid, message = validate_shelf_name(shelf)
        if is_valid or not message:  # Allow warnings
            valid_shelves.append(shelf)
        else:
            log.warning(
                "%s: Ignoring invalid shelf '%s': %s", PLUGIN_NAME, shelf, message
            )

    return list(set(valid_shelves))


def add_known_shelf(shelf_name: str) -> None:
    """
    Add a shelf name to the list of known shelves.
    Args:
        shelf_name: Name of the shelf to add
    """
    if not shelf_name or not shelf_name.strip():
        return

    shelves = get_known_shelves()
    if shelf_name not in shelves:
        shelves.append(shelf_name)
        config.setting[ShelfConstants.CONFIG_SHELVES_KEY] = shelves  # type: ignore[index]
        log.debug("%s: Added shelf '%s' to known shelves", PLUGIN_NAME, shelf_name)


def remove_known_shelf(shelf_name: str) -> None:
    """
    Remove a shelf name from the list of known shelves.

    Args:
        shelf_name: Name of the shelf to remove
    """
    shelves = get_known_shelves()
    if shelf_name in shelves:
        shelves.remove(shelf_name)
        config.setting[ShelfConstants.CONFIG_SHELVES_KEY] = shelves  # type: ignore[index]
        log.debug(
            "%s: Removed shelf '%s' from known shelves", PLUGIN_NAME, shelf_name
        )


def get_shelf_from_path(path: str, base_path: Optional[str] = None) -> str:
    """
    Extract the shelf name from a file path relative to the configured base path.
    This uses Picard's configured base directory to determine which top-level folder represents the shelf.

    Args:
    	path: Full file path
    	base_path: Optional base path override (uses Picard config if not provided)

    Returns:
    	Extracted shelf	name or "Standard" as fallback
    """
    if base_path is None:
        try:
            base_path = config.setting["move_files_to"]  # type: ignore[index]
        except KeyError:
            log.warning(
                "%s: No base path configured in Picard settings, using fallback detection",
                PLUGIN_NAME,
            )
            return _get_shelf_from_path_fallback(path)

    try:
        log.debug("%s: Extracting shelf from path: %s", PLUGIN_NAME, path)

        path_obj = Path(path).resolve()
        base_obj = Path(base_path).resolve()

        # Check if a path is under base_path
        try:
            relative = path_obj.relative_to(base_obj)
        except ValueError:
            log.debug(
                "%s: Path '%s' is not under base directory '%s'",
                PLUGIN_NAME,
                path,
                base_path,
            )
            return _get_shelf_from_path_fallback(path)

        # The first directory component is the shelf
        parts = relative.parts
        if not parts or parts[0] == path_obj.name:
            # File is directly in the base directory
            log.debug("%s: File is in base directory, no shelf", PLUGIN_NAME)
            return ShelfConstants.DEFAULT_SHELF

        shelf_name = parts[0]
        log.debug("%s: Found potential shelf: %s", PLUGIN_NAME, shelf_name)

        is_likely, reason = is_likely_shelf_name(shelf_name)
        if not is_likely:
            log.warning(
                "%s: '%s' doesn't look like a shelf (%s). Using '%s' instead. "
                "If this is actually a shelf, add it in plugin settings.",
                PLUGIN_NAME,
                shelf_name,
                reason,
                ShelfConstants.DEFAULT_SHELF,
            )
            return ShelfConstants.DEFAULT_SHELF

        log.debug("%s: Confirmed shelf: %s", PLUGIN_NAME, shelf_name)
        return shelf_name

    except (OSError, ValueError, AttributeError) as e:
        log.error(
            "%s: Error extracting shelf from path '%s': %s", PLUGIN_NAME, path, e
        )
        return ShelfConstants.DEFAULT_SHELF


def _get_shelf_from_path_fallback(path: str) -> str:
    """
    Fallback method to extract shelf when a base path is not configured.
    Args:
        path: Full file path
    Returns:
        Best-guess shelf name or "Standard"
    """
    try:
        parts = [p for p in Path(path).parts if p]
        if len(parts) >= 3:
            # Assume: [..., ShelfName, Artist, Album, file]
            shelf_name = parts[-4] if len(parts) >= 4 else parts[-3]

            is_likely, reason = is_likely_shelf_name(shelf_name)
            if is_likely:
                log.debug("%s: Fallback detected shelf: %s", PLUGIN_NAME, shelf_name)
                return shelf_name
            else:
                log.debug(
                    "%s: Fallback shelf '%s' looks suspicious: %s",
                    PLUGIN_NAME,
                    shelf_name,
                    reason,
                )

    except (IndexError, ValueError):
        pass

    return ShelfConstants.DEFAULT_SHELF
