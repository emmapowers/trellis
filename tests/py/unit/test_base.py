"""Tests for core component types and props functions."""

import weakref

from trellis.core.components.base import ElementKind
from trellis.core.components.composition import component
from trellis.core.components.react import ReactComponentBase
from trellis.core.rendering.element import Element
from trellis.html.base import html_element
from trellis.html.text import TextNode


class _DummySession:
    pass


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

    def test_html_element_normalizes_python_keyword_props(self, monkeypatch) -> None:
        """Trailing underscore kwargs map back to DOM prop names."""

        @html_element("script")
        def Script(*, async_: bool | None = None) -> Element: ...

        captured: dict[str, object] = {}
        dummy_session = _DummySession()

        def fake_place(**props: object) -> Element:
            captured.update(props)
            return Element(
                component=Script._component,
                _session_ref=weakref.ref(dummy_session),
                render_count=0,
                props={},
                id="test-1",
            )

        monkeypatch.setattr(Script._component, "_place", fake_place)

        Script(async_=True)
        assert captured["async"] is True
        assert "async_" not in captured

    def test_html_element_preserves_escaped_data_attr_alongside_data_mapping(
        self, monkeypatch
    ) -> None:
        """Escaped HTML attrs should not collide with the data-* mapping helper."""

        @html_element("object")
        def Object(
            *,
            data_: str | None = None,
            data: dict[str, object] | None = None,
        ) -> Element: ...

        captured: dict[str, object] = {}
        dummy_session = _DummySession()

        def fake_place(**props: object) -> Element:
            captured.update(props)
            return Element(
                component=Object._component,
                _session_ref=weakref.ref(dummy_session),
                render_count=0,
                props={},
                id="test-2",
            )

        monkeypatch.setattr(Object._component, "_place", fake_place)

        Object(data_="/asset.bin", data={"asset-id": 1})
        assert captured["data_"] == "/asset.bin"
        assert captured["data"] == {"asset-id": 1}

    def test_react_component_has_react_component_kind(self) -> None:
        """ReactComponentBase subclass should return REACT_COMPONENT kind."""

        class MyWidget(ReactComponentBase):
            _element_name = "MyWidget"

        widget = MyWidget(name="MyWidget")
        assert widget.element_kind == ElementKind.REACT_COMPONENT
        assert widget.element_name == "MyWidget"
