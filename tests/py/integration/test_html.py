"""Tests for native HTML elements."""

from trellis import html as h
from trellis.core.components.composition import component
from trellis.platforms.common.serialization import parse_callback_id, serialize_element


class TestHtmlElements:
    """Tests for HTML element rendering."""

    def test_div_renders_as_container(self, rendered) -> None:
        """Div element can contain children."""

        @component
        def App() -> None:
            with h.Div():
                h.Span("Hello")

        result = rendered(App)

        div = result.session.elements.get(result.root_element.child_ids[0])
        assert div.component.name == "Div"
        assert len(div.child_ids) == 1
        assert result.session.elements.get(div.child_ids[0]).component.name == "Span"

    def test_nested_divs(self, rendered) -> None:
        """Divs can be nested."""

        @component
        def App() -> None:
            with h.Div():
                with h.Div():
                    h.Span("Nested")

        result = rendered(App)

        outer = result.session.elements.get(result.root_element.child_ids[0])
        inner = result.session.elements.get(outer.child_ids[0])
        span = result.session.elements.get(inner.child_ids[0])

        assert outer.component.name == "Div"
        assert inner.component.name == "Div"
        assert span.component.name == "Span"

    def test_text_element_stores_text(self, rendered) -> None:
        """Text elements store text in _text prop."""

        @component
        def App() -> None:
            h.H1("Page Title")
            h.P("Paragraph text")
            h.Span("Inline text")

        result = rendered(App)

        h1 = result.session.elements.get(result.root_element.child_ids[0])
        p = result.session.elements.get(result.root_element.child_ids[1])
        span = result.session.elements.get(result.root_element.child_ids[2])

        assert h1.properties["_text"] == "Page Title"
        assert p.properties["_text"] == "Paragraph text"
        assert span.properties["_text"] == "Inline text"

    def test_element_with_style(self, rendered) -> None:
        """Elements accept style dict."""

        @component
        def App() -> None:
            with h.Div(style={"backgroundColor": "red", "padding": "10px"}):
                pass

        result = rendered(App)

        div = result.session.elements.get(result.root_element.child_ids[0])
        assert div.properties["style"] == {"backgroundColor": "red", "padding": "10px"}

    def test_element_with_class_name(self, rendered) -> None:
        """Elements accept className prop."""

        @component
        def App() -> None:
            with h.Div(className="container"):
                pass

        result = rendered(App)

        div = result.session.elements.get(result.root_element.child_ids[0])
        assert div.properties["className"] == "container"

    def test_text_renders_plain_text(self, rendered) -> None:
        """Text element renders plain text without wrapper."""

        @component
        def App() -> None:
            with h.Div():
                h.Span("Count: ")
                h.Text(42)

        result = rendered(App)

        div = result.session.elements.get(result.root_element.child_ids[0])
        assert len(div.child_ids) == 2
        assert result.session.elements.get(div.child_ids[0]).component.name == "Span"
        assert result.session.elements.get(div.child_ids[1]).component.name == "Text"
        assert result.session.elements.get(div.child_ids[1]).properties["_text"] == "42"

    def test_text_converts_values_to_string(self, rendered) -> None:
        """Text converts any value to string."""

        @component
        def App() -> None:
            h.Text(123)
            h.Text(3.14)
            h.Text(True)
            h.Text(None)

        result = rendered(App)

        assert (
            result.session.elements.get(result.root_element.child_ids[0]).properties["_text"]
            == "123"
        )
        assert (
            result.session.elements.get(result.root_element.child_ids[1]).properties["_text"]
            == "3.14"
        )
        assert (
            result.session.elements.get(result.root_element.child_ids[2]).properties["_text"]
            == "True"
        )
        assert (
            result.session.elements.get(result.root_element.child_ids[3]).properties["_text"]
            == "None"
        )


class TestHtmlSerialization:
    """Tests for HTML element serialization."""

    def test_serialize_div_as_tag_name(self, rendered) -> None:
        """Div serializes with type='div' (not a React component)."""

        @component
        def App() -> None:
            with h.Div():
                pass

        result = rendered(App)

        serialized = serialize_element(result.root_element, result.session)
        div_data = serialized["children"][0]

        assert div_data["type"] == "div"
        assert div_data["name"] == "Div"

    def test_serialize_various_tags(self, rendered) -> None:
        """Different HTML elements serialize with correct tag names."""

        @component
        def App() -> None:
            h.Span("text")
            h.H1("heading")
            h.P("paragraph")
            h.A("link", href="https://example.com")  # A is hybrid, needs text or with

        result = rendered(App)

        serialized = serialize_element(result.root_element, result.session)

        assert serialized["children"][0]["type"] == "span"
        assert serialized["children"][1]["type"] == "h1"
        assert serialized["children"][2]["type"] == "p"
        assert serialized["children"][3]["type"] == "a"

    def test_serialize_text_content(self, rendered) -> None:
        """Text content is serialized in _text prop."""

        @component
        def App() -> None:
            h.H1("Hello World")

        result = rendered(App)

        serialized = serialize_element(result.root_element, result.session)
        h1_data = serialized["children"][0]

        assert h1_data["type"] == "h1"
        assert h1_data["props"]["_text"] == "Hello World"

    def test_serialize_nested_structure(self, rendered) -> None:
        """Nested HTML elements serialize correctly."""

        @component
        def App() -> None:
            with h.Div(style={"padding": "20px"}):
                h.H1("Title")
                with h.Div():
                    h.P("Content")

        result = rendered(App)

        serialized = serialize_element(result.root_element, result.session)
        outer = serialized["children"][0]

        assert outer["type"] == "div"
        assert outer["props"]["style"] == {"padding": "20px"}
        assert len(outer["children"]) == 2

        h1 = outer["children"][0]
        inner = outer["children"][1]

        assert h1["type"] == "h1"
        assert h1["props"]["_text"] == "Title"
        assert inner["type"] == "div"
        assert inner["children"][0]["type"] == "p"

    def test_serialize_onclick_as_callback(self, rendered) -> None:
        """onClick handler serializes as callback reference."""
        clicked = []

        @component
        def App() -> None:
            with h.Div(onClick=lambda: clicked.append(True)):
                pass

        result = rendered(App)

        serialized = serialize_element(result.root_element, result.session)
        div_data = serialized["children"][0]

        assert "__callback__" in div_data["props"]["onClick"]

        # Verify callback works
        cb_id = div_data["props"]["onClick"]["__callback__"]
        node_id, prop_name = parse_callback_id(cb_id)
        result.session.get_callback(node_id, prop_name)()
        assert clicked == [True]

    def test_serialize_link_props(self, rendered) -> None:
        """Anchor element serializes with href and target."""

        @component
        def App() -> None:
            h.A("Click here", href="https://example.com", target="_blank")

        result = rendered(App)

        serialized = serialize_element(result.root_element, result.session)
        a_data = serialized["children"][0]

        assert a_data["type"] == "a"
        assert a_data["props"]["_text"] == "Click here"
        assert a_data["props"]["href"] == "https://example.com"
        assert a_data["props"]["target"] == "_blank"

    def test_serialize_text_node(self, rendered) -> None:
        """Text element serializes with special _text type."""

        @component
        def App() -> None:
            with h.Div():
                h.Span("Label: ")
                h.Text("value")

        result = rendered(App)

        serialized = serialize_element(result.root_element, result.session)
        div_data = serialized["children"][0]

        assert len(div_data["children"]) == 2
        span_data = div_data["children"][0]
        text_data = div_data["children"][1]

        assert span_data["type"] == "span"
        assert text_data["type"] == "__text__"
        assert text_data["kind"] == "text"  # TEXT ElementKind
        assert text_data["name"] == "Text"
        assert text_data["props"]["_text"] == "value"


class TestHybridElements:
    """Tests for hybrid elements that can be text-only or containers."""

    def test_td_with_text_auto_collects(self, rendered) -> None:
        """Td with text is auto-collected without with block."""

        @component
        def App() -> None:
            with h.Tr():
                h.Td("Cell 1")
                h.Td("Cell 2")

        result = rendered(App)

        tr = result.session.elements.get(result.root_element.child_ids[0])
        assert len(tr.child_ids) == 2
        assert result.session.elements.get(tr.child_ids[0]).properties["_text"] == "Cell 1"
        assert result.session.elements.get(tr.child_ids[1]).properties["_text"] == "Cell 2"

    def test_td_as_container(self, rendered) -> None:
        """Td without text can be used as container."""

        @component
        def App() -> None:
            with h.Tr():
                with h.Td():
                    h.Strong("Bold")
                    h.Span(" text")

        result = rendered(App)

        tr = result.session.elements.get(result.root_element.child_ids[0])
        td = result.session.elements.get(tr.child_ids[0])
        assert len(td.child_ids) == 2
        assert result.session.elements.get(td.child_ids[0]).component.name == "Strong"
        assert result.session.elements.get(td.child_ids[1]).component.name == "Span"

    def test_li_with_text_auto_collects(self, rendered) -> None:
        """Li with text is auto-collected."""

        @component
        def App() -> None:
            with h.Ul():
                h.Li("Item 1")
                h.Li("Item 2")

        result = rendered(App)

        ul = result.session.elements.get(result.root_element.child_ids[0])
        assert len(ul.child_ids) == 2

    def test_li_as_container(self, rendered) -> None:
        """Li without text can be used as container."""

        @component
        def App() -> None:
            with h.Ul():
                with h.Li():
                    h.Strong("Bold item")

        result = rendered(App)

        ul = result.session.elements.get(result.root_element.child_ids[0])
        li = result.session.elements.get(ul.child_ids[0])
        assert len(li.child_ids) == 1
        assert result.session.elements.get(li.child_ids[0]).component.name == "Strong"

    def test_a_with_text_auto_collects(self, rendered) -> None:
        """A with text is auto-collected."""

        @component
        def App() -> None:
            with h.Div():
                h.A("Click here", href="/path")

        result = rendered(App)

        div = result.session.elements.get(result.root_element.child_ids[0])
        assert len(div.child_ids) == 1
        assert result.session.elements.get(div.child_ids[0]).properties["_text"] == "Click here"
        assert result.session.elements.get(div.child_ids[0]).properties["href"] == "/path"

    def test_a_as_container(self, rendered) -> None:
        """A without text can be used as container."""

        @component
        def App() -> None:
            with h.Div():
                with h.A(href="/path"):
                    h.Span("Link text")

        result = rendered(App)

        div = result.session.elements.get(result.root_element.child_ids[0])
        a = result.session.elements.get(div.child_ids[0])
        assert len(a.child_ids) == 1
        assert result.session.elements.get(a.child_ids[0]).component.name == "Span"

    def test_hybrid_no_double_collection(self, rendered) -> None:
        """Using with on a text hybrid element doesn't double-collect."""

        @component
        def App() -> None:
            with h.Div():
                # This would double-collect without the _auto_collected fix
                with h.Td("text"):
                    pass

        result = rendered(App)

        div = result.session.elements.get(result.root_element.child_ids[0])
        # Should only have one Td child, not two
        assert len(div.child_ids) == 1
        assert result.session.elements.get(div.child_ids[0]).component.name == "Td"


class TestHtmlContainerBehavior:
    """Tests for container vs non-container element behavior."""

    def test_section_is_container(self, rendered) -> None:
        """Section element supports children via with block."""

        @component
        def App() -> None:
            with h.Section():
                h.H1("Section Title")
                h.P("Section content")

        result = rendered(App)

        section = result.session.elements.get(result.root_element.child_ids[0])
        assert section.component.name == "Section"
        assert len(section.child_ids) == 2

    def test_article_is_container(self, rendered) -> None:
        """Article element supports children."""

        @component
        def App() -> None:
            with h.Article():
                h.H2("Article Title")

        result = rendered(App)

        article = result.session.elements.get(result.root_element.child_ids[0])
        assert article.component.name == "Article"
        assert len(article.child_ids) == 1

    def test_ul_with_li_children(self, rendered) -> None:
        """List elements work together."""

        @component
        def App() -> None:
            with h.Ul():
                h.Li("Item 1")
                h.Li("Item 2")
                h.Li("Item 3")

        result = rendered(App)

        ul = result.session.elements.get(result.root_element.child_ids[0])
        assert ul.component.name == "Ul"
        assert len(ul.child_ids) == 3

        for i, li_id in enumerate(ul.child_ids):
            li = result.session.elements.get(li_id)
            assert li.component.name == "Li"
            assert li.properties["_text"] == f"Item {i + 1}"
