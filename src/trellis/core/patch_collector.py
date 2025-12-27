"""Patch collection during rendering.

PatchCollector accumulates render patches generated during a render pass.
These are internal patches referencing ElementNode objects, not serialized
wire-format patches.
"""

from __future__ import annotations

import logging
import typing as tp

from trellis.core.render_patches import (
    RenderAddPatch,
    RenderPatch,
    RenderRemovePatch,
    RenderUpdatePatch,
)

__all__ = ["PatchCollector"]

logger = logging.getLogger(__name__)


class PatchCollector:
    """Collects render patches generated during a render pass.

    Patches describe changes to the UI tree. These are internal patches
    that reference ElementNode objects directly. Serialization to wire
    format happens in MessageHandler.
    """

    __slots__ = ("_patches",)

    def __init__(self) -> None:
        self._patches: list[RenderPatch] = []

    def emit(self, patch: RenderPatch) -> None:
        """Add a patch to the collection.

        Args:
            patch: The render patch to emit
        """
        # Log patch details
        if isinstance(patch, RenderAddPatch):
            logger.debug(
                "Patch: RenderAddPatch(parent=%s, node=%s)",
                patch.parent_id,
                patch.node.component.name,
            )
        elif isinstance(patch, RenderUpdatePatch):
            logger.debug(
                "Patch: RenderUpdatePatch(id=%s, props_changed=%s, children=%s)",
                patch.node_id,
                patch.props_changed,
                patch.children is not None,
            )
        elif isinstance(patch, RenderRemovePatch):
            logger.debug("Patch: RenderRemovePatch(id=%s)", patch.node_id)

        self._patches.append(patch)

    def get_all(self) -> list[RenderPatch]:
        """Get all collected patches.

        Returns:
            List of all patches (not a copy)
        """
        return self._patches

    def pop_all(self) -> list[RenderPatch]:
        """Pop and return all patches, clearing the collection.

        Returns:
            List of all patches
        """
        patches = list(self._patches)
        self._patches.clear()
        return patches

    def clear(self) -> None:
        """Clear all collected patches."""
        self._patches.clear()

    def __len__(self) -> int:
        """Return number of patches collected."""
        return len(self._patches)

    def __iter__(self) -> tp.Iterator[RenderPatch]:
        """Iterate over collected patches."""
        return iter(self._patches)
