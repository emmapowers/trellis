"""Test helpers for Trellis tests."""

from __future__ import annotations

import typing as tp

from trellis.platforms.common.messages import AddPatch
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession


def render_to_tree(session: RenderSession) -> dict[str, tp.Any]:
    """Render and return the serialized tree dict.

    This is a test helper that extracts the tree from the initial render's
    AddPatch. For incremental renders, use render(session) directly to get patches.

    Args:
        session: The RenderSession to render

    Returns:
        Serialized tree dict (same format as the old render() method)

    Raises:
        ValueError: If render() doesn't return an AddPatch with the tree
    """
    patches = render(session)
    if not patches:
        raise ValueError("render() returned no patches")

    first_patch = patches[0]
    if not isinstance(first_patch, AddPatch):
        raise ValueError(f"Expected AddPatch, got {type(first_patch).__name__}")

    return first_patch.node
