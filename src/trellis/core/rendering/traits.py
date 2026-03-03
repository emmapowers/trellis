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

from trellis.core.rendering.child_ref import ChildRef
from trellis.core.rendering.session import get_active_session
from trellis.utils.logger import logger

if tp.TYPE_CHECKING:
    from typing import Self

    from trellis.core.components.base import Component
    from trellis.core.rendering.session import RenderSession

__all__ = ["ContainerTrait", "KeyTrait", "TraitHooks", "get_trait_hooks"]

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


class ContainerTrait:
    """Mixin providing `with` block support for collecting children.

    Any element class composed with this trait can be used as a context manager
    to collect child elements. This is the core container mechanism — subclasses
    like HtmlContainerTrait may add domain-specific checks.

    Expects the host class to have Element-compatible attributes:
    component, _session_ref, id, props, child_ids.
    """

    # These attributes are provided by Element (or any host dataclass).
    component: Component
    _session_ref: weakref.ref[RenderSession]
    id: str
    props: dict[str, tp.Any]
    child_ids: list[str]

    def __enter__(self) -> Self:
        """Enter a `with` block to collect children for a container component."""
        session = get_active_session()
        if session is None or session.active is None:
            raise RuntimeError(
                f"Cannot use 'with {self.component.name}()' outside of render context. "
                f"Container components must be created during rendering, not in callbacks."
            )

        # Validate: can't provide children as both prop and via with block
        if "children" in self.props:
            raise RuntimeError(
                f"Cannot provide 'children' prop and use 'with' block. "
                f"Component: {self.component.name}"
            )

        # Push new frame for children created in this scope
        session.active.frames.push(parent_id=self.id)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: tp.Any,
    ) -> None:
        """Exit the `with` block, storing ChildRefs in props["children"]."""
        session = get_active_session()
        if session is None or session.active is None:
            return

        child_ids = session.active.frames.pop()

        # Don't process children if an exception occurred
        if exc_type is not None:
            return

        logger.debug(
            "Container __exit__ %s: collected %d children",
            self.component.name,
            len(child_ids),
        )

        # Store collected child IDs (for initial render/reconciliation)
        self.child_ids = list(child_ids)

        # Create ChildRefs for the container to use during execution.
        # These are stable references that survive container re-renders.
        children = [ChildRef(id=cid, _session_ref=self._session_ref) for cid in child_ids]
        self.props["children"] = children

        # Re-store element with child_ids and children props set
        session.elements.store(self)  # type: ignore[arg-type]


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
