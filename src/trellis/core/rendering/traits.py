"""Trait mixins for Element.

Traits provide fluent methods for setting element properties. Each trait
adds one or more methods that modify the element and return self for chaining.

Example:
    html.Div().key("my-div")
    Button(text="Click").ref(holder).key("btn-1")
"""

from __future__ import annotations

import typing as tp
import weakref

if tp.TYPE_CHECKING:
    from typing import Self

    from trellis.core.rendering.session import RenderSession
    from trellis.core.state.ref import _RefHolder

__all__ = ["KeyTrait", "RefTrait"]


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


class RefTrait:
    """Trait providing fluent ref attachment for parent-child handles.

    Allows a parent component to attach a ref holder to a child element,
    so the parent can access the child's imperative handle after rendering.
    """

    id: str  # Provided by Element
    _session_ref: weakref.ref[RenderSession]  # Provided by Element

    def ref(self, holder: _RefHolder[tp.Any]) -> Self:
        """Attach a ref holder to this element.

        The holder will be wired to the child's exposed_ref after the child
        executes. If a different holder was previously attached, the old one
        is detached first.

        Args:
            holder: A _RefHolder obtained from get_ref()

        Returns:
            self, for method chaining (e.g. MyChild().ref(holder))
        """
        session = self._session_ref()
        if session is None:
            raise RuntimeError("Cannot attach ref: session has been garbage collected")

        state = session.states.get_or_create(self.id)

        # Detach old holder if swapping
        old_holder = state.ref_holder
        if old_holder is not None and old_holder is not holder:
            old_holder._detach()

        state.ref_holder = holder

        # If exposed_ref is already set (e.g. re-render), wire immediately
        if state.exposed_ref is not None:
            holder._attach(state.exposed_ref)

        return self
