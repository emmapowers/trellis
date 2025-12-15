"""Base component class for the Trellis UI framework.

This module provides the abstract Component base class that all components
inherit from. Components are the building blocks of Trellis UIs.

The Component class implements the IComponent protocol and provides:
- `__call__()`: Creates an ElementNode (placement phase - no rendering)
- `render()`: Abstract method that subclasses implement for rendering

Example:
    ```python
    class MyComponent(Component):
        def __init__(self, name: str = "MyComponent") -> None:
            super().__init__(name)

        def render(self, **props) -> None:
            Text(f"Hello, {props.get('name', 'World')}!")
    ```

See Also:
    - `CompositionComponent`: Concrete implementation using decorated functions
    - `ElementNode`: The node type returned by `__call__()`
"""

from __future__ import annotations

import typing as tp
from abc import ABC, abstractmethod

from trellis.core.rendering import (
    ElementKind,
    ElementNode,
    freeze_props,
    get_active_render_tree,
)

__all__ = ["Component"]


class Component(ABC):
    """Abstract base class for all Trellis components.

    Components define reusable UI elements. They follow a two-phase rendering model:

    1. **Placement Phase**: When called (e.g., `Button(text="Click")`), creates an
       immutable ElementNode that describes the component invocation.

    2. **Render Phase**: When the reconciler determines this component needs to
       render, it calls `render()` which produces child descriptors.

    Attributes:
        name: Human-readable component name (used for debugging and error messages)
        element_kind: The kind of element (REACT_COMPONENT, JSX_ELEMENT, TEXT)
        element_name: The type name used to render this on the client
    """

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @property
    @abstractmethod
    def element_kind(self) -> ElementKind:
        """The kind of element (REACT_COMPONENT, JSX_ELEMENT, or TEXT).

        Must be overridden by subclasses:
        - Most components return REACT_COMPONENT
        - HTML elements return JSX_ELEMENT
        - Text nodes return TEXT
        """
        ...

    @property
    @abstractmethod
    def element_name(self) -> str:
        """The element type name used to render this component on the client.

        For CompositionComponents, this is always "CompositionComponent".
        For ReactComponentBase subclasses, this is the specific React component name.
        For HTML elements, this is the tag name (e.g., "div").
        """
        ...

    @property
    def _has_children_param(self) -> bool:
        """Whether this component accepts children via `with` block.

        Override in subclasses that support children. Default is False.
        """
        return False

    def _place(self, /, **props: tp.Any) -> ElementNode:
        """Place this component, creating an ElementNode.

        This is the placement phase - NO execution occurs here. The node
        captures the component reference, key, and props for later reconciliation.

        If called inside a `with` block (and this component doesn't accept children),
        the node is automatically added to the parent's pending children.

        Args:
            **props: Properties to pass to the component. The special `key` prop
                is extracted for reconciliation and not passed to `render()`.

        Returns:
            An immutable ElementNode describing this component invocation.

        Example:
            ```python
            # Creates node, doesn't render yet
            node = Button(text="Click me", key="btn-1")

            # Inside a with block, auto-collected
            with Column():
                Button(text="First")   # Added to Column's children
                Button(text="Second")  # Added to Column's children
            ```
        """
        key: str | None = None
        if "key" in props:
            raw_key = props.pop("key")
            if raw_key is not None:
                key = str(raw_key)

        node = ElementNode(
            component=self,
            key=key,
            props=freeze_props(props),
        )

        # Ensure we're inside a render context - components cannot be created
        # in callbacks or other code outside of rendering
        ctx = get_active_render_tree()
        if ctx is None:
            raise RuntimeError(
                f"Cannot create component '{self.name}' outside of render context. "
                f"Components must be created during rendering, not in callbacks."
            )

        # Auto-collect: add to parent node's pending children (if any)
        # BUT only if this component doesn't have a children param - those will
        # be added in __exit__ of the with block instead
        if ctx.has_active_frame() and not self._has_children_param:
            ctx.add_to_current_frame(node)
            # Mark as auto-collected to prevent double-collection if used with `with`
            object.__setattr__(node, "_auto_collected", True)

        return node

    def __call__(self, /, **props: tp.Any) -> ElementNode:
        """Create an ElementNode for this component invocation.

        Delegates to _place(). This is the standard way to invoke a component.

        Args:
            **props: Properties to pass to the component.

        Returns:
            An immutable ElementNode describing this component invocation.
        """
        return self._place(**props)

    @abstractmethod
    def render(self, /, **props: tp.Any) -> None:
        """Render this component to produce child nodes.

        Called by RenderTree when the component needs to render
        (new mount, props changed, or marked dirty).

        During rendering, the component should create child components by
        calling them (e.g., `Text("Hello")`), which creates nodes that
        are collected and reconciled after this method returns.

        For container components (those with a `children` parameter), the
        `children` prop contains a list of ElementNodes. The component
        should call `child()` on each to mount them at the desired location.

        Args:
            **props: The properties passed to this component invocation.
                     For containers, includes `children: list[ElementNode]`.

        Example:
            ```python
            def render(self, **props) -> None:
                # Simple component - just create children
                Text(f"Count: {props['count']}")
                Button(text="Increment", on_click=props['on_increment'])

            # Container component
            def render(self, children: list, **props) -> None:
                for child_node in children:
                    child_node()  # Mount each child
            ```
        """
        pass
