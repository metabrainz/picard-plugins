# -*- coding: utf-8 -*-

"""
Shelf manager for tracking album shelf assignments.
"""

from __future__ import annotations

from collections import Counter
from typing import Dict

from .constants import DEFAULT_SHELVES, ShelfConstants

from picard import log


PLUGIN_NAME = "Shelves"


class ShelfManager:
    """Manages shelf assignments and state with conflict detection."""

    def __init__(self) -> None:
        """Initialise the shelf manager."""
        self._shelves_by_album: Dict[str, str] = {}
        self._shelf_votes: Dict[str, Counter] = {}

    def vote_for_shelf(self, album_id: str, shelf_name: str) -> None:
        """
        Register a shelf vote for an album (used when multiple files suggest different shelves).

        Args:
            album_id: MusicBrainz album ID
            shelf_name: Name of the shelf to vote for
        """
        if not shelf_name or not shelf_name.strip():
            return

        if album_id not in self._shelf_votes:
            self._shelf_votes[album_id] = Counter()

        self._shelf_votes[album_id][shelf_name] += 1

        # Get the shelf with most votes
        winner = self._shelf_votes[album_id].most_common(1)[0][0]

        # Check for conflicts
        if len(self._shelf_votes[album_id]) > 1:
            all_votes = self._shelf_votes[album_id].most_common()
            log.warning(
                "%s: Album %s has files from different shelves. Votes: %s. Using: '%s'",
                PLUGIN_NAME,
                album_id,
                dict(all_votes),
                winner,
            )

        self._shelves_by_album[album_id] = winner

    def get_album_shelf(self, album_id: str) -> str | None:
        """
        Retrieve the shelf name for an album.
        Args:
            album_id: MusicBrainz album ID
        Returns:
            The shelf name for the album. If the album is not found, it returns the default shelf value.
        """
        if self._shelves_by_album.get(album_id) is not None:
            return self._shelves_by_album.get(album_id)
        log.warning("%s: The shelf of the album %s could not be identified with certainty.", PLUGIN_NAME, album_id)

        return None

    def clear_album(self, album_id: str) -> None:
        """
        Clear all data for an album.

        Args:
            album_id: MusicBrainz album ID
        """
        self._shelves_by_album.pop(album_id, None)
        self._shelf_votes.pop(album_id, None)
