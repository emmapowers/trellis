"""Test helpers for Trellis tests."""

from __future__ import annotations

import typing as tp

from trellis.core.rendering.patches import RenderAddPatch
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.platforms.common.serialization import serialize_node


def render_to_tree(session: RenderSession) -> dict[str, tp.Any]:
    """Render and return the serialized tree dict.

    This is a test helper that extracts the tree from the initial render's
    RenderAddPatch. For incremental renders, use render(session) directly to get patches.

    Args:
        session: The RenderSession to render

    Returns:
        Serialized tree dict (same format as the old render() method)

    Raises:
        ValueError: If render() doesn't return a RenderAddPatch with the tree
    """
    patches = render(session)
    if not patches:
        raise ValueError("render() returned no patches")

    first_patch = patches[0]
    if not isinstance(first_patch, RenderAddPatch):
        raise ValueError(f"Expected RenderAddPatch, got {type(first_patch).__name__}")

    # Serialize the node to wire format for test assertions
    return serialize_node(first_patch.node, session)
