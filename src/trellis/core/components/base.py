"""Base component class for the Trellis UI framework.

This module provides the abstract Component base class that all components
inherit from. Components are the building blocks of Trellis UIs.

The Component class implements the IComponent protocol and provides:
- `__call__()`: Creates an ElementNode with eager execution
- `render()`: Abstract method that subclasses implement for rendering

The eager execution model:
1. When a component is called, it checks if the old node can be reused
2. If reusable (same component, same props, not dirty), returns old node
3. If not reusable, executes immediately (for non-container components)
4. Container components defer execution to __exit__ after children collected

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
import weakref
from abc import ABC, abstractmethod
from enum import StrEnum

from trellis.core.rendering.element import ElementNode
from trellis.core.rendering.session import get_active_session
from trellis.utils.logger import logger

__all__ = ["Component"]


class ElementKind(StrEnum):
    """Kind of element in the render tree.

    Used by the client to determine how to render each node:
    - REACT_COMPONENT: Custom React component (Button, Slider, etc.)
    - JSX_ELEMENT: Intrinsic HTML element (div, span, p)
    - TEXT: Raw text node

    Values are explicit strings for stable wire format (serialized to client).
    """

    REACT_COMPONENT = "react_component"
    JSX_ELEMENT = "jsx_element"
    TEXT = "text"


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
        """Place this component with eager execution.

        This implements the eager execution model:
        1. Check if the old node at this position can be reused
        2. If reusable (same component, same props, not dirty), return old node
        3. If not reusable, create new node and execute immediately
        4. Container components defer execution to __exit__ after children collected

        If called inside a `with` block (and this component doesn't accept children),
        the node is automatically added to the parent's pending children.

        Args:
            **props: Properties to pass to the component. The special `key` prop
                is extracted for reconciliation and not passed to `render()`.

        Returns:
            An immutable ElementNode describing this component invocation.

        Example:
            ```python
            # Creates and executes immediately (if not reused)
            node = Button(text="Click me", key="btn-1")

            # Inside a with block, auto-collected
            with Column():
                Button(text="First")   # Executed immediately, added to children
                Button(text="Second")  # Executed immediately, added to children
            ```
        """
        key: str | None = None
        if "key" in props:
            raw_key = props.pop("key")
            if raw_key is not None:
                key = str(raw_key)

        # Ensure we're inside a render context - components cannot be created
        # in callbacks or other code outside of rendering
        session = get_active_session()
        if session is None:
            raise RuntimeError(
                f"Cannot create component '{self.name}' outside of render context. "
                f"Components must be created during rendering, not in callbacks."
            )

        # Compute position-based ID at creation time, including component identity
        assert session.active is not None
        if session.active.frames.has_active():
            position_id = session.active.frames.next_child_id(self, key)
        else:
            position_id = session.active.frames.root_id(self)

        # REUSE CHECK - the key optimization from Phase 5
        # We can only reuse if:
        # 1. Old node exists at this position
        # 2. Same component type
        # 3. Same props
        # 4. Node is mounted (has active ElementState with mounted=True)
        # 5. Node is not dirty
        old_node = session.elements.get(position_id)
        state = session.states.get(position_id)
        is_mounted = state is not None and state.mounted
        is_dirty = state.dirty if state else False

        if (
            old_node is not None
            and old_node.component == self
            and old_node.props == props
            and is_mounted
            and not is_dirty
        ):
            # Reuse old node - skip execution entirely, preserve subtree
            logger.debug(
                "Reusing node %s (container=%s)",
                self.name,
                self._has_children_param,
            )
            if session.active.frames.has_active() and not self._has_children_param:
                session.active.frames.add_child(old_node.id)
            return old_node

        # Create new node
        node = ElementNode(
            component=self,
            _session_ref=weakref.ref(session),
            render_count=session.render_count,
            props=props,
            key=key,
            id=position_id,
        )

        # Store node (execution happens later via _execute_tree)
        session.elements.store(node)

        # Auto-collect: add to parent node's pending children
        # Containers are also auto-collected now (execution deferred to _execute_tree)
        if session.active.frames.has_active():
            session.active.frames.add_child(node.id)

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
    def execute(self, /, **props: tp.Any) -> None:
        pass
