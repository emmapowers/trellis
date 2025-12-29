"""Unit tests for Element class and related utilities."""

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
    make_component: "tp.Callable[[str], CompositionComponent]",
) -> weakref.ref[RenderSession]:
    """Get a weakref to a dummy session for testing."""
    global _dummy_session
    if _dummy_session is None:
        _dummy_session = RenderSession(make_component("DummyRoot"))
    return weakref.ref(_dummy_session)


def _make_descriptor(
    make_component: "tp.Callable[[str], CompositionComponent]",
    comp: CompositionComponent,
    key: str | None = None,
    props: dict | None = None,
) -> Element:
    """Helper to create an Element."""
    return Element(
        component=comp,
        _session_ref=_get_dummy_session_ref(make_component),
        render_count=0,
        key=key,
        props=props or {},
    )


class TestElement:
    def test_element_node_creation(
        self, make_component: "tp.Callable[[str], CompositionComponent]"
    ) -> None:
        comp = make_component("Test")
        node = _make_descriptor(make_component, comp)

        assert node.component == comp
        assert node.key is None
        assert node.props == {}
        assert node.child_ids == []
        assert node.id == ""

    def test_element_node_with_key(
        self, make_component: "tp.Callable[[str], CompositionComponent]"
    ) -> None:
        comp = make_component("Test")
        node = _make_descriptor(make_component, comp, key="my-key")

        assert node.key == "my-key"

    def test_element_node_with_properties(
        self, make_component: "tp.Callable[[str], CompositionComponent]"
    ) -> None:
        comp = make_component("Test")
        node = _make_descriptor(make_component, comp, props={"foo": "bar", "count": 42})

        assert node.properties == {"foo": "bar", "count": 42}

    def test_element_node_is_mutable(
        self, make_component: "tp.Callable[[str], CompositionComponent]"
    ) -> None:
        comp = make_component("Test")
        node = _make_descriptor(make_component, comp, props={"a": 1})

        # Element is mutable and uses render_count-based hashing
        hash(node)  # Should not raise

        # Can modify attributes
        node.id = "new-id"
        assert node.id == "new-id"


class TestEscapeKey:
    """Tests for URL-encoding special characters in keys."""

    def test_no_special_chars(self) -> None:
        """Keys without special chars pass through unchanged."""
        from trellis.core.rendering.frames import _escape_key

        assert _escape_key("simple") == "simple"
        assert _escape_key("with-dash") == "with-dash"
        assert _escape_key("with_underscore") == "with_underscore"
        assert _escape_key("CamelCase") == "CamelCase"
        assert _escape_key("123") == "123"

    def test_escape_colon(self) -> None:
        """Colon is escaped."""
        from trellis.core.rendering.frames import _escape_key

        assert _escape_key("my:key") == "my%3Akey"
        assert _escape_key("a:b:c") == "a%3Ab%3Ac"

    def test_escape_at(self) -> None:
        """At sign is escaped."""
        from trellis.core.rendering.frames import _escape_key

        assert _escape_key("item@home") == "item%40home"
        assert _escape_key("user@domain") == "user%40domain"

    def test_escape_slash(self) -> None:
        """Slash is escaped."""
        from trellis.core.rendering.frames import _escape_key

        assert _escape_key("row/5") == "row%2F5"
        assert _escape_key("path/to/item") == "path%2Fto%2Fitem"

    def test_escape_percent(self) -> None:
        """Percent must be escaped first to avoid double-encoding."""
        from trellis.core.rendering.frames import _escape_key

        assert _escape_key("100%") == "100%25"
        assert _escape_key("%done") == "%25done"

    def test_multiple_special_chars(self) -> None:
        """All special characters are escaped in a single key."""
        from trellis.core.rendering.frames import _escape_key

        assert _escape_key("a:b@c/d%e") == "a%3Ab%40c%2Fd%25e"
        # Percent first, then others
        assert _escape_key("%:@/") == "%25%3A%40%2F"
