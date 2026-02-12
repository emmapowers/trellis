"""Unit tests for the @react decorator."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from trellis.bundler.registry import ExportKind, ModuleRegistry
from trellis.core.components.composition import component
from trellis.core.components.react import ReactComponentBase, react
from trellis.core.rendering.element import Element


@pytest.fixture(autouse=True)
def isolated_registry():
    """Provide an isolated registry for each test."""
    isolated = ModuleRegistry()
    with patch("trellis.core.components.react.registry", isolated):
        yield isolated


class TestReactDecoratorBasics:
    """Tests for basic @react decorator behavior."""

    def test_creates_callable_returning_element(self, rendered) -> None:
        """Decorated function produces an Element when called in a render context."""

        @react("client/TestWidget.tsx")
        def TestWidget(value: int = 0) -> None:
            pass

        @component
        def App() -> None:
            TestWidget(value=42)

        result = rendered(App)
        node = result.session.elements.get(result.root_element.child_ids[0])
        assert node is not None
        assert node.component.element_name == "TestWidget"
        assert dict(node.props).get("value") == 42

    def test_preserves_function_metadata(self) -> None:
        """Decorator preserves __name__ and __doc__."""

        @react("client/MyWidget.tsx")
        def MyWidget(x: int = 0) -> None:
            """My widget docstring."""

        assert MyWidget.__name__ == "MyWidget"
        assert MyWidget.__doc__ == "My widget docstring."

    def test_default_export_name_is_function_name(self) -> None:
        """Element name matches the function name by default."""

        @react("client/TestWidget.tsx")
        def TestWidget() -> None:
            pass

        assert TestWidget._component.element_name == "TestWidget"

    def test_custom_export_name(self) -> None:
        """export_name overrides the element name."""

        @react("client/Foo.tsx", export_name="Bar")
        def Foo() -> None:
            pass

        assert Foo._component.element_name == "Bar"

    def test_is_container_default_false(self) -> None:
        """Components are not containers by default."""

        @react("client/Leaf.tsx")
        def Leaf() -> None:
            pass

        assert Leaf._component.is_container is False

    def test_is_container_true(self) -> None:
        """is_container=True makes the component a container."""

        @react("client/Container.tsx", is_container=True)
        def Container() -> None:
            pass

        assert Container._component.is_container is True

    def test_element_class_parameter(self) -> None:
        """Custom Element subclass is used when provided."""

        class CustomElement(Element):
            pass

        @react("client/Custom.tsx", element_class=CustomElement)
        def Custom() -> None:
            pass

        assert Custom._component.element_class is CustomElement

    def test_exposes_component_for_introspection(self) -> None:
        """Decorated function has a _component attribute."""

        @react("client/Widget.tsx")
        def Widget() -> None:
            pass

        assert hasattr(Widget, "_component")
        assert isinstance(Widget._component, ReactComponentBase)


class TestReactDecoratorRegistration:
    """Tests for module registration behavior."""

    def test_registers_module_with_bundler(self, isolated_registry) -> None:
        """Module appears in registry after decoration."""

        @react("client/MyWidget.tsx")
        def MyWidget() -> None:
            pass

        collected = isolated_registry.collect()
        assert len(collected.modules) == 1

    def test_registered_module_has_component_export(self, isolated_registry) -> None:
        """Export has correct name, kind, and source."""

        @react("client/MyWidget.tsx")
        def MyWidget() -> None:
            pass

        collected = isolated_registry.collect()
        module = collected.modules[0]
        assert len(module.exports) == 1
        export = module.exports[0]
        assert export.name == "MyWidget"
        assert export.kind == ExportKind.COMPONENT
        assert export.source == "client/MyWidget.tsx"

    def test_registered_module_has_packages(self, isolated_registry) -> None:
        """Packages are passed through to the registered module."""

        @react("client/Chart.tsx", packages={"recharts": "3.6.0"})
        def Chart() -> None:
            pass

        collected = isolated_registry.collect()
        assert collected.packages == {"recharts": "3.6.0"}

    def test_registered_module_base_path(self, isolated_registry) -> None:
        """Base path is set to the calling file's directory."""

        @react("client/Widget.tsx")
        def Widget() -> None:
            pass

        collected = isolated_registry.collect()
        module = collected.modules[0]
        # The base_path should be this test file's directory
        assert module._base_path == Path(__file__).parent.resolve()

    def test_module_name_derived_from_function(self, isolated_registry) -> None:
        """Module name is derived from function's module and qualname with dots replaced by dashes."""

        @react("client/Widget.tsx")
        def Widget() -> None:
            pass

        collected = isolated_registry.collect()
        module = collected.modules[0]
        # Module name uses dots→dashes from f"{func.__module__}.{func.__qualname__}"
        expected_name = f"{Widget.__module__}.{Widget.__qualname__}".replace(".", "-")
        assert module.name == expected_name

    def test_custom_export_name_in_registration(self, isolated_registry) -> None:
        """Custom export_name is used in the module export."""

        @react("client/Internal.tsx", export_name="PublicName")
        def _Internal() -> None:
            pass

        collected = isolated_registry.collect()
        export = collected.modules[0].exports[0]
        assert export.name == "PublicName"

    def test_multiple_decorators_same_source_file(self, isolated_registry) -> None:
        """Two @react decorators pointing at the same TSX file both register."""

        @react("client/Multi.tsx", export_name="WidgetA")
        def WidgetA() -> None:
            pass

        @react("client/Multi.tsx", export_name="WidgetB")
        def WidgetB() -> None:
            pass

        collected = isolated_registry.collect()
        assert len(collected.modules) == 2
        export_names = {m.exports[0].name for m in collected.modules}
        assert export_names == {"WidgetA", "WidgetB"}
