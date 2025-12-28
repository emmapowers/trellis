"""Render-layer patch types and collection.

This module provides patch types that describe changes to the element tree
during rendering, as well as a collector to accumulate them.

Patches reference Element objects directly. Serialization to wire format
happens at the protocol boundary in MessageHandler.
"""

from __future__ import annotations

import logging
import typing as tp
from dataclasses import dataclass

if tp.TYPE_CHECKING:
    from trellis.core.rendering.element import Element

__all__ = [
    "PatchCollector",
    "RenderAddPatch",
    "RenderPatch",
    "RenderRemovePatch",
    "RenderUpdatePatch",
]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RenderAddPatch:
    """A new node was added to the tree.

    Attributes:
        parent_id: ID of the parent node (None for root)
        children: Parent's new child order after this addition
        node: The Element that was added (not serialized)
    """

    parent_id: str | None
    children: tuple[str, ...]
    node: Element


@dataclass(frozen=True)
class RenderUpdatePatch:
    """A node's props or children changed.

    Attributes:
        node_id: ID of the node that changed
        props: Serialized props dict if props changed, None otherwise
        children: New child order if changed, None otherwise
    """

    node_id: str
    props: dict[str, tp.Any] | None
    children: tuple[str, ...] | None


@dataclass(frozen=True)
class RenderRemovePatch:
    """A node was removed from the tree.

    Attributes:
        node_id: ID of the node that was removed
    """

    node_id: str


RenderPatch = RenderAddPatch | RenderUpdatePatch | RenderRemovePatch


class PatchCollector:
    """Collects render patches generated during a render pass.

    Patches describe changes to the UI tree. These are internal patches
    that reference Element objects directly. Serialization to wire
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
                "Patch: RenderUpdatePatch(id=%s, has_props=%s, children=%s)",
                patch.node_id,
                patch.props is not None,
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
