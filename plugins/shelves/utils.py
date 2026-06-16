# -*- coding: utf-8 -*-

"""
Utility functions for managing shelves.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

from picard import config, log

from . import PLUGIN_NAME
from .constants import DEFAULT_SHELVES, ShelfConstants

class ShelfUtils:
    """
    Utility functions for shelf management.
    Call set_shelf_manager() during plugin initialization to set the ShelfManager instance.
    """
    @staticmethod
    def _determine_shelf_recursive(path, known_shelves, base_path):
        """
        Recursively determine the shelf from a given path.

        Args:
            path: The file path to analyze
            known_shelves: List of known shelf names (passed from caller to avoid redundant calls)
            base_path: The base path to use for relative calculations
        """
        workflow_stage_1 = config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_KEY]  # type: ignore[index]
        workflow_stage_2 = config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_KEY]  # type: ignore[index]
        try:
            log.debug("%s: Extracting shelf from path: %s", PLUGIN_NAME, path)

            path_obj = Path(path).resolve()
            base_obj = Path(base_path).resolve()

            # Check if a path is under base_path
            try:
                relative = path_obj.relative_to(base_obj)
            except ValueError:
                log.debug(
                    "%s: Path '%s' is not under base directory '%s', setting shelf to '%s'",
                    PLUGIN_NAME,
                    path,
                    base_path, workflow_stage_1
                )
                return workflow_stage_1

            # The first directory component is the shelf
            parts = relative.parts
            if not parts or parts[0] == path_obj.name:
                # File is directly in the base directory
                log.debug("%s: File is in base directory, setting shelf to '%s'", PLUGIN_NAME,
                          workflow_stage_2)
                return workflow_stage_2

            shelf_name = parts[0]
            log.debug("%s: Found potential shelf: %s", PLUGIN_NAME, shelf_name)

            is_likely, reason = ShelfUtils.is_likely_shelf_name(shelf_name, known_shelves=known_shelves)
            if not is_likely:
                log.warning(
                    "%s: '%s' doesn't look like a shelf (%s). Using '%s' instead. "
                    "If this is actually a shelf, add it in plugin settings.",
                    PLUGIN_NAME,
                    shelf_name,
                    reason,
                    workflow_stage_2,
                )
                return workflow_stage_2

            log.debug("%s: Confirmed shelf: %s", PLUGIN_NAME, shelf_name)
            return shelf_name

        except (OSError, ValueError, AttributeError) as e:
            log.error(
                "%s: Error extracting shelf from path '%s': %s", PLUGIN_NAME, path, e
            )
            return workflow_stage_2


    @staticmethod
    def validate_shelf_name(name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a shelf name for use as a directory name.

        Args:
            name: The shelf name to validate

        Returns:
            Tuple of (is_valid, warning_message)
        """
        if not name or not name.strip():
            return False, "Shelf name cannot be empty"

        found_invalid = [c for c in ShelfConstants.INVALID_PATH_CHARS if c in name]
        if found_invalid:
            return False, f"Contains invalid characters: {', '.join(found_invalid)}"

        if name.startswith(".") or name.endswith("."):
            return (
                True,
                "Warning: Names starting or ending with '.' may cause issues "
                "on some systems",
            )

        if name in [".", ".."]:
            return False, "Cannot use '.' or '..' as shelf name"

        return True, None

    @staticmethod
    def is_likely_shelf_name(name: str, known_shelves: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Check if a name is likely a shelf name or an artist/album name.

        Args:
            name: The name to validate
            known_shelves: List of known shelf names

        Returns:
            Tuple of (is_likely_shelf, reason_if_not)
        """
        if not name:
            return False, "Empty name"

        # Default shelves are always valid
        if name in DEFAULT_SHELVES.values():
            return True, None

        if name in known_shelves:
            return True, None

        # Heuristics for suspicious names
        suspicious_reasons = []

        # Contains ` - ` (typical for "Artist - Album")
        if " - " in name:
            suspicious_reasons.append(
                "contains ' - ' (typical for 'Artist - Album' format)"
            )

        # Too long
        if len(name) > ShelfConstants.MAX_SHELF_NAME_LENGTH:
            suspicious_reasons.append(f"too long ({len(name)} chars)")

        # Too many words
        word_count = len(name.split())
        if word_count > ShelfConstants.MAX_WORD_COUNT:
            suspicious_reasons.append(f"too many words ({word_count})")

        # Contains album indicators
        if any(indicator in name for indicator in ShelfConstants.ALBUM_INDICATORS):
            suspicious_reasons.append("contains album indicator (Vol., Disc, etc.)")

        if suspicious_reasons:
            return False, "; ".join(suspicious_reasons)

        return True, None

    @staticmethod
    def get_known_shelves() -> List[str]:
        """
        Retrieve the list of known shelves from config with validation.
        Returns:
            List of unique, validated shelf names
        """
        shelves = config.setting[ShelfConstants.CONFIG_SHELVES_KEY]  # type: ignore[index]

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

            is_valid, message = ShelfUtils.validate_shelf_name(shelf)
            if is_valid or not message:  # Allow warnings
                valid_shelves.append(shelf)
            else:
                log.warning(
                    "%s: Ignoring invalid shelf '%s': %s", PLUGIN_NAME, shelf, message
                )
        log.debug("%s: Known shelves: %s", PLUGIN_NAME, valid_shelves)
        return sorted(list(set(valid_shelves)))

    @staticmethod
    def get_existing_dirs() -> list[str]:
        """
        Load existing directories from the music directory.
        Returns: List of directory names
        """
        music_dir_str = config.setting["move_files_to"]  # type: ignore[index]
        music_dir = Path(music_dir_str)

        shelves_found = [entry.name for entry in music_dir.iterdir() if entry.is_dir()]
        return shelves_found

    @staticmethod
    def add_known_shelf(shelf_name: str) -> None:
        """
        Add a shelf name to the list of known shelves.
        Args:
            shelf_name: Name of the shelf to add
        """
        if not shelf_name or not shelf_name.strip():
            return

        shelves = ShelfUtils.get_known_shelves()
        if shelf_name not in shelves:
            shelves.append(shelf_name)
            config.setting[ShelfConstants.CONFIG_SHELVES_KEY] = sorted(shelves)  # type: ignore[index]
            log.debug("%s: Added shelf '%s' to known shelves", PLUGIN_NAME, shelf_name)

    @staticmethod
    def remove_known_shelf(shelf_name: str) -> None:
        """
        Remove a shelf name from the list of known shelves.

        Args:
            shelf_name: Name of the shelf to remove
        """
        shelves = ShelfUtils.get_known_shelves()
        if shelf_name in shelves:
            shelves.remove(shelf_name)
            config.setting[ShelfConstants.CONFIG_SHELVES_KEY] = shelves  # type: ignore[index]
            log.debug(
                "%s: Removed shelf '%s' from known shelves", PLUGIN_NAME, shelf_name
            )

    @staticmethod
    def get_shelf_from_path(path: str, known_shelves: List[str], base_path: Optional[str] = None) -> str:
        """
        Extract the shelf name from a file path relative to the configured base path.
        This uses Picard's configured base directory to determine which top-level folder represents the shelf.

        Args:
            known_shelves: List of known shelf names
            path: Full file path
            base_path: Optional base path override (uses Picard config if not provided)

        Returns:
            Extracted shelf name or "Standard" as fallback
        """
        if base_path is None:
            try:
                base_path = config.setting["move_files_to"]  # type: ignore[index]
            except KeyError:
                log.warning(
                    "%s: No base path configured in Picard settings, set shelf to '%s'",
                    PLUGIN_NAME, config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_KEY]  # type: ignore[index]
                )
                return config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_KEY]  # type: ignore[index]

        return ShelfUtils._determine_shelf_recursive(path, known_shelves, base_path)
