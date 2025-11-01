# -*- coding: utf-8 -*-

"""
Validation functions for shelf names.
"""

from __future__ import annotations

from typing import Optional, Tuple

from .constants import DEFAULT_SHELVES, ShelfConstants


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


def is_likely_shelf_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Check if a name is likely a shelf name or an artist/album name.

    Args:
        name: The name to validate

    Returns:
        Tuple of (is_likely_shelf, reason_if_not)
    """
    if not name:
        return False, "Empty name"

    # Default shelves are always valid
    if name in DEFAULT_SHELVES.values():
        return True, None

    # Known shelves are valid - import here to avoid circular dependency
    from .utils import get_known_shelves
    if name in get_known_shelves():
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
