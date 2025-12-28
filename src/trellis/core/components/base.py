"""Base component class."""

from __future__ import annotations

import typing as tp
import weakref
from abc import ABC, abstractmethod
from enum import StrEnum

from trellis.core.rendering.element import Element
from trellis.core.rendering.session import get_active_session
from trellis.utils.logger import logger

__all__ = ["Component"]


class ElementKind(StrEnum):
    """Kind of element: REACT_COMPONENT, JSX_ELEMENT, or TEXT."""

    REACT_COMPONENT = "react_component"
    JSX_ELEMENT = "jsx_element"
    TEXT = "text"


class Component(ABC):
    """Abstract base class for all Trellis components."""

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @property
    @abstractmethod
    def element_kind(self) -> ElementKind:
        """The kind of element."""
        ...

    @property
    @abstractmethod
    def element_name(self) -> str:
        """The element type name for the client."""
        ...

    @property
    def _has_children_param(self) -> bool:
        """Whether this component accepts children via `with` block."""
        return False

    def _place(self, /, **props: tp.Any) -> Element:
        """Place this component, creating or reusing an Element."""
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
        is_dirty = position_id in session.dirty

        if (
            old_node is not None
            and old_node.component == self
            and old_node.props == props
            and is_mounted
            and not is_dirty
        ):
            # For containers with `with` blocks, we must create a new node object.
            # The old_elements snapshot shares node references, so modifying
            # old_node.child_ids in __exit__ would corrupt the snapshot and break
            # reconciliation (old vs new child_ids would be identical).
            if self._has_children_param:
                logger.debug("Creating new node for container %s (preserving snapshot)", self.name)
                node = Element(
                    component=self,
                    _session_ref=weakref.ref(session),
                    render_count=session.render_count,
                    props=props,
                    key=key,
                    id=position_id,
                    child_ids=[],  # Will be populated by __exit__
                )
                session.elements.store(node)
                # Add container to parent's frame (same as non-container path below)
                if session.active.frames.has_active():
                    session.active.frames.add_child(node.id)
                return node

            # Non-container: reuse old node - skip execution entirely, preserve subtree
            logger.debug("Reusing node %s", self.name)
            if session.active.frames.has_active():
                session.active.frames.add_child(old_node.id)
            return old_node

        # Create new node
        node = Element(
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

    def __call__(self, /, **props: tp.Any) -> Element:
        """Create an Element for this component invocation."""
        return self._place(**props)

    @abstractmethod
    def execute(self, /, **props: tp.Any) -> None:
        pass
