"""Base component class for the Trellis UI framework.

This module provides the abstract Component base class that all components
inherit from. Components are the building blocks of Trellis UIs.

The Component class implements the IComponent protocol and provides:
- `__call__()`: Creates an ElementNode (phase 1 - no execution)
- `execute()`: Abstract method that subclasses implement for rendering (phase 2)

Example:
    ```python
    @dataclass(kw_only=True)
    class MyComponent(Component):
        name: str = "MyComponent"

        def execute(self, **props) -> None:
            Text(f"Hello, {props.get('name', 'World')}!")
    ```

See Also:
    - `FunctionalComponent`: Concrete implementation using decorated functions
    - `ElementNode`: The node type returned by `__call__()`
"""

from __future__ import annotations

import typing as tp
from abc import ABC, abstractmethod
from dataclasses import dataclass

from trellis.core.rendering import (
    ElementNode,
    freeze_props,
    get_active_render_tree,
)

__all__ = ["Component"]


@dataclass(kw_only=True)
class Component(ABC):
    """Abstract base class for all Trellis components.

    Components define reusable UI elements. They follow a two-phase rendering model:

    1. **Descriptor Phase**: When called (e.g., `Button(text="Click")`), creates an
       immutable ElementNode that describes the component invocation.

    2. **Execution Phase**: When the reconciler determines this component needs to
       render, it calls `execute()` which produces child descriptors.

    Attributes:
        name: Human-readable component name (used for debugging and error messages)
        react_type: The React component type used to render this on the client
    """

    name: str

    @property
    @abstractmethod
    def react_type(self) -> str:
        """The React component type name used to render this component on the client.

        For FunctionalComponents, this is always "FunctionalComponent".
        For ReactComponents, this is the specific React component name.
        """
        ...

    def __call__(self, /, **props: tp.Any) -> ElementNode:
        """Create an ElementNode for this component invocation.

        This is phase 1 of rendering - NO execution occurs here. The node
        captures the component reference, key, and props for later reconciliation.

        If called inside a `with` block (and this component doesn't accept children),
        the node is automatically added to the parent's pending children.

        Args:
            **props: Properties to pass to the component. The special `key` prop
                is extracted for reconciliation and not passed to `execute()`.

        Returns:
            An immutable ElementNode describing this component invocation.

        Example:
            ```python
            # Creates node, doesn't execute yet
            node = Button(text="Click me", key="btn-1")

            # Inside a with block, auto-collected
            with Column():
                Button(text="First")   # Added to Column's children
                Button(text="Second")  # Added to Column's children
            ```
        """
        key = ""
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
        has_children_param = getattr(self, "_has_children_param", False)
        if ctx.has_active_frame() and not has_children_param:
            ctx.add_to_current_frame(node)
            # Mark as auto-collected to prevent double-collection if used with `with`
            object.__setattr__(node, "_auto_collected", True)

        return node

    @abstractmethod
    def execute(self, /, **props: tp.Any) -> None:
        """Execute this component to produce child nodes.

        This is phase 2 of rendering - called by the reconciler when the
        component needs to render (new mount, props changed, or marked dirty).

        During execution, the component should create child components by
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
            def execute(self, **props) -> None:
                # Simple component - just create children
                Text(f"Count: {props['count']}")
                Button(text="Increment", on_click=props['on_increment'])

            # Container component
            def execute(self, children: list, **props) -> None:
                for child_node in children:
                    child_node()  # Mount each child
            ```
        """
        pass
