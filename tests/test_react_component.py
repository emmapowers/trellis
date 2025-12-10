"""Tests for ReactComponent base class and decorator."""

from dataclasses import dataclass

import pytest

from trellis.core.functional_component import component
from trellis.core.react_component import ReactComponent, react_component
from trellis.core.rendering import RenderContext
from trellis.core.serialization import serialize_element
from trellis.widgets import Button, Column, Label, Row


class TestReactTypeProperty:
    """Tests for the react_type property on components."""

    def test_react_component_returns_specific_type(self) -> None:
        """ReactComponent subclasses return their _react_type."""

        @react_component("CustomWidget")
        @dataclass(kw_only=True)
        class CustomWidget(ReactComponent):
            name: str = "CustomWidget"

        widget = CustomWidget()
        assert widget.react_type == "CustomWidget"

    def test_functional_component_returns_functional_component(self) -> None:
        """FunctionalComponents all return 'FunctionalComponent'."""

        @component
        def MyComponent() -> None:
            pass

        assert MyComponent.react_type == "FunctionalComponent"

    def test_different_functional_components_same_react_type(self) -> None:
        """All FunctionalComponents share the same react_type."""

        @component
        def ComponentA() -> None:
            pass

        @component
        def ComponentB() -> None:
            pass

        assert ComponentA.react_type == "FunctionalComponent"
        assert ComponentB.react_type == "FunctionalComponent"
        assert ComponentA.react_type == ComponentB.react_type

    def test_widget_react_types(self) -> None:
        """Built-in widgets have correct react_type values."""
        # Get the underlying component from factory function result
        @component
        def App() -> None:
            Label(text="test")
            Button(text="test")
            with Column():
                pass
            with Row():
                pass

        ctx = RenderContext(App)
        ctx.render_tree(from_element=None)

        children = ctx.root_element.children
        assert children[0].component.react_type == "Label"
        assert children[1].component.react_type == "Button"
        assert children[2].component.react_type == "Column"
        assert children[3].component.react_type == "Row"

    def test_react_component_without_react_type_raises(self) -> None:
        """ReactComponent without _react_type raises NotImplementedError."""

        @dataclass(kw_only=True)
        class BadWidget(ReactComponent):
            name: str = "BadWidget"

        widget = BadWidget()
        with pytest.raises(NotImplementedError, match="must set _react_type"):
            _ = widget.react_type


class TestReactComponentDecorator:
    """Tests for the @react_component decorator."""

    def test_decorator_sets_react_type(self) -> None:
        """Decorator sets _react_type class attribute."""

        @react_component("MyType")
        @dataclass(kw_only=True)
        class MyWidget(ReactComponent):
            name: str = "MyWidget"

        assert MyWidget._react_type == "MyType"
        assert MyWidget().react_type == "MyType"

    def test_decorator_sets_has_children_false_by_default(self) -> None:
        """Decorator leaves _has_children False by default."""

        @react_component("LeafWidget")
        @dataclass(kw_only=True)
        class LeafWidget(ReactComponent):
            name: str = "LeafWidget"

        assert LeafWidget._has_children is False

    def test_decorator_sets_has_children_true(self) -> None:
        """Decorator sets _has_children True when specified."""

        @react_component("ContainerWidget", has_children=True)
        @dataclass(kw_only=True)
        class ContainerWidget(ReactComponent):
            name: str = "ContainerWidget"

        assert ContainerWidget._has_children is True

    def test_has_children_param_property(self) -> None:
        """_has_children_param property reads from class variable."""

        @react_component("Container", has_children=True)
        @dataclass(kw_only=True)
        class Container(ReactComponent):
            name: str = "Container"

        @react_component("Leaf")
        @dataclass(kw_only=True)
        class Leaf(ReactComponent):
            name: str = "Leaf"

        assert Container()._has_children_param is True
        assert Leaf()._has_children_param is False


class TestReactComponentSerialization:
    """Tests for serialization of ReactComponents."""

    def test_react_component_type_equals_name(self) -> None:
        """For ReactComponents, type and name are both the component name."""

        @component
        def App() -> None:
            Label(text="test")

        ctx = RenderContext(App)
        ctx.render_tree(from_element=None)

        result = serialize_element(ctx.root_element)
        label_data = result["children"][0]

        # ReactComponent: type is the React component, name is Python name
        assert label_data["type"] == "Label"
        assert label_data["name"] == "Label"

    def test_functional_component_type_differs_from_name(self) -> None:
        """For FunctionalComponents, type is generic but name is specific."""

        @component
        def MyCustomComponent() -> None:
            pass

        ctx = RenderContext(MyCustomComponent)
        ctx.render_tree(from_element=None)

        result = serialize_element(ctx.root_element)

        # FunctionalComponent: type is generic, name is Python function name
        assert result["type"] == "FunctionalComponent"
        assert result["name"] == "MyCustomComponent"

    def test_mixed_tree_serialization(self) -> None:
        """Tree with both component types serializes correctly."""

        @component
        def Header() -> None:
            Label(text="Title")

        @component
        def App() -> None:
            with Column():
                Header()
                Button(text="Click")

        ctx = RenderContext(App)
        ctx.render_tree(from_element=None)

        result = serialize_element(ctx.root_element)

        # Root is FunctionalComponent
        assert result["type"] == "FunctionalComponent"
        assert result["name"] == "App"

        # Column is ReactComponent
        column = result["children"][0]
        assert column["type"] == "Column"
        assert column["name"] == "Column"

        # Header is FunctionalComponent
        header = column["children"][0]
        assert header["type"] == "FunctionalComponent"
        assert header["name"] == "Header"

        # Label inside Header is ReactComponent
        label = header["children"][0]
        assert label["type"] == "Label"
        assert label["name"] == "Label"

        # Button is ReactComponent
        button = column["children"][1]
        assert button["type"] == "Button"
        assert button["name"] == "Button"
