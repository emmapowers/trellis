"""Tests for trellis.core.rendering module."""

from trellis.core.rendering import (
    Element,
    ElementDescriptor,
    RenderContext,
    freeze_props,
    get_active_render_context,
    set_active_render_context,
)
from trellis.core.functional_component import FunctionalComponent


def make_component(name: str) -> FunctionalComponent:
    """Helper to create a simple test component."""
    return FunctionalComponent(name=name, render_func=lambda: None)


def make_descriptor(
    comp: FunctionalComponent,
    key: str = "",
    props: dict | None = None,
) -> ElementDescriptor:
    """Helper to create an ElementDescriptor."""
    return ElementDescriptor(
        component=comp,
        key=key,
        props=freeze_props(props or {}),
    )


def make_element(
    comp: FunctionalComponent,
    key: str = "",
    props: dict | None = None,
    depth: int = 0,
) -> Element:
    """Helper to create an Element with a descriptor."""
    desc = make_descriptor(comp, key, props)
    return Element(descriptor=desc, depth=depth)


class TestElement:
    def test_element_creation(self) -> None:
        comp = make_component("Test")
        elem = make_element(comp)

        assert elem.component == comp
        assert elem.key == ""
        assert elem.properties == {}
        assert elem.children == []
        assert elem.dirty is False
        assert elem.parent is None
        assert elem.depth == 0

    def test_element_with_key(self) -> None:
        comp = make_component("Test")
        elem = make_element(comp, key="my-key")

        assert elem.key == "my-key"

    def test_element_with_properties(self) -> None:
        comp = make_component("Test")
        elem = make_element(comp, props={"foo": "bar", "count": 42})

        assert elem.properties == {"foo": "bar", "count": 42}

    def test_element_hash_uses_identity(self) -> None:
        comp = make_component("Test")
        elem1 = make_element(comp)
        elem2 = make_element(comp)

        assert hash(elem1) != hash(elem2)
        assert hash(elem1) == hash(elem1)

    def test_element_replace(self) -> None:
        comp = make_component("Test")
        elem1 = make_element(comp, props={"a": 1}, depth=0)
        elem2 = make_element(comp, props={"b": 2}, depth=5)

        elem1.replace(elem2)

        assert elem1.properties == {"b": 2}
        assert elem1.depth == 5


class TestActiveRenderContext:
    def test_default_is_none(self) -> None:
        assert get_active_render_context() is None

    def test_set_and_get(self) -> None:
        comp = make_component("Root")
        ctx = RenderContext(comp)

        set_active_render_context(ctx)
        assert get_active_render_context() is ctx

        set_active_render_context(None)
        assert get_active_render_context() is None


class TestRenderContext:
    def test_creation(self) -> None:
        comp = make_component("Root")
        ctx = RenderContext(comp)

        assert ctx.root_component == comp
        assert ctx.root_element is None
        assert ctx.dirty_elements == set()
        assert ctx.rendering is False

    def test_mark_dirty(self) -> None:
        comp = make_component("Root")
        ctx = RenderContext(comp)
        elem = make_element(comp)

        ctx.mark_dirty(elem)

        assert elem in ctx.dirty_elements
        assert elem.dirty is True

    def test_current_element_empty_stack(self) -> None:
        comp = make_component("Root")
        ctx = RenderContext(comp)

        assert ctx.current_element is None
