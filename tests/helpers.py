"""Test helpers for Trellis tests."""

from __future__ import annotations

import typing as tp

from trellis.core.messages import AddPatch
from trellis.core.rendering import RenderTree


def render_to_tree(tree: RenderTree) -> dict[str, tp.Any]:
    """Render and return the serialized tree dict.

    This is a test helper that extracts the tree from the initial render's
    AddPatch. For incremental renders, use tree.render() directly to get patches.

    Args:
        tree: The RenderTree to render

    Returns:
        Serialized tree dict (same format as the old render() method)

    Raises:
        ValueError: If render() doesn't return an AddPatch with the tree
    """
    patches = tree.render()
    if not patches:
        raise ValueError("render() returned no patches")

    first_patch = patches[0]
    if not isinstance(first_patch, AddPatch):
        raise ValueError(f"Expected AddPatch, got {type(first_patch).__name__}")

    return first_patch.node
