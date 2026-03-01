"""Trait mixins for Element.

Traits provide fluent methods for setting element properties. Each trait
adds one or more methods that modify the element and return self for chaining.

Traits may participate in the element lifecycle by defining hook methods:
- ``_before_execute(element, state, session)`` — called before component executes
- ``_after_execute(element, state, session)`` — called after component executes
- ``_on_trait_mount(element, state, session)`` — called after initial mount
- ``_on_trait_unmount(element, state, session)`` — called before unmount

Example:
    html.Div().key("my-div")
    Button(text="Click").ref(holder).key("btn-1")
"""

from __future__ import annotations

import typing as tp
import weakref
from dataclasses import dataclass

from trellis.core.rendering.lifecycle import invoke_lifecycle_hook

if tp.TYPE_CHECKING:
    from typing import Self

    from trellis.core.rendering.element import Element
    from trellis.core.rendering.element_state import ElementState
    from trellis.core.rendering.session import RenderSession
    from trellis.core.state.ref import _RefHolder

__all__ = ["KeyTrait", "RefTrait", "RefTraitState", "TraitHooks", "get_trait_hooks"]

_HOOK_NAMES = ("_before_execute", "_after_execute", "_on_trait_mount", "_on_trait_unmount")

# Callable signature for trait hooks: (self/element, element, state, session) -> None
TraitHookFn = tp.Callable[..., None]

# Module-level cache: element class -> list of TraitHooks
_trait_hooks_cache: dict[type, list[TraitHooks]] = {}


@dataclass(frozen=True)
class TraitHooks:
    """Describes which lifecycle hooks a trait class provides.

    Hook fields are either the unbound method from the trait class or None.
    """

    trait_class: type
    before_execute: TraitHookFn | None
    after_execute: TraitHookFn | None
    on_mount: TraitHookFn | None
    on_unmount: TraitHookFn | None

    @property
    def has_before_execute(self) -> bool:
        return self.before_execute is not None

    @property
    def has_after_execute(self) -> bool:
        return self.after_execute is not None

    @property
    def has_on_mount(self) -> bool:
        return self.on_mount is not None

    @property
    def has_on_unmount(self) -> bool:
        return self.on_unmount is not None


def get_trait_hooks(element_class: type) -> list[TraitHooks]:
    """Discover trait hooks for an element class via MRO scan.

    Scans the MRO (excluding the element class itself and ``object``) for
    classes that define lifecycle hook methods in their own ``__dict__``
    (not inherited). Results are cached per element class.
    """
    cached = _trait_hooks_cache.get(element_class)
    if cached is not None:
        return cached

    result: list[TraitHooks] = []
    for cls in type.mro(element_class):
        if cls is element_class or cls is object:
            continue
        hooks: dict[str, TraitHookFn | None] = {}
        has_any = False
        for hook_name in _HOOK_NAMES:
            fn = cls.__dict__.get(hook_name)
            hooks[hook_name] = fn
            if fn is not None:
                has_any = True
        if has_any:
            result.append(
                TraitHooks(
                    trait_class=cls,
                    before_execute=hooks["_before_execute"],
                    after_execute=hooks["_after_execute"],
                    on_mount=hooks["_on_trait_mount"],
                    on_unmount=hooks["_on_trait_unmount"],
                )
            )

    _trait_hooks_cache[element_class] = result
    return result


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


@dataclass
class RefTraitState:
    """Per-element state for RefTrait, stored via ElementState.trait()."""

    exposed_ref: tp.Any = None
    ref_holder: tp.Any = None


class RefTrait:
    """Trait providing fluent ref attachment for parent-child handles.

    Allows a parent component to attach a ref holder to a child element,
    so the parent can access the child's imperative handle after rendering.

    Lifecycle hooks handle ref wiring/unwiring automatically:
    - _before_execute: resets exposed_ref so we detect if child calls set_ref()
    - _after_execute: reads _ref_holder, reconciles with trait state, wires/detaches
    - _on_trait_mount: calls Ref.on_mount if exposed_ref is a Ref
    - _on_trait_unmount: calls Ref.on_unmount, clears state, detaches holder
    """

    id: str  # Provided by Element
    _session_ref: weakref.ref[RenderSession]  # Provided by Element

    def ref(self, holder: _RefHolder[tp.Any]) -> Self:
        """Attach a ref holder to this element.

        Sets _ref_holder as a plain instance attribute. The _after_execute
        hook reads it to wire the ref after execution completes.

        For already-mounted elements (reuse case where _after_execute won't
        fire), wires immediately if exposed_ref is available.

        Args:
            holder: A _RefHolder obtained from get_ref()

        Returns:
            self, for method chaining (e.g. MyChild().ref(holder))
        """
        session = self._session_ref()
        if session is None:
            raise RuntimeError("Cannot attach ref: session has been garbage collected")

        self._ref_holder = holder

        # For already-mounted elements, update trait state and wire immediately
        state = session.states.get(self.id)
        if state is not None and state.mounted:
            ts = state.trait(RefTraitState)
            old_holder = ts.ref_holder
            if old_holder is not None and old_holder is not holder:
                old_holder._detach()
            ts.ref_holder = holder
            if ts.exposed_ref is not None:
                holder._attach(ts.exposed_ref)

        return self

    def _before_execute(
        self, element: Element, state: ElementState, session: RenderSession
    ) -> None:
        """Reset exposed_ref before execute so we detect if child calls set_ref()."""
        ts = state.trait(RefTraitState)
        ts.exposed_ref = None

    def _after_execute(self, element: Element, state: ElementState, session: RenderSession) -> None:
        """Wire ref holder to exposed ref after component executes."""
        ts = state.trait(RefTraitState)
        holder_attr: _RefHolder[tp.Any] | None = getattr(element, "_ref_holder", None)

        if holder_attr is not None:
            # Detach old holder if swapping
            old_holder = ts.ref_holder
            if old_holder is not None and old_holder is not holder_attr:
                old_holder._detach()
            ts.ref_holder = holder_attr

        # Wire ref: connect holder to exposed ref, or detach if child stopped exposing
        if ts.exposed_ref is not None and ts.ref_holder is not None:
            ts.ref_holder._attach(ts.exposed_ref)
        elif ts.exposed_ref is None and ts.ref_holder is not None:
            if ts.ref_holder:  # was previously attached
                ts.ref_holder._detach()

    def _on_trait_mount(
        self, element: Element, state: ElementState, session: RenderSession
    ) -> None:
        """Call Ref.on_mount if exposed_ref is a Ref instance."""
        from trellis.core.state.ref import Ref  # noqa: PLC0415 (circular import)

        ts = state.trait(RefTraitState)
        if ts.exposed_ref is not None and isinstance(ts.exposed_ref, Ref):
            invoke_lifecycle_hook(session, element.id, ts.exposed_ref.on_mount, "Ref.on_mount")

    def _on_trait_unmount(
        self, element: Element | None, state: ElementState, session: RenderSession
    ) -> None:
        """Call Ref.on_unmount, clear exposed_ref, detach holder."""
        from trellis.core.state.ref import Ref  # noqa: PLC0415 (circular import)

        ts = state.trait(RefTraitState)
        if ts.exposed_ref is not None and isinstance(ts.exposed_ref, Ref):
            element_id = element.id if element is not None else ""
            invoke_lifecycle_hook(session, element_id, ts.exposed_ref.on_unmount, "Ref.on_unmount")
            ts.exposed_ref = None

        if ts.ref_holder is not None:
            ts.ref_holder._detach()
