"""Unit tests for Element trait mixins."""

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING

from trellis.core.components.composition import CompositionComponent
from trellis.core.rendering.element import Element
from trellis.core.rendering.session import RenderSession

if TYPE_CHECKING:
    import typing as tp


# Dummy session for testing Element creation
_dummy_session: RenderSession | None = None


def _get_dummy_session_ref(
    make_component: tp.Callable[[str], CompositionComponent],
) -> weakref.ref[RenderSession]:
    """Get a weakref to a dummy session for testing."""
    global _dummy_session
    if _dummy_session is None:
        _dummy_session = RenderSession(make_component("DummyRoot"))
    return weakref.ref(_dummy_session)


def make_element(
    make_component: tp.Callable[[str], CompositionComponent],
    comp: CompositionComponent | None = None,
) -> Element:
    """Helper to create an Element for testing."""
    if comp is None:
        comp = make_component("Test")
    return Element(
        component=comp,
        _session_ref=_get_dummy_session_ref(make_component),
        render_count=0,
        props={},
    )


class TestKeyTrait:
    """Tests for the fluent .key() method on Element."""

    def test_key_sets_key_attribute(
        self, make_component: tp.Callable[[str], CompositionComponent]
    ) -> None:
        """The key() method sets the _key attribute."""
        node = make_element(make_component)
        assert node._key is None

        node.key("my-key")
        assert node._key == "my-key"

    def test_key_returns_self(
        self, make_component: tp.Callable[[str], CompositionComponent]
    ) -> None:
        """The key() method returns self for chaining."""
        node = make_element(make_component)
        result = node.key("my-key")
        assert result is node

    def test_key_allows_chaining(
        self, make_component: tp.Callable[[str], CompositionComponent]
    ) -> None:
        """Multiple trait methods can be chained."""
        node = make_element(make_component).key("first")
        assert node._key == "first"

        # Chain another call
        node.key("second")
        assert node._key == "second"

    def test_key_overwrites_existing(
        self, make_component: tp.Callable[[str], CompositionComponent]
    ) -> None:
        """Calling key() overwrites any existing key."""
        node = make_element(make_component)
        # Set initial key via the trait
        node.key("initial")
        assert node._key == "initial"

        node.key("updated")
        assert node._key == "updated"
