"""Integration tests for element_class parameter on component decorators."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self
from unittest.mock import patch

import pytest

from trellis.bundler.registry import ModuleRegistry
from trellis.core.components.composition import CompositionComponent, component
from trellis.core.components.react import react
from trellis.core.rendering.child_ref import ChildRef
from trellis.core.rendering.element import Element
from trellis.core.rendering.render import render
from trellis.core.rendering.traits import ContainerTrait
from trellis.core.state.stateful import Stateful
from trellis.html.base import HtmlContainerTrait, html_element

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


class ContainerCustomElement(ContainerTrait, CustomElement):
    """Custom element that supports container behavior."""


class HtmlContainerCustomElement(HtmlContainerTrait, CustomElement):
    """Custom element that supports HTML container behavior."""


class TestElementClass:
    """Tests for element_class parameter on component decorators."""

    @pytest.fixture(autouse=True)
    def _isolated_registry(self):
        """Provide an isolated registry for @react decorator tests."""
        isolated = ModuleRegistry()
        with patch("trellis.core.components.react.registry", isolated):
            yield isolated

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

    def test_react_uses_custom_element_class(
        self, rendered: Callable[[CompositionComponent], RenderResult]
    ) -> None:
        """@react with element_class creates nodes of that type."""

        @react("client/TestWidget.tsx", element_class=CustomElement)
        def TestWidget(*, text: str = "") -> None:
            pass

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

        @react("client/TestWidget2.tsx", element_class=CustomElement)
        def TestWidget(*, value: int = 0) -> None:
            pass

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

    def test_component_is_container_with_custom_element_class(
        self,
    ) -> None:
        """@component rejects custom element_class without ContainerTrait."""

        with pytest.raises(TypeError, match="ContainerTrait"):

            @component(is_container=True, element_class=CustomElement)
            def MyContainer(children: list[ChildRef]) -> None:
                for child in children:
                    child()

    def test_component_is_container_with_trait_aware_element_class(
        self, rendered: Callable[[CompositionComponent], RenderResult]
    ) -> None:
        """@component accepts custom element_class with ContainerTrait."""

        @component(is_container=True, element_class=ContainerCustomElement)
        def MyContainer(children: list[ChildRef]) -> None:
            for child in children:
                child()

        @component
        def Child() -> None:
            pass

        @component
        def App() -> None:
            with MyContainer():
                Child()

        result = rendered(App)

        root = result.root_element
        assert root is not None
        container = result.session.elements.get(root.child_ids[0])
        assert container is not None
        assert isinstance(container, ContainerCustomElement)
        assert isinstance(container, ContainerTrait)
        assert hasattr(container, "__enter__")
        assert len(container.child_ids) == 1

    def test_react_is_container_with_custom_element_class(
        self,
    ) -> None:
        """@react rejects custom element_class without ContainerTrait."""

        with pytest.raises(TypeError, match="ContainerTrait"):

            @react("client/TestContainer.tsx", is_container=True, element_class=CustomElement)
            def TestContainer(*, label: str = "") -> None:
                pass

    def test_react_is_container_with_trait_aware_element_class(
        self, rendered: Callable[[CompositionComponent], RenderResult]
    ) -> None:
        """@react accepts custom element_class with ContainerTrait."""

        @react("client/TestContainer.tsx", is_container=True, element_class=ContainerCustomElement)
        def TestContainer(*, label: str = "") -> None:
            pass

        @component
        def App() -> None:
            with TestContainer(label="test"):
                pass

        result = rendered(App)

        root = result.root_element
        assert root is not None
        container = result.session.elements.get(root.child_ids[0])
        assert container is not None
        assert isinstance(container, ContainerCustomElement)
        assert isinstance(container, ContainerTrait)

    def test_html_element_is_container_with_custom_element_class(
        self,
    ) -> None:
        """@html_element rejects custom element_class without HtmlContainerTrait."""

        with pytest.raises(TypeError, match="HtmlContainerTrait"):

            @html_element("div", is_container=True, element_class=CustomElement)
            def CustomDiv(*, className: str | None = None) -> Element: ...

    def test_html_element_is_container_with_trait_aware_element_class(
        self, rendered: Callable[[CompositionComponent], RenderResult]
    ) -> None:
        """@html_element accepts custom element_class with HtmlContainerTrait."""

        @html_element("div", is_container=True, element_class=HtmlContainerCustomElement)
        def CustomDiv(*, className: str | None = None) -> Element: ...

        @component
        def App() -> None:
            with CustomDiv(className="test"):
                pass

        result = rendered(App)

        root = result.root_element
        assert root is not None
        container = result.session.elements.get(root.child_ids[0])
        assert container is not None
        assert isinstance(container, HtmlContainerCustomElement)
        assert isinstance(container, HtmlContainerTrait)
        assert isinstance(container, ContainerTrait)

    def test_html_element_maps_positional_text_argument_to_text_prop(
        self, rendered: Callable[[CompositionComponent], RenderResult]
    ) -> None:
        """@html_element maps one positional arg to _text."""

        @html_element("span", is_container=True, name="CustomSpan")
        def CustomSpan(*, _text: str | None = None, className: str | None = None) -> Element: ...

        @component
        def App() -> None:
            CustomSpan("hello", className="test")

        result = rendered(App)

        root = result.root_element
        assert root is not None
        child = result.session.elements.get(root.child_ids[0])
        assert child is not None
        assert child.properties["_text"] == "hello"
        assert child.properties["className"] == "test"

    def test_html_element_rejects_multiple_positional_arguments(
        self, rendered: Callable[[CompositionComponent], RenderResult]
    ) -> None:
        """@html_element raises when more than one positional arg is passed."""

        @html_element("span", is_container=True, name="CustomSpan")
        def CustomSpan(*, _text: str | None = None, className: str | None = None) -> Element: ...

        @component
        def App() -> None:
            CustomSpan("hello", "world")

        with pytest.raises(TypeError, match="at most one positional argument"):
            rendered(App)

    def test_html_element_rejects_positional_argument_with_text_keyword(
        self, rendered: Callable[[CompositionComponent], RenderResult]
    ) -> None:
        """@html_element raises when both positional text and _text kwarg are passed."""

        @html_element("span", is_container=True, name="CustomSpan")
        def CustomSpan(*, _text: str | None = None, className: str | None = None) -> Element: ...

        @component
        def App() -> None:
            CustomSpan("hello", _text="override")

        with pytest.raises(TypeError, match="both positional text and '_text'"):
            rendered(App)
