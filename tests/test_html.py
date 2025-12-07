"""Tests for native HTML elements."""

from trellis import html as h
from trellis.core.functional_component import component
from trellis.core.rendering import RenderContext
from trellis.core.serialization import clear_callbacks, get_callback, serialize_element


class TestHtmlElements:
    """Tests for HTML element rendering."""

    def test_div_renders_as_container(self) -> None:
        """Div element can contain children."""

        @component
        def App() -> None:
            with h.Div():
                h.Span("Hello")

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        div = ctx.root_element.children[0]
        assert div.component.name == "Div"
        assert len(div.children) == 1
        assert div.children[0].component.name == "Span"

    def test_nested_divs(self) -> None:
        """Divs can be nested."""

        @component
        def App() -> None:
            with h.Div():
                with h.Div():
                    h.Span("Nested")

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        outer = ctx.root_element.children[0]
        inner = outer.children[0]
        span = inner.children[0]

        assert outer.component.name == "Div"
        assert inner.component.name == "Div"
        assert span.component.name == "Span"

    def test_text_element_stores_text(self) -> None:
        """Text elements store text in _text prop."""

        @component
        def App() -> None:
            h.H1("Page Title")
            h.P("Paragraph text")
            h.Span("Inline text")

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        h1 = ctx.root_element.children[0]
        p = ctx.root_element.children[1]
        span = ctx.root_element.children[2]

        assert h1.properties["_text"] == "Page Title"
        assert p.properties["_text"] == "Paragraph text"
        assert span.properties["_text"] == "Inline text"

    def test_element_with_style(self) -> None:
        """Elements accept style dict."""

        @component
        def App() -> None:
            with h.Div(style={"backgroundColor": "red", "padding": "10px"}):
                pass

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        div = ctx.root_element.children[0]
        assert div.properties["style"] == {"backgroundColor": "red", "padding": "10px"}

    def test_element_with_class_name(self) -> None:
        """Elements accept className prop."""

        @component
        def App() -> None:
            with h.Div(className="container"):
                pass

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        div = ctx.root_element.children[0]
        assert div.properties["className"] == "container"


class TestHtmlSerialization:
    """Tests for HTML element serialization."""

    def setup_method(self) -> None:
        """Clear callbacks between tests."""
        clear_callbacks()

    def teardown_method(self) -> None:
        """Clean up after tests."""
        clear_callbacks()

    def test_serialize_div_as_tag_name(self) -> None:
        """Div serializes with type='div' (not a React component)."""

        @component
        def App() -> None:
            with h.Div():
                pass

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        result = serialize_element(ctx.root_element)
        div_data = result["children"][0]

        assert div_data["type"] == "div"
        assert div_data["name"] == "Div"

    def test_serialize_various_tags(self) -> None:
        """Different HTML elements serialize with correct tag names."""

        @component
        def App() -> None:
            h.Span("text")
            h.H1("heading")
            h.P("paragraph")
            h.A("link", href="https://example.com")  # A is hybrid, needs text or with

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        result = serialize_element(ctx.root_element)

        assert result["children"][0]["type"] == "span"
        assert result["children"][1]["type"] == "h1"
        assert result["children"][2]["type"] == "p"
        assert result["children"][3]["type"] == "a"

    def test_serialize_text_content(self) -> None:
        """Text content is serialized in _text prop."""

        @component
        def App() -> None:
            h.H1("Hello World")

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        result = serialize_element(ctx.root_element)
        h1_data = result["children"][0]

        assert h1_data["type"] == "h1"
        assert h1_data["props"]["_text"] == "Hello World"

    def test_serialize_nested_structure(self) -> None:
        """Nested HTML elements serialize correctly."""

        @component
        def App() -> None:
            with h.Div(style={"padding": "20px"}):
                h.H1("Title")
                with h.Div():
                    h.P("Content")

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        result = serialize_element(ctx.root_element)
        outer = result["children"][0]

        assert outer["type"] == "div"
        assert outer["props"]["style"] == {"padding": "20px"}
        assert len(outer["children"]) == 2

        h1 = outer["children"][0]
        inner = outer["children"][1]

        assert h1["type"] == "h1"
        assert h1["props"]["_text"] == "Title"
        assert inner["type"] == "div"
        assert inner["children"][0]["type"] == "p"

    def test_serialize_onclick_as_callback(self) -> None:
        """onClick handler serializes as callback reference."""
        clicked = []

        @component
        def App() -> None:
            with h.Div(onClick=lambda: clicked.append(True)):
                pass

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        result = serialize_element(ctx.root_element)
        div_data = result["children"][0]

        assert "__callback__" in div_data["props"]["onClick"]

        # Verify callback works
        cb_id = div_data["props"]["onClick"]["__callback__"]
        get_callback(cb_id)()
        assert clicked == [True]

    def test_serialize_link_props(self) -> None:
        """Anchor element serializes with href and target."""

        @component
        def App() -> None:
            h.A("Click here", href="https://example.com", target="_blank")

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        result = serialize_element(ctx.root_element)
        a_data = result["children"][0]

        assert a_data["type"] == "a"
        assert a_data["props"]["_text"] == "Click here"
        assert a_data["props"]["href"] == "https://example.com"
        assert a_data["props"]["target"] == "_blank"


class TestHybridElements:
    """Tests for hybrid elements that can be text-only or containers."""

    def test_td_with_text_auto_collects(self) -> None:
        """Td with text is auto-collected without with block."""

        @component
        def App() -> None:
            with h.Tr():
                h.Td("Cell 1")
                h.Td("Cell 2")

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        tr = ctx.root_element.children[0]
        assert len(tr.children) == 2
        assert tr.children[0].properties["_text"] == "Cell 1"
        assert tr.children[1].properties["_text"] == "Cell 2"

    def test_td_as_container(self) -> None:
        """Td without text can be used as container."""

        @component
        def App() -> None:
            with h.Tr():
                with h.Td():
                    h.Strong("Bold")
                    h.Span(" text")

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        tr = ctx.root_element.children[0]
        td = tr.children[0]
        assert len(td.children) == 2
        assert td.children[0].component.name == "Strong"
        assert td.children[1].component.name == "Span"

    def test_li_with_text_auto_collects(self) -> None:
        """Li with text is auto-collected."""

        @component
        def App() -> None:
            with h.Ul():
                h.Li("Item 1")
                h.Li("Item 2")

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        ul = ctx.root_element.children[0]
        assert len(ul.children) == 2

    def test_li_as_container(self) -> None:
        """Li without text can be used as container."""

        @component
        def App() -> None:
            with h.Ul():
                with h.Li():
                    h.Strong("Bold item")

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        ul = ctx.root_element.children[0]
        li = ul.children[0]
        assert len(li.children) == 1
        assert li.children[0].component.name == "Strong"

    def test_a_with_text_auto_collects(self) -> None:
        """A with text is auto-collected."""

        @component
        def App() -> None:
            with h.Div():
                h.A("Click here", href="/path")

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        div = ctx.root_element.children[0]
        assert len(div.children) == 1
        assert div.children[0].properties["_text"] == "Click here"
        assert div.children[0].properties["href"] == "/path"

    def test_a_as_container(self) -> None:
        """A without text can be used as container."""

        @component
        def App() -> None:
            with h.Div():
                with h.A(href="/path"):
                    h.Span("Link text")

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        div = ctx.root_element.children[0]
        a = div.children[0]
        assert len(a.children) == 1
        assert a.children[0].component.name == "Span"

    def test_hybrid_no_double_collection(self) -> None:
        """Using with on a text hybrid element doesn't double-collect."""

        @component
        def App() -> None:
            with h.Div():
                # This would double-collect without the _auto_collected fix
                with h.Td("text"):
                    pass

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        div = ctx.root_element.children[0]
        # Should only have one Td child, not two
        assert len(div.children) == 1
        assert div.children[0].component.name == "Td"


class TestHtmlContainerBehavior:
    """Tests for container vs non-container element behavior."""

    def test_section_is_container(self) -> None:
        """Section element supports children via with block."""

        @component
        def App() -> None:
            with h.Section():
                h.H1("Section Title")
                h.P("Section content")

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        section = ctx.root_element.children[0]
        assert section.component.name == "Section"
        assert len(section.children) == 2

    def test_article_is_container(self) -> None:
        """Article element supports children."""

        @component
        def App() -> None:
            with h.Article():
                h.H2("Article Title")

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        article = ctx.root_element.children[0]
        assert article.component.name == "Article"
        assert len(article.children) == 1

    def test_ul_with_li_children(self) -> None:
        """List elements work together."""

        @component
        def App() -> None:
            with h.Ul():
                h.Li("Item 1")
                h.Li("Item 2")
                h.Li("Item 3")

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        ul = ctx.root_element.children[0]
        assert ul.component.name == "Ul"
        assert len(ul.children) == 3

        for i, li in enumerate(ul.children):
            assert li.component.name == "Li"
            assert li.properties["_text"] == f"Item {i + 1}"
