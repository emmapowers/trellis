"""Tests for ContainerElement behavior.

Verifies that Element (leaf) and ContainerElement (container) have distinct
context manager behavior: Element does not support `with` blocks, while
ContainerElement does when used inside a render context.
"""

from __future__ import annotations

import weakref

import pytest

from trellis.core.components.composition import component
from trellis.core.rendering.element import ContainerElement, Element
from trellis.core.rendering.session import RenderSession
from trellis.html import Td


class TestElementIsNotContextManager:
    """Element (leaf) should not support `with` blocks."""

    def test_element_has_no_enter(self) -> None:
        """Element does not have __enter__."""
        assert not hasattr(Element, "__enter__")

    def test_element_has_no_exit(self) -> None:
        """Element does not have __exit__."""
        assert not hasattr(Element, "__exit__")


class TestContainerElementContextManager:
    """ContainerElement supports `with` blocks in render context."""

    def test_container_element_has_enter(self) -> None:
        """ContainerElement has __enter__."""
        assert hasattr(ContainerElement, "__enter__")

    def test_container_element_has_exit(self) -> None:
        """ContainerElement has __exit__."""
        assert hasattr(ContainerElement, "__exit__")

    def test_container_enter_raises_outside_render(self, noop_component) -> None:
        """ContainerElement.__enter__ raises RuntimeError outside render context."""
        session = RenderSession(noop_component)
        elem = ContainerElement(
            component=noop_component,
            _session_ref=weakref.ref(session),
            render_count=0,
            props={},
            id="test-1",
        )
        with pytest.raises(RuntimeError, match="outside of render context"):
            elem.__enter__()

    def test_container_enter_raises_with_text_prop(self, rendered) -> None:
        """ContainerElement.__enter__ raises TypeError when _text is set."""

        @component
        def App() -> None:
            with Td("text"):
                pass

        with pytest.raises(TypeError, match=r"Cannot use.*with.*text content"):
            rendered(App)

    def test_container_element_is_subclass(self) -> None:
        """ContainerElement is a subclass of Element."""
        assert issubclass(ContainerElement, Element)
