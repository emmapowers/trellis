"""Integration tests for element_class parameter on component decorators."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from trellis.core.components.composition import CompositionComponent, component
from trellis.core.components.react import react_component_base
from trellis.core.rendering.element import Element
from trellis.core.state.stateful import Stateful
from trellis.html.base import html_element

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.conftest import RenderResult


# Custom Element subclass for testing
class CustomElement(Element):
    """Custom element with a test_id trait method."""

    def test_id(self, value: str) -> Self:
        """Set a data-testid prop."""
        self.props["data-testid"] = value
        return self


class TestElementClass:
    """Tests for element_class parameter on component decorators."""

    def test_component_uses_custom_element_class(
        self, rendered: Callable[[CompositionComponent], RenderResult]
    ) -> None:
        """@component with element_class creates nodes of that type."""

        @component(element_class=CustomElement)
        def MyWidget() -> None:
            pass

        result = rendered(MyWidget)

        node = result.root_element
        assert node is not None
        assert isinstance(node, CustomElement)
        assert type(node) is CustomElement

    def test_component_custom_node_has_trait_methods(
        self, rendered: Callable[[CompositionComponent], RenderResult]
    ) -> None:
        """Custom element type has its trait methods available."""

        @component(element_class=CustomElement)
        def MyWidget() -> None:
            pass

        result = rendered(MyWidget)

        node = result.root_element
        assert node is not None
        assert hasattr(node, "test_id")

    def test_react_component_base_uses_custom_element_class(
        self, rendered: Callable[[CompositionComponent], RenderResult]
    ) -> None:
        """@react_component_base with element_class creates nodes of that type."""

        @react_component_base("TestWidget", element_class=CustomElement)
        def TestWidget(*, text: str = "") -> Element: ...

        @component
        def App() -> None:
            TestWidget(text="hello")

        result = rendered(App)

        # Find the TestWidget node (child of root)
        root = result.root_element
        assert root is not None
        assert len(root.child_ids) == 1
        child = result.session.elements.get(root.child_ids[0])
        assert child is not None
        assert isinstance(child, CustomElement)
        assert type(child) is CustomElement

    def test_html_element_uses_custom_element_class(
        self, rendered: Callable[[CompositionComponent], RenderResult]
    ) -> None:
        """@html_element with element_class creates nodes of that type."""

        @html_element("span", element_class=CustomElement)
        def CustomSpan(*, className: str | None = None) -> Element: ...

        @component
        def App() -> None:
            CustomSpan(className="test")

        result = rendered(App)

        # Find the CustomSpan node (child of root)
        root = result.root_element
        assert root is not None
        assert len(root.child_ids) == 1
        child = result.session.elements.get(root.child_ids[0])
        assert child is not None
        assert isinstance(child, CustomElement)
        assert type(child) is CustomElement

    def test_custom_element_class_preserved_on_rerender(
        self, rendered: Callable[[CompositionComponent], RenderResult]
    ) -> None:
        """Custom element class is preserved when node is re-rendered."""

        class Counter(Stateful):
            count: int = 0

        @react_component_base("TestWidget", element_class=CustomElement)
        def TestWidget(*, value: int = 0) -> Element: ...

        @component
        def App() -> None:
            state = Counter()
            TestWidget(value=state.count)

        result = rendered(App)

        # Get the TestWidget node
        root = result.root_element
        assert root is not None
        child_id = root.child_ids[0]
        child = result.session.elements.get(child_id)
        assert isinstance(child, CustomElement)

        # Trigger a re-render by marking dirty
        result.session.dirty.mark(root.id)
        from trellis.core.rendering.render import render

        render(result.session)

        # Node should still be CustomElement after re-render
        new_child = result.session.elements.get(child_id)
        assert new_child is not None
        assert isinstance(new_child, CustomElement)
        assert type(new_child) is CustomElement

    def test_default_element_class_is_element(
        self, rendered: Callable[[CompositionComponent], RenderResult]
    ) -> None:
        """Without element_class parameter, Element is used."""

        @component
        def DefaultWidget() -> None:
            pass

        result = rendered(DefaultWidget)

        node = result.root_element
        assert node is not None
        assert type(node) is Element
