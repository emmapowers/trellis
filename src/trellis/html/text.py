"""Text HTML elements."""

from __future__ import annotations

import typing as tp

from trellis.core.components.base import Component, ElementKind
from trellis.core.rendering.element import Element
from trellis.html._generated_runtime import (
    H1,
    H2,
    H3,
    H4,
    H5,
    H6,
    Abbr,
    Br,
    Code,
    Em,
    Hr,
    Mark,
    P,
    Pre,
    Small,
    Strong,
    Sub,
    Sup,
    Time,
)

__all__ = [
    "H1",
    "H2",
    "H3",
    "H4",
    "H5",
    "H6",
    "Abbr",
    "Br",
    "Code",
    "Em",
    "Hr",
    "Mark",
    "P",
    "Pre",
    "Small",
    "Strong",
    "Sub",
    "Sup",
    "Text",
    "Time",
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
