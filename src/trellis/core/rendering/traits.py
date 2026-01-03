"""Trait mixins for Element.

Traits provide fluent methods for setting element properties. Each trait
adds one or more methods that modify the element and return self for chaining.

Example:
    html.Div().key("my-div")
    Button(text="Click").key("btn-1")
"""

from __future__ import annotations

import typing as tp

if tp.TYPE_CHECKING:
    from typing import Self

__all__ = ["KeyTrait"]


class KeyTrait:
    """Trait providing fluent key setter for reconciliation.

    The key is used during reconciliation to match elements across renders.
    Elements with the same key are assumed to represent the same logical item,
    even if their position in the tree changes.
    """

    _key: str | None  # Provided by Element

    def key(self, value: str) -> Self:
        """Set the element's key for reconciliation.

        Args:
            value: The key to assign to this element

        Returns:
            self, for method chaining
        """
        self._key = value
        return self
