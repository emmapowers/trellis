"""Tests for core component types and props functions."""

import pytest

from trellis.core.components.base import ElementKind
from trellis.core.components.composition import CompositionComponent, component
from trellis.core.components.react import ReactComponentBase
from trellis.core.rendering.element import Element
from trellis.html.base import HtmlElement, html_element
from trellis.html.text import TextNode


class TestElementKind:
    """Tests for ElementKind enum."""

    def test_element_kind_explicit_values(self) -> None:
        """ElementKind values should be explicit strings for stable wire format."""
        assert ElementKind.REACT_COMPONENT == "react_component"
        assert ElementKind.JSX_ELEMENT == "jsx_element"
        assert ElementKind.TEXT == "text"

    def test_element_kind_is_str_enum(self) -> None:
        """ElementKind values should be usable as strings."""
        assert str(ElementKind.REACT_COMPONENT) == "react_component"
        assert f"{ElementKind.JSX_ELEMENT}" == "jsx_element"

    def test_element_kind_value_property(self) -> None:
        """ElementKind.value should return the string value."""
        assert ElementKind.REACT_COMPONENT.value == "react_component"
        assert ElementKind.JSX_ELEMENT.value == "jsx_element"
        assert ElementKind.TEXT.value == "text"


class TestIComponentProtocolConformance:
    """Tests verifying component types implement IComponent protocol correctly."""

    def test_composition_component_has_element_kind(self) -> None:
        """CompositionComponent should have element_kind property."""

        @component
        def MyComp() -> None:
            pass

        assert hasattr(MyComp, "element_kind")
        assert MyComp.element_kind == ElementKind.REACT_COMPONENT

    def test_composition_component_has_element_name(self) -> None:
        """CompositionComponent should have element_name property."""

        @component
        def MyComp() -> None:
            pass

        assert hasattr(MyComp, "element_name")
        assert MyComp.element_name == "CompositionComponent"

    def test_composition_component_has_required_methods(self) -> None:
        """CompositionComponent should have required protocol methods."""

        @component
        def MyComp() -> None:
            pass

        assert callable(MyComp)
        assert hasattr(MyComp, "execute")
        assert hasattr(MyComp, "_has_children_param")

    def test_html_element_has_jsx_element_kind(self) -> None:
        """HtmlElement should return JSX_ELEMENT kind."""

        @html_element("div")
        def TestDiv() -> Element:
            ...

        # Access the underlying component via the decorator's _component attribute
        elem = TestDiv._component
        assert elem.element_kind == ElementKind.JSX_ELEMENT

    def test_text_node_has_text_kind(self) -> None:
        """TextNode should return TEXT kind."""
        text_node = TextNode(name="Text")
        assert text_node.element_kind == ElementKind.TEXT
        assert text_node.element_name == "__text__"

    def test_react_component_base_has_react_component_kind(self) -> None:
        """ReactComponentBase subclass should return REACT_COMPONENT kind."""

        class MyWidget(ReactComponentBase):
            _element_name = "MyWidget"

        widget = MyWidget(name="MyWidget")
        assert widget.element_kind == ElementKind.REACT_COMPONENT
        assert widget.element_name == "MyWidget"
