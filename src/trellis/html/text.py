"""Handwritten text helpers exposed from trellis.html.

Most text-related HTML wrappers are generated. This module only owns the
special ``Text`` node helper, which renders raw text without a wrapping HTML
element.
"""

from __future__ import annotations

import typing as tp

from trellis.core.components.base import Component, ElementKind
from trellis.core.rendering.element import Element

__all__ = [
    "Text",
]


class TextNode(Component):
    """Special component for raw text nodes."""

    @property
    def is_container(self) -> bool:
        """Text nodes don't accept children."""
        return False

    @property
    def element_kind(self) -> ElementKind:
        """Text nodes have their own kind for special client handling."""
        return ElementKind.TEXT

    @property
    def element_name(self) -> str:
        """Special marker for text nodes."""
        return "__text__"

    def execute(self, /, **props: tp.Any) -> None:
        """Text nodes are leaf nodes."""
        return


_text_node = TextNode("Text")


def Text(value: tp.Any) -> Element:
    """A plain text node without any wrapper element."""
    return _text_node(_text=str(value))
