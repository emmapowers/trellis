"""Tests for ReactComponentBase base class and @react decorator."""

from dataclasses import dataclass
from unittest.mock import patch

import pytest

from trellis.bundler.registry import ModuleRegistry
from trellis.core.components.composition import component
from trellis.core.components.react import ReactComponentBase, react
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

    def test_widget_element_names(self, rendered) -> None:
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

        result = rendered(App)

        assert (
            result.session.elements.get(result.root_element.child_ids[0]).component.element_name
            == "Label"
        )
        # Button is a composition component wrapping _Button
        button_wrapper = result.session.elements.get(result.root_element.child_ids[1])
        assert button_wrapper.component.element_name == "CompositionComponent"
        # The inner _Button has element_name "Button"
        inner_button = result.session.elements.get(button_wrapper.child_ids[0])
        assert inner_button.component.element_name == "Button"
        assert (
            result.session.elements.get(result.root_element.child_ids[2]).component.element_name
            == "Column"
        )
        assert (
            result.session.elements.get(result.root_element.child_ids[3]).component.element_name
            == "Row"
        )

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

    def test_subclass_is_container_false_by_default(self) -> None:
        """Subclasses have _is_container False by default."""

        @dataclass(kw_only=True)
        class LeafWidget(ReactComponentBase):
            name: str = "LeafWidget"
            _element_name = "LeafWidget"

        assert LeafWidget._is_container is False

    def test_subclass_is_container_true(self) -> None:
        """Subclasses can set _is_container True."""

        @dataclass(kw_only=True)
        class ContainerWidget(ReactComponentBase):
            name: str = "ContainerWidget"
            _element_name = "ContainerWidget"
            _is_container = True

        assert ContainerWidget._is_container is True

    def testis_container_property(self) -> None:
        """is_container property reads from class variable."""

        @dataclass(kw_only=True)
        class Container(ReactComponentBase):
            name: str = "Container"
            _element_name = "Container"
            _is_container = True

        @dataclass(kw_only=True)
        class Leaf(ReactComponentBase):
            name: str = "Leaf"
            _element_name = "Leaf"

        assert Container().is_container is True
        assert Leaf().is_container is False


class TestReactDecorator:
    """Tests for the @react decorator in integration context."""

    @pytest.fixture(autouse=True)
    def _isolated_registry(self):
        """Provide an isolated registry for decorator tests."""
        isolated = ModuleRegistry()
        with patch("trellis.core.components.react.registry", isolated):
            yield isolated

    def test_decorator_creates_callable(self, rendered) -> None:
        """Decorator creates a callable that returns Element."""

        @react("client/TestWidget.tsx")
        def TestWidget(value: int = 0) -> None:
            """Test widget."""

        @component
        def App() -> None:
            TestWidget(value=42)

        result = rendered(App)

        node = result.session.elements.get(result.root_element.child_ids[0])
        assert node.component.element_name == "TestWidget"
        assert dict(node.props).get("value") == 42

    def test_decorator_preserves_function_metadata(self) -> None:
        """Decorator preserves function name and docstring."""

        @react("client/MyWidget.tsx")
        def MyWidget(x: int = 0) -> None:
            """My widget docstring."""

        assert MyWidget.__name__ == "MyWidget"
        assert MyWidget.__doc__ == "My widget docstring."

    def test_decorator_is_container_false_by_default(self) -> None:
        """Decorator creates components with _is_container False by default."""

        @react("client/LeafWidget.tsx")
        def LeafWidget() -> None:
            pass

        assert LeafWidget._component.is_container is False

    def test_decorator_is_container_true(self) -> None:
        """Decorator can create container components."""

        @react("client/ContainerWidget.tsx", is_container=True)
        def ContainerWidget() -> None:
            pass

        assert ContainerWidget._component.is_container is True

    def test_decorator_exposes_component(self) -> None:
        """Decorated function exposes _component for introspection."""

        @react("client/Widget.tsx")
        def Widget() -> None:
            pass

        assert hasattr(Widget, "_component")
        assert isinstance(Widget._component, ReactComponentBase)
        assert Widget._component.element_name == "Widget"


class TestReactComponentBaseSerialization:
    """Tests for serialization of ReactComponentBase."""

    def test_react_component_type_equals_name(self, rendered) -> None:
        """For ReactComponents, type and name are both the component name."""

        @component
        def App() -> None:
            Label(text="test")

        result = rendered(App)

        label_data = result.tree["children"][0]

        # ReactComponent: type is the React component, name is Python name
        assert label_data["type"] == "Label"
        assert label_data["name"] == "Label"

    def test_composition_component_type_differs_from_name(self, rendered) -> None:
        """For CompositionComponents, type is generic but name is specific."""

        @component
        def MyCustomComponent() -> None:
            pass

        result = rendered(MyCustomComponent)

        # CompositionComponent: type is generic, name is Python function name
        assert result.tree["type"] == "CompositionComponent"
        assert result.tree["name"] == "MyCustomComponent"

    def test_mixed_tree_serialization(self, rendered) -> None:
        """Tree with both component types serializes correctly."""

        @component
        def Header() -> None:
            Label(text="Title")

        @component
        def App() -> None:
            with Column():
                Header()
                Button(text="Click")

        result = rendered(App)

        # Root is CompositionComponent
        assert result.tree["type"] == "CompositionComponent"
        assert result.tree["name"] == "App"

        # Column is ReactComponentBase
        column = result.tree["children"][0]
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

        # Button is a composition component wrapping _Button
        button_wrapper = column["children"][1]
        assert button_wrapper["type"] == "CompositionComponent"
        assert button_wrapper["name"] == "Button"
        # The inner _Button is the actual ReactComponentBase
        inner_button = button_wrapper["children"][0]
        assert inner_button["type"] == "Button"
        assert inner_button["name"] == "_Button"
