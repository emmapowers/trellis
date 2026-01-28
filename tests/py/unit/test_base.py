"""Tests for core component types and props functions."""

import inspect
from pathlib import Path
from unittest.mock import patch

from tests.helpers import requires_pytauri
from trellis.core.components.base import ElementKind
from trellis.core.components.composition import component
from trellis.core.components.react import ReactComponentBase
from trellis.core.rendering.element import Element
from trellis.html.base import html_element
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
        assert hasattr(MyComp, "is_container")

    def test_html_element_has_jsx_element_kind(self) -> None:
        """HtmlElement should return JSX_ELEMENT kind."""

        @html_element("div")
        def TestDiv() -> Element: ...

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


class TestServerPlatformBundle:
    """Tests for ServerPlatform.bundle() method."""

    def test_bundle_returns_workspace_path(self, tmp_path: Path) -> None:
        """bundle() returns the workspace Path used for the build."""
        from trellis.platforms.server.platform import ServerPlatform  # noqa: PLC0415

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        platform = ServerPlatform()
        with (
            patch("trellis.platforms.server.platform.build"),
            patch("trellis.platforms.server.platform.get_project_workspace") as mock_ws,
        ):
            mock_ws.return_value = workspace
            result = platform.bundle()

            assert result == workspace
            assert isinstance(result, Path)

    def test_bundle_return_type_is_path(self) -> None:
        """bundle() return type annotation is Path."""
        from trellis.platforms.server.platform import ServerPlatform  # noqa: PLC0415

        platform = ServerPlatform()
        sig = inspect.signature(platform.bundle)
        # With from __future__ import annotations, the annotation is a string
        assert sig.return_annotation in (Path, "Path")


@requires_pytauri
class TestDesktopPlatformBundle:
    """Tests for DesktopPlatform.bundle() method."""

    def test_bundle_returns_workspace_path(self, tmp_path: Path) -> None:
        """bundle() returns the workspace Path used for the build."""
        # Import guarded by @requires_pytauri on class
        from trellis.platforms.desktop.platform import DesktopPlatform  # noqa: PLC0415

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        platform = DesktopPlatform()
        with (
            patch("trellis.platforms.desktop.platform.build"),
            patch("trellis.platforms.desktop.platform.get_project_workspace") as mock_ws,
        ):
            mock_ws.return_value = workspace
            result = platform.bundle()

            assert result == workspace
            assert isinstance(result, Path)

    def test_bundle_return_type_is_path(self) -> None:
        """bundle() return type annotation is Path."""
        # Import guarded by @requires_pytauri on class
        from trellis.platforms.desktop.platform import DesktopPlatform  # noqa: PLC0415

        platform = DesktopPlatform()
        sig = inspect.signature(platform.bundle)
        # With from __future__ import annotations, the annotation is a string
        assert sig.return_annotation in (Path, "Path")
