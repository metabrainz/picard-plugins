# -*- coding: utf-8 -*-

"""
Constants for the Shelves plugin.
"""

from __future__ import annotations


class ShelfConstants:
    """Central constants for the Shelves plugin."""
    # noinspection SpellCheckingInspection
    MUSICBRAINZ_ALBUMID = "musicbrainz_albumid"
    # noinspection SpellCheckingInspection
    TAG_KEY = "shelf"

    BACKUP_TAG_KEY = "shelf_backup"
    DEFAULT_SHELF = "Standard"
    DEFAULT_INCOMING_SHELF = "Incoming"

    # Validation limits
    MAX_SHELF_NAME_LENGTH = 30
    MAX_WORD_COUNT = 3
    INVALID_PATH_CHARS = r'<>:"|?*'

    # Workflow placeholders
    WORKFLOW_STAGE_1_PLACEHOLDER = "~~~workflow_stage_1~~~"
    WORKFLOW_STAGE_2_PLACEHOLDER = "~~~workflow_stage_2~~~"

    # Config keys
    CONFIG_SHELVES_KEY = "shelves_known_shelves"
    CONFIG_ALBUM_SHELF_KEY = "shelves_album_shelf"
    CONFIG_WORKFLOW_STAGE_1_KEY = "shelves_workflow_stage_1"
    CONFIG_WORKFLOW_STAGE_2_KEY = "shelves_workflow_stage_2"
    CONFIG_WORKFLOW_ENABLED_KEY = "shelves_workflow_enabled"
    CONFIG_RENAME_SNIPPET_SKELETON_KEY = "shelves_rename_snippet_skeleton"

    # Album indicators that suggest a name is not a shelf
    ALBUM_INDICATORS = ["Vol.", "Volume", "Disc", "CD", "Part"]


# Default configuration values
DEFAULT_SHELVES = {
    ShelfConstants.CONFIG_WORKFLOW_STAGE_1_KEY: ShelfConstants.DEFAULT_INCOMING_SHELF,
    ShelfConstants.CONFIG_WORKFLOW_STAGE_2_KEY: ShelfConstants.DEFAULT_SHELF,
}
