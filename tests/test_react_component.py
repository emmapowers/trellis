"""Tests for ReactComponentBase base class and react_component_base decorator."""

from dataclasses import dataclass

import pytest

from trellis.core.components.composition import component
from trellis.core.rendering.element import ElementNode
from trellis.core.components.react import ReactComponentBase, react_component_base
from trellis.core.rendering.render import render
from trellis.platforms.common.serialization import serialize_node
from trellis.core.rendering.session import RenderSession
from trellis.widgets import Button, Column, Label, Row


class TestElementNameProperty:
    """Tests for the element_name property on components."""

    def test_react_component_subclass_returns_specific_type(self) -> None:
        """ReactComponentBase subclasses return their _element_name."""

        @dataclass(kw_only=True)
        class CustomWidget(ReactComponentBase):
            name: str = "CustomWidget"
            _element_name = "CustomWidget"

        widget = CustomWidget()
        assert widget.element_name == "CustomWidget"

    def test_composition_component_returns_composition_component(self) -> None:
        """CompositionComponents all return 'CompositionComponent'."""

        @component
        def MyComponent() -> None:
            pass

        assert MyComponent.element_name == "CompositionComponent"

    def test_different_composition_components_same_element_name(self) -> None:
        """All CompositionComponents share the same element_name."""

        @component
        def ComponentA() -> None:
            pass

        @component
        def ComponentB() -> None:
            pass

        assert ComponentA.element_name == "CompositionComponent"
        assert ComponentB.element_name == "CompositionComponent"
        assert ComponentA.element_name == ComponentB.element_name

    def test_widget_element_names(self) -> None:
        """Built-in widgets have correct element_name values."""
        # Get the underlying component from factory function result
        @component
        def App() -> None:
            Label(text="test")
            Button(text="test")
            with Column():
                pass
            with Row():
                pass

        ctx = RenderSession(App)
        render(ctx)

        assert ctx.elements.get(ctx.root_element.child_ids[0]).component.element_name == "Label"
        assert ctx.elements.get(ctx.root_element.child_ids[1]).component.element_name == "Button"
        assert ctx.elements.get(ctx.root_element.child_ids[2]).component.element_name == "Column"
        assert ctx.elements.get(ctx.root_element.child_ids[3]).component.element_name == "Row"

    def test_react_component_without_element_name_raises(self) -> None:
        """ReactComponentBase without _element_name raises NotImplementedError."""

        @dataclass(kw_only=True)
        class BadWidget(ReactComponentBase):
            name: str = "BadWidget"

        widget = BadWidget()
        with pytest.raises(NotImplementedError, match="must set _element_name"):
            _ = widget.element_name


class TestReactComponentBaseSubclass:
    """Tests for direct subclassing of ReactComponentBase."""

    def test_subclass_sets_element_name(self) -> None:
        """Subclass _element_name is accessible via element_name property."""

        @dataclass(kw_only=True)
        class MyWidget(ReactComponentBase):
            name: str = "MyWidget"
            _element_name = "MyType"

        assert MyWidget._element_name == "MyType"
        assert MyWidget().element_name == "MyType"

    def test_subclass_has_children_false_by_default(self) -> None:
        """Subclasses have _has_children False by default."""

        @dataclass(kw_only=True)
        class LeafWidget(ReactComponentBase):
            name: str = "LeafWidget"
            _element_name = "LeafWidget"

        assert LeafWidget._has_children is False

    def test_subclass_has_children_true(self) -> None:
        """Subclasses can set _has_children True."""

        @dataclass(kw_only=True)
        class ContainerWidget(ReactComponentBase):
            name: str = "ContainerWidget"
            _element_name = "ContainerWidget"
            _has_children = True

        assert ContainerWidget._has_children is True

    def test_has_children_param_property(self) -> None:
        """_has_children_param property reads from class variable."""

        @dataclass(kw_only=True)
        class Container(ReactComponentBase):
            name: str = "Container"
            _element_name = "Container"
            _has_children = True

        @dataclass(kw_only=True)
        class Leaf(ReactComponentBase):
            name: str = "Leaf"
            _element_name = "Leaf"

        assert Container()._has_children_param is True
        assert Leaf()._has_children_param is False


class TestReactComponentBaseDecorator:
    """Tests for the @react_component_base decorator."""

    def test_decorator_creates_callable(self) -> None:
        """Decorator creates a callable that returns ElementNode."""

        @react_component_base("TestWidget")
        def TestWidget(value: int = 0) -> ElementNode:
            """Test widget."""
            ...

        @component
        def App() -> None:
            TestWidget(value=42)

        ctx = RenderSession(App)
        render(ctx)

        node = ctx.elements.get(ctx.root_element.child_ids[0])
        assert node.component.element_name == "TestWidget"
        assert dict(node.props).get("value") == 42

    def test_decorator_preserves_function_metadata(self) -> None:
        """Decorator preserves function name and docstring."""

        @react_component_base("MyWidget")
        def MyWidget(x: int = 0) -> ElementNode:
            """My widget docstring."""
            ...

        assert MyWidget.__name__ == "MyWidget"
        assert MyWidget.__doc__ == "My widget docstring."

    def test_decorator_has_children_false_by_default(self) -> None:
        """Decorator creates components with _has_children False by default."""

        @react_component_base("LeafWidget")
        def LeafWidget() -> ElementNode:
            ...

        # Access the underlying component
        assert LeafWidget._component._has_children_param is False

    def test_decorator_has_children_true(self) -> None:
        """Decorator can create container components."""

        @react_component_base("ContainerWidget", has_children=True)
        def ContainerWidget() -> ElementNode:
            ...

        assert ContainerWidget._component._has_children_param is True

    def test_decorator_exposes_component(self) -> None:
        """Decorated function exposes _component for introspection."""

        @react_component_base("Widget")
        def Widget() -> ElementNode:
            ...

        assert hasattr(Widget, "_component")
        assert isinstance(Widget._component, ReactComponentBase)
        assert Widget._component.element_name == "Widget"


class TestReactComponentBaseSerialization:
    """Tests for serialization of ReactComponentBase."""

    def test_react_component_type_equals_name(self) -> None:
        """For ReactComponents, type and name are both the component name."""

        @component
        def App() -> None:
            Label(text="test")

        ctx = RenderSession(App)
        render(ctx)

        result = serialize_node(ctx.root_element, ctx)
        label_data = result["children"][0]

        # ReactComponent: type is the React component, name is Python name
        assert label_data["type"] == "Label"
        assert label_data["name"] == "Label"

    def test_composition_component_type_differs_from_name(self) -> None:
        """For CompositionComponents, type is generic but name is specific."""

        @component
        def MyCustomComponent() -> None:
            pass

        ctx = RenderSession(MyCustomComponent)
        render(ctx)

        result = serialize_node(ctx.root_element, ctx)

        # CompositionComponent: type is generic, name is Python function name
        assert result["type"] == "CompositionComponent"
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

        ctx = RenderSession(App)
        render(ctx)

        result = serialize_node(ctx.root_element, ctx)

        # Root is CompositionComponent
        assert result["type"] == "CompositionComponent"
        assert result["name"] == "App"

        # Column is ReactComponentBase
        column = result["children"][0]
        assert column["type"] == "Column"
        assert column["name"] == "Column"

        # Header is CompositionComponent
        header = column["children"][0]
        assert header["type"] == "CompositionComponent"
        assert header["name"] == "Header"

        # Label inside Header is ReactComponentBase
        label = header["children"][0]
        assert label["type"] == "Label"
        assert label["name"] == "Label"

        # Button is ReactComponentBase
        button = column["children"][1]
        assert button["type"] == "Button"
        assert button["name"] == "Button"
