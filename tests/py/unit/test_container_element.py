"""Tests for ContainerTrait and ContainerElement behavior.

Verifies that Element (leaf) does not support `with` blocks, while
ContainerTrait provides __enter__/__exit__ as a standalone mixin,
and ContainerElement composes ContainerTrait + Element.
"""

from __future__ import annotations

import weakref

import pytest

from trellis import component
from trellis import html as h
from trellis.core.rendering.element import ContainerElement, Element
from trellis.core.rendering.session import RenderSession
from trellis.core.rendering.traits import ContainerTrait


class TestElementIsNotContextManager:
    """Element (leaf) should not support `with` blocks."""

    def test_element_has_no_enter(self) -> None:
        """Element does not have __enter__."""
        assert not hasattr(Element, "__enter__")

    def test_element_has_no_exit(self) -> None:
        """Element does not have __exit__."""
        assert not hasattr(Element, "__exit__")


class TestContainerTrait:
    """ContainerTrait is a standalone mixin providing __enter__/__exit__."""

    def test_trait_has_enter(self) -> None:
        """ContainerTrait has __enter__."""
        assert hasattr(ContainerTrait, "__enter__")

    def test_trait_has_exit(self) -> None:
        """ContainerTrait has __exit__."""
        assert hasattr(ContainerTrait, "__exit__")

    def test_trait_is_not_element(self) -> None:
        """ContainerTrait is independent of Element."""
        assert not issubclass(ContainerTrait, Element)


class TestContainerElementContextManager:
    """ContainerElement composes ContainerTrait + Element."""

    def test_container_element_has_enter(self) -> None:
        """ContainerElement has __enter__ from ContainerTrait."""
        assert hasattr(ContainerElement, "__enter__")

    def test_container_element_has_exit(self) -> None:
        """ContainerElement has __exit__ from ContainerTrait."""
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
        """ContainerTrait.__enter__ raises TypeError when _text is set."""

        @component
        def App() -> None:
            with h.Td("text"):
                pass

        with pytest.raises(TypeError, match=r"Cannot use.*with.*text content"):
            rendered(App)

    def test_container_element_is_subclass(self) -> None:
        """ContainerElement is a subclass of Element."""
        assert issubclass(ContainerElement, Element)

    def test_container_element_has_container_trait(self) -> None:
        """ContainerElement includes ContainerTrait in its MRO."""
        assert issubclass(ContainerElement, ContainerTrait)
