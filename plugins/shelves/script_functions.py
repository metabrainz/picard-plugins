# -*- coding: utf-8 -*-

"""
Script functions for the Shelves plugin.
"""

from __future__ import annotations

from typing import Any

from picard import config, log

from .constants import ShelfConstants


PLUGIN_NAME = "Shelves"


def func_shelf(parser: Any) -> str:
    """
    Picard script function: `$shelf()`
    Used in the code snippet created by the plugin and can only be used in conjunction with the plugin.
    Returns the shelf name, optionally applying workflow transition.

    Args:
        parser: Picard script parser
    Returns:
        The shelf name (taking workflow transitions into account, if activated)
    """
    shelf = parser.context.get("shelf", "")
    try:
        is_workflow = config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY]  # type: ignore[index]
    except KeyError:
        return shelf

    if not is_workflow:
        return shelf

    try:
        workflow_stage_1 = config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_KEY]  # type: ignore[index]
        workflow_stage_2 = config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_KEY]  # type: ignore[index]
    except KeyError:
        return shelf

    # Apply workflow transition
    if shelf == workflow_stage_1:
        log.debug(
            "%s: Applying workflow transition: '%s' -> '%s'",
            PLUGIN_NAME,
            workflow_stage_1,
            workflow_stage_2,
        )
        return workflow_stage_2

    return shelf
