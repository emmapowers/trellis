"""Debug logging configuration for Trellis.

This module provides a category-based debug logging system that can be
controlled via command-line arguments. Each category maps to a Python
logger that will be set to DEBUG level when enabled.

Usage:
    trellis run -d              # List available categories
    trellis run -d render,state # Enable specific categories
    trellis run -d all          # Enable all debug logging

Categories:
    render    - Render lifecycle, element execution, mount/unmount
    reconcile - Child reconciliation algorithm
    state     - Stateful property access and mutations
    tracked   - TrackedList/Dict/Set mutations
    messages  - WebSocket message handling
    patches   - Detailed patch content
"""

from __future__ import annotations

import logging
from typing import NamedTuple

# Category definitions: shorthand -> logger name
DEBUG_CATEGORIES: dict[str, str] = {
    "render": "trellis.core.rendering",
    "reconcile": "trellis.core.reconcile",
    "state": "trellis.core.state",
    "tracked": "trellis.core.tracked",
    "messages": "trellis.core.message_handler",
    "patches": "trellis.core.rendering",  # Same logger, different semantic
}

# Track which categories are enabled for client sync
_enabled_categories: list[str] = []


class DebugCategory(NamedTuple):
    """Description of a debug category."""

    name: str
    logger: str
    description: str


# Detailed category descriptions for help text
CATEGORY_DESCRIPTIONS: list[DebugCategory] = [
    DebugCategory(
        "render", "trellis.core.rendering", "Render lifecycle, element execution, mount/unmount"
    ),
    DebugCategory("reconcile", "trellis.core.reconcile", "Child reconciliation algorithm"),
    DebugCategory("state", "trellis.core.state", "Stateful property access and mutations"),
    DebugCategory("tracked", "trellis.core.tracked", "TrackedList/Dict/Set mutations"),
    DebugCategory("messages", "trellis.core.message_handler", "WebSocket message handling"),
    DebugCategory("patches", "trellis.core.rendering", "Detailed patch content"),
]


def list_categories() -> str:
    """Return formatted list of available debug categories."""
    max_name_len = max(len(c.name) for c in CATEGORY_DESCRIPTIONS)
    lines = [
        "Available debug categories:",
        "",
        *[f"  {cat.name:<{max_name_len}}  {cat.description}" for cat in CATEGORY_DESCRIPTIONS],
        "",
        "Usage: trellis run -d render,state",
        "       trellis run -d all",
    ]
    return "\n".join(lines)


def parse_categories(categories_str: str) -> list[str]:
    """Parse comma-separated category string into list.

    Args:
        categories_str: Comma-separated category names (e.g., "render,state")

    Returns:
        List of category names

    Raises:
        ValueError: If an unknown category is specified
    """
    if not categories_str:
        return []

    categories = [c.strip().lower() for c in categories_str.split(",")]

    # "all" expands to all categories
    if "all" in categories:
        return list(DEBUG_CATEGORIES.keys())

    # Validate categories
    unknown = [c for c in categories if c not in DEBUG_CATEGORIES]
    if unknown:
        raise ValueError(f"Unknown debug categories: {', '.join(unknown)}")

    return categories


def configure_debug(categories: list[str]) -> None:
    """Configure debug logging for the specified categories.

    Sets the specified category loggers to DEBUG level. The root logger
    (set up by setup_logging() in trellis.py) remains at INFO, so only
    the explicitly enabled categories will emit DEBUG messages.

    Args:
        categories: List of category names to enable
    """
    global _enabled_categories
    _enabled_categories = list(categories)

    # Collect unique loggers to enable
    loggers_to_enable: set[str] = set()
    for category in categories:
        if category in DEBUG_CATEGORIES:
            loggers_to_enable.add(DEBUG_CATEGORIES[category])

    # Set each category's logger to DEBUG
    # These loggers will accept DEBUG messages and propagate to root's handler
    for logger_name in loggers_to_enable:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)


def get_enabled_categories() -> list[str]:
    """Return list of currently enabled debug categories.

    Used to pass debug configuration to the client via HelloResponse.
    """
    return list(_enabled_categories)


def is_debug_enabled(category: str) -> bool:
    """Check if a specific debug category is enabled.

    Args:
        category: Category name to check

    Returns:
        True if the category is enabled
    """
    return category in _enabled_categories or "all" in _enabled_categories
