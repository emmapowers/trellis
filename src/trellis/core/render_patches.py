"""Render-layer patch types.

These patches describe changes to the node tree without serialization.
They reference ElementNode objects directly, allowing the rendering layer
to remain independent of serialization concerns.

Serialization happens at the protocol boundary in MessageHandler, which
converts these to wire-format Patch types from messages.py.
"""

from __future__ import annotations

import typing as tp
from dataclasses import dataclass

if tp.TYPE_CHECKING:
    from trellis.core.rendering import ElementNode

__all__ = [
    "RenderAddPatch",
    "RenderPatch",
    "RenderRemovePatch",
    "RenderUpdatePatch",
]


@dataclass(frozen=True)
class RenderAddPatch:
    """A new node was added to the tree.

    Attributes:
        parent_id: ID of the parent node (None for root)
        children: Parent's new child order after this addition
        node: The ElementNode that was added (not serialized)
    """

    parent_id: str | None
    children: tuple[str, ...]
    node: ElementNode


@dataclass(frozen=True)
class RenderUpdatePatch:
    """A node's props or children changed.

    Attributes:
        node_id: ID of the node that changed
        props_changed: True if props changed (serialization needed)
        children: New child order if changed, None otherwise
    """

    node_id: str
    props_changed: bool
    children: tuple[str, ...] | None


@dataclass(frozen=True)
class RenderRemovePatch:
    """A node was removed from the tree.

    Attributes:
        node_id: ID of the node that was removed
    """

    node_id: str


RenderPatch = RenderAddPatch | RenderUpdatePatch | RenderRemovePatch
