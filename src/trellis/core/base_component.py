"""Base component class for the Trellis UI framework.

This module provides the abstract Component base class that all components
inherit from. Components are the building blocks of Trellis UIs.

The Component class implements the IComponent protocol and provides:
- `__call__()`: Creates an ElementDescriptor (phase 1 - no execution)
- `execute()`: Abstract method that subclasses implement for rendering (phase 2)

Example:
    ```python
    @dataclass(kw_only=True)
    class MyComponent(Component):
        name: str = "MyComponent"

        def execute(self, node: Element, **props) -> None:
            Text(f"Hello, {props.get('name', 'World')}!")
    ```

See Also:
    - `FunctionalComponent`: Concrete implementation using decorated functions
    - `ElementDescriptor`: The descriptor type returned by `__call__()`
"""

from __future__ import annotations

import typing as tp
from abc import ABC, abstractmethod
from dataclasses import dataclass

from trellis.core.rendering import (
    Element,
    ElementDescriptor,
    _descriptor_stack,
    freeze_props,
)

T = tp.TypeVar("T", bound=Element, default=Element)


@dataclass(kw_only=True)
class Component(ABC, tp.Generic[T]):
    """Abstract base class for all Trellis components.

    Components define reusable UI elements. They follow a two-phase rendering model:

    1. **Descriptor Phase**: When called (e.g., `Button(text="Click")`), creates an
       immutable ElementDescriptor that describes the component invocation.

    2. **Execution Phase**: When the reconciler determines this component needs to
       render, it calls `execute()` which produces child descriptors.

    Attributes:
        name: Human-readable component name (used for debugging and error messages)
        elementType: The Element subclass to use for this component's nodes

    Type Parameters:
        T: The Element type this component produces (defaults to Element)
    """

    name: str
    elementType: type[Element] = Element

    def __call__(self, /, **props: tp.Any) -> ElementDescriptor:
        """Create an ElementDescriptor for this component invocation.

        This is phase 1 of rendering - NO execution occurs here. The descriptor
        captures the component reference, key, and props for later reconciliation.

        If called inside a `with` block (and this component doesn't accept children),
        the descriptor is automatically added to the parent's pending children.

        Args:
            **props: Properties to pass to the component. The special `key` prop
                is extracted for reconciliation and not passed to `execute()`.

        Returns:
            An immutable ElementDescriptor describing this component invocation.

        Example:
            ```python
            # Creates descriptor, doesn't execute yet
            desc = Button(text="Click me", key="btn-1")

            # Inside a with block, auto-collected
            with Column():
                Button(text="First")   # Added to Column's children
                Button(text="Second")  # Added to Column's children
            ```
        """
        key = ""
        if "key" in props:
            key = str(props.pop("key"))

        descriptor = ElementDescriptor(
            component=self,
            key=key,
            props=freeze_props(props),
        )

        # Auto-collect: add to parent descriptor's pending children (if any)
        # BUT only if this component doesn't have a children param - those will
        # be added in __exit__ of the with block instead
        has_children_param = getattr(self, "_has_children_param", False)
        if _descriptor_stack and not has_children_param:
            _descriptor_stack[-1].append(descriptor)

        return descriptor

    @abstractmethod
    def execute(self, /, node: T, **props: tp.Any) -> None:
        """Execute this component to produce child descriptors.

        This is phase 2 of rendering - called by the reconciler when the
        component needs to render (new mount, props changed, or marked dirty).

        During execution, the component should create child components by
        calling them (e.g., `Text("Hello")`), which creates descriptors that
        are collected and reconciled after this method returns.

        For container components (those with a `children` parameter), the
        `children` prop contains a list of ElementDescriptors. The component
        should call `child()` on each to mount them at the desired location.

        Args:
            node: The Element instance this component is rendering into.
                  Can be used to access local state via `node._local_state`.
            **props: The properties passed to this component invocation.
                     For containers, includes `children: list[ElementDescriptor]`.

        Example:
            ```python
            def execute(self, node: Element, **props) -> None:
                # Simple component - just create children
                Text(f"Count: {props['count']}")
                Button(text="Increment", on_click=props['on_increment'])

            # Container component
            def execute(self, node: Element, children: list, **props) -> None:
                for child_desc in children:
                    child_desc()  # Mount each child
            ```
        """
        pass


def fixup_children(parent: Element, children: list[Element]) -> None:
    """Update parent references and depths for a list of child elements.

    Called by the reconciler after reconciling children to ensure the
    tree structure is consistent.

    Args:
        parent: The parent element
        children: List of child elements to fix up
    """
    for child in children:
        child.parent = parent
        child.depth = parent.depth + 1
