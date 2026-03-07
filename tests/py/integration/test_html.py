"""Tests for native HTML elements."""

import pytest

from trellis import html as h
from trellis.core.components.composition import component
from trellis.core.rendering.element import ContainerElement
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

    def test_div_element_is_container_element_type(self, rendered) -> None:
        """Container html elements create ContainerElement instances."""

        @component
        def App() -> None:
            with h.Div():
                pass

        result = rendered(App)
        div = result.session.elements.get(result.root_element.child_ids[0])

        assert isinstance(div, ContainerElement)

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
        """Elements accept class_name prop."""

        @component
        def App() -> None:
            with h.Div(class_name="container"):
                pass

        result = rendered(App)

        div = result.session.elements.get(result.root_element.child_ids[0])
        assert div.properties["class_name"] == "container"

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
        """on_click handler serializes as callback reference."""
        clicked = []

        @component
        def App() -> None:
            with h.Div(on_click=lambda: clicked.append(True)):
                pass

        result = rendered(App)

        serialized = serialize_element(result.root_element, result.session)
        div_data = serialized["children"][0]

        assert "__callback__" in div_data["props"]["on_click"]

        # Verify callback works
        cb_id = div_data["props"]["on_click"]["__callback__"]
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

    def test_hybrid_text_with_block_raises_type_error(self, rendered) -> None:
        """Using with on a text hybrid element raises TypeError."""

        @component
        def App() -> None:
            with h.Div():
                with h.Td("text"):
                    pass

        with pytest.raises(TypeError, match=r"Cannot use.*with.*text content"):
            rendered(App)


class TestTextElementsAsContainers:
    """Tests for text elements used as containers (hybrid mode)."""

    def test_p_as_container(self, rendered) -> None:
        """P can be used as a container with children."""

        @component
        def App() -> None:
            with h.P():
                h.Strong("bold")

        result = rendered(App)

        p = result.session.elements.get(result.root_element.child_ids[0])
        assert p.component.name == "P"
        assert len(p.child_ids) == 1
        assert result.session.elements.get(p.child_ids[0]).component.name == "Strong"

    def test_p_as_text_still_works(self, rendered) -> None:
        """P("text") still works as text-only."""

        @component
        def App() -> None:
            h.P("text content")

        result = rendered(App)

        p = result.session.elements.get(result.root_element.child_ids[0])
        assert p.properties["_text"] == "text content"

    def test_p_as_empty_text_still_works(self, rendered) -> None:
        """P("") stays in text mode with explicit empty text."""

        @component
        def App() -> None:
            h.P("")

        result = rendered(App)

        p = result.session.elements.get(result.root_element.child_ids[0])
        assert p.properties["_text"] == ""

    def test_p_text_with_block_raises(self, rendered) -> None:
        """P("text") with block raises TypeError."""

        @component
        def App() -> None:
            with h.P("text"):
                pass

        with pytest.raises(TypeError, match=r"Cannot use.*with.*text content"):
            rendered(App)

    def test_span_empty_text_with_block_raises(self, rendered) -> None:
        """Span("") with block raises TypeError."""

        @component
        def App() -> None:
            with h.Span(""):
                pass

        with pytest.raises(TypeError, match=r"Cannot use.*with.*text content"):
            rendered(App)

    def test_span_as_container(self, rendered) -> None:
        """Span can be used as a container."""

        @component
        def App() -> None:
            with h.Span():
                h.Strong("inner")

        result = rendered(App)

        span = result.session.elements.get(result.root_element.child_ids[0])
        assert span.component.name == "Span"
        assert len(span.child_ids) == 1

    def test_h1_as_container(self, rendered) -> None:
        """H1 can be used as a container."""

        @component
        def App() -> None:
            with h.H1():
                h.Span("styled heading")

        result = rendered(App)

        h1 = result.session.elements.get(result.root_element.child_ids[0])
        assert h1.component.name == "H1"
        assert len(h1.child_ids) == 1

    def test_strong_as_container(self, rendered) -> None:
        """Strong can be used as a container."""

        @component
        def App() -> None:
            with h.Strong():
                h.Em("bold and italic")

        result = rendered(App)

        strong = result.session.elements.get(result.root_element.child_ids[0])
        assert strong.component.name == "Strong"
        assert len(strong.child_ids) == 1

    def test_em_as_container(self, rendered) -> None:
        """Em can be used as a container."""

        @component
        def App() -> None:
            with h.Em():
                h.Strong("italic and bold")

        result = rendered(App)

        em = result.session.elements.get(result.root_element.child_ids[0])
        assert em.component.name == "Em"
        assert len(em.child_ids) == 1

    def test_code_as_container(self, rendered) -> None:
        """Code can be used as a container."""

        @component
        def App() -> None:
            with h.Code():
                h.Span("code content")

        result = rendered(App)

        code = result.session.elements.get(result.root_element.child_ids[0])
        assert code.component.name == "Code"
        assert len(code.child_ids) == 1

    def test_pre_containing_code(self, rendered) -> None:
        """Pre can contain Code (common pattern)."""

        @component
        def App() -> None:
            with h.Pre():
                h.Code("code block")

        result = rendered(App)

        pre = result.session.elements.get(result.root_element.child_ids[0])
        assert pre.component.name == "Pre"
        assert len(pre.child_ids) == 1
        assert result.session.elements.get(pre.child_ids[0]).component.name == "Code"


class TestNewTextElements:
    """Tests for new text/inline elements."""

    def test_br_renders_as_void(self, rendered) -> None:
        @component
        def App() -> None:
            with h.Div():
                h.P("Line 1")
                h.Br()
                h.P("Line 2")

        result = rendered(App)
        div = result.session.elements.get(result.root_element.child_ids[0])
        assert len(div.child_ids) == 3
        br = result.session.elements.get(div.child_ids[1])
        assert br.component.name == "Br"
        assert len(br.child_ids) == 0

    def test_hr_renders_as_void(self, rendered) -> None:
        @component
        def App() -> None:
            with h.Div():
                h.Hr()

        result = rendered(App)
        div = result.session.elements.get(result.root_element.child_ids[0])
        hr = result.session.elements.get(div.child_ids[0])
        assert hr.component.name == "Hr"
        assert len(hr.child_ids) == 0

    def test_small_hybrid(self, rendered) -> None:
        @component
        def App() -> None:
            h.Small("fine print")
            with h.Small():
                h.Em("italic fine print")

        result = rendered(App)
        text_small = result.session.elements.get(result.root_element.child_ids[0])
        assert text_small.properties["_text"] == "fine print"
        container_small = result.session.elements.get(result.root_element.child_ids[1])
        assert len(container_small.child_ids) == 1

    def test_mark_hybrid(self, rendered) -> None:
        @component
        def App() -> None:
            h.Mark("highlighted")

        result = rendered(App)
        mark = result.session.elements.get(result.root_element.child_ids[0])
        assert mark.properties["_text"] == "highlighted"

    def test_sub_sup_hybrid(self, rendered) -> None:
        @component
        def App() -> None:
            h.Sub("2")
            h.Sup("n")

        result = rendered(App)
        sub = result.session.elements.get(result.root_element.child_ids[0])
        sup = result.session.elements.get(result.root_element.child_ids[1])
        assert sub.properties["_text"] == "2"
        assert sup.properties["_text"] == "n"

    def test_abbr_with_title(self, rendered) -> None:
        @component
        def App() -> None:
            h.Abbr("HTML", title="HyperText Markup Language")

        result = rendered(App)
        abbr = result.session.elements.get(result.root_element.child_ids[0])
        assert abbr.properties["_text"] == "HTML"
        assert abbr.properties["title"] == "HyperText Markup Language"

    def test_time_with_datetime(self, rendered) -> None:
        @component
        def App() -> None:
            h.Time("March 1", date_time="2026-03-01")

        result = rendered(App)
        time_el = result.session.elements.get(result.root_element.child_ids[0])
        assert time_el.properties["_text"] == "March 1"
        assert time_el.properties["date_time"] == "2026-03-01"


class TestNewLayoutElements:
    """Tests for new layout/structural elements."""

    def test_blockquote_hybrid(self, rendered) -> None:
        @component
        def App() -> None:
            h.Blockquote("A wise quote", cite="https://example.com")

        result = rendered(App)
        bq = result.session.elements.get(result.root_element.child_ids[0])
        assert bq.properties["_text"] == "A wise quote"
        assert bq.properties["cite"] == "https://example.com"

    def test_blockquote_as_container(self, rendered) -> None:
        @component
        def App() -> None:
            with h.Blockquote():
                h.P("Quote paragraph")

        result = rendered(App)
        bq = result.session.elements.get(result.root_element.child_ids[0])
        assert len(bq.child_ids) == 1

    def test_address_container(self, rendered) -> None:
        @component
        def App() -> None:
            with h.Address():
                h.P("123 Main St")

        result = rendered(App)
        addr = result.session.elements.get(result.root_element.child_ids[0])
        assert addr.component.name == "Address"
        assert len(addr.child_ids) == 1

    def test_details_summary(self, rendered) -> None:
        @component
        def App() -> None:
            with h.Details(open=True):
                h.Summary("Click to expand")
                h.P("Hidden content")

        result = rendered(App)
        details = result.session.elements.get(result.root_element.child_ids[0])
        assert details.component.name == "Details"
        assert details.properties["open"] is True
        assert len(details.child_ids) == 2
        summary = result.session.elements.get(details.child_ids[0])
        assert summary.component.name == "Summary"
        assert summary.properties["_text"] == "Click to expand"

    def test_figure_figcaption(self, rendered) -> None:
        @component
        def App() -> None:
            with h.Figure():
                h.Img(src="photo.jpg")
                h.Figcaption("A beautiful photo")

        result = rendered(App)
        figure = result.session.elements.get(result.root_element.child_ids[0])
        assert figure.component.name == "Figure"
        assert len(figure.child_ids) == 2
        caption = result.session.elements.get(figure.child_ids[1])
        assert caption.component.name == "Figcaption"
        assert caption.properties["_text"] == "A beautiful photo"


class TestNewListElements:
    """Tests for definition list elements."""

    def test_dl_dt_dd(self, rendered) -> None:
        @component
        def App() -> None:
            with h.Dl():
                h.Dt("Term")
                h.Dd("Definition")

        result = rendered(App)
        dl = result.session.elements.get(result.root_element.child_ids[0])
        assert dl.component.name == "Dl"
        assert len(dl.child_ids) == 2
        dt = result.session.elements.get(dl.child_ids[0])
        dd = result.session.elements.get(dl.child_ids[1])
        assert dt.properties["_text"] == "Term"
        assert dd.properties["_text"] == "Definition"

    def test_dt_dd_as_containers(self, rendered) -> None:
        @component
        def App() -> None:
            with h.Dl():
                with h.Dt():
                    h.Strong("Term")
                with h.Dd():
                    h.P("Definition paragraph")

        result = rendered(App)
        dl = result.session.elements.get(result.root_element.child_ids[0])
        dt = result.session.elements.get(dl.child_ids[0])
        dd = result.session.elements.get(dl.child_ids[1])
        assert len(dt.child_ids) == 1
        assert len(dd.child_ids) == 1


class TestNewTableElements:
    """Tests for new table elements."""

    def test_tfoot_container(self, rendered) -> None:
        @component
        def App() -> None:
            with h.Table():
                with h.Tfoot():
                    with h.Tr():
                        h.Td("Total")

        result = rendered(App)
        table = result.session.elements.get(result.root_element.child_ids[0])
        tfoot = result.session.elements.get(table.child_ids[0])
        assert tfoot.component.name == "Tfoot"
        assert len(tfoot.child_ids) == 1

    def test_caption_hybrid(self, rendered) -> None:
        @component
        def App() -> None:
            with h.Table():
                h.Caption("Table title")

        result = rendered(App)
        table = result.session.elements.get(result.root_element.child_ids[0])
        caption = result.session.elements.get(table.child_ids[0])
        assert caption.component.name == "Caption"
        assert caption.properties["_text"] == "Table title"


class TestNewFormElements:
    """Tests for new form elements."""

    def test_button_and_label_use_generated_public_names(self, rendered) -> None:
        @component
        def App() -> None:
            h.Label("Name", html_for="name-input")
            with h.Label(html_for="nested-name-input"):
                h.Input(id="nested-name-input", type="text")
            h.Button("Save", type="submit")

        result = rendered(App)
        label = result.session.elements.get(result.root_element.child_ids[0])
        nested_label = result.session.elements.get(result.root_element.child_ids[1])
        button = result.session.elements.get(result.root_element.child_ids[2])

        assert label.component.name == "Label"
        assert label.properties["_text"] == "Name"
        assert label.properties["html_for"] == "name-input"
        assert nested_label.component.name == "Label"
        assert nested_label.properties["html_for"] == "nested-name-input"
        assert len(nested_label.child_ids) == 1
        assert button.component.name == "Button"
        assert button.properties["_text"] == "Save"
        assert button.properties["type"] == "submit"

    def test_fieldset_legend(self, rendered) -> None:
        @component
        def App() -> None:
            with h.Fieldset():
                h.Legend("Personal Info")
                h.Input(type="text", name="name")

        result = rendered(App)
        fieldset = result.session.elements.get(result.root_element.child_ids[0])
        assert fieldset.component.name == "Fieldset"
        assert len(fieldset.child_ids) == 2
        legend = result.session.elements.get(fieldset.child_ids[0])
        assert legend.properties["_text"] == "Personal Info"

    def test_fieldset_disabled(self, rendered) -> None:
        @component
        def App() -> None:
            with h.Fieldset(disabled=True):
                h.Input(type="text")

        result = rendered(App)
        fieldset = result.session.elements.get(result.root_element.child_ids[0])
        assert fieldset.properties["disabled"] is True

    def test_optgroup(self, rendered) -> None:
        @component
        def App() -> None:
            with h.Select():
                with h.Optgroup(label="Group 1"):
                    h.Option("A", value="a")
                    h.Option("B", value="b")

        result = rendered(App)
        select = result.session.elements.get(result.root_element.child_ids[0])
        optgroup = result.session.elements.get(select.child_ids[0])
        assert optgroup.component.name == "Optgroup"
        assert optgroup.properties["label"] == "Group 1"
        assert len(optgroup.child_ids) == 2

    def test_progress(self, rendered) -> None:
        @component
        def App() -> None:
            h.Progress(value=0.7, max=1.0)

        result = rendered(App)
        progress = result.session.elements.get(result.root_element.child_ids[0])
        assert progress.component.name == "Progress"
        assert progress.properties["value"] == 0.7
        assert progress.properties["max"] == 1.0

    def test_meter(self, rendered) -> None:
        @component
        def App() -> None:
            h.Meter(value=0.6, min=0.0, max=1.0, low=0.25, high=0.75, optimum=0.5)

        result = rendered(App)
        meter = result.session.elements.get(result.root_element.child_ids[0])
        assert meter.component.name == "Meter"
        assert meter.properties["value"] == 0.6

    def test_output_hybrid(self, rendered) -> None:
        @component
        def App() -> None:
            h.Output("Result: 42", name="result")

        result = rendered(App)
        output = result.session.elements.get(result.root_element.child_ids[0])
        assert output.properties["_text"] == "Result: 42"
        assert output.properties["name"] == "result"

    def test_datalist(self, rendered) -> None:
        @component
        def App() -> None:
            with h.Datalist(id="browsers"):
                h.Option("Chrome", value="chrome")
                h.Option("Firefox", value="firefox")

        result = rendered(App)
        datalist = result.session.elements.get(result.root_element.child_ids[0])
        assert datalist.component.name == "Datalist"
        assert len(datalist.child_ids) == 2


class TestNewMediaElements:
    """Tests for media/embed elements."""

    def test_img_allows_missing_src(self, rendered) -> None:
        @component
        def App() -> None:
            h.Img()

        result = rendered(App)
        image = result.session.elements.get(result.root_element.child_ids[0])
        assert image.component.name == "Img"
        assert "src" not in image.properties

    def test_video_container(self, rendered) -> None:
        @component
        def App() -> None:
            with h.Video(controls=True, width=640, height=480):
                h.Source(src="video.mp4", type="video/mp4")

        result = rendered(App)
        video = result.session.elements.get(result.root_element.child_ids[0])
        assert video.component.name == "Video"
        assert video.properties["controls"] is True
        assert video.properties["width"] == 640
        source = result.session.elements.get(video.child_ids[0])
        assert source.component.name == "Source"
        assert source.properties["src"] == "video.mp4"

    def test_audio_container(self, rendered) -> None:
        @component
        def App() -> None:
            with h.Audio(controls=True):
                h.Source(src="song.mp3", type="audio/mpeg")

        result = rendered(App)
        audio = result.session.elements.get(result.root_element.child_ids[0])
        assert audio.component.name == "Audio"
        assert audio.properties["controls"] is True
        assert len(audio.child_ids) == 1

    def test_source_void(self, rendered) -> None:
        @component
        def App() -> None:
            with h.Video():
                h.Source(src="video.mp4", type="video/mp4")
                h.Source(src="video.webm", type="video/webm")

        result = rendered(App)
        video = result.session.elements.get(result.root_element.child_ids[0])
        assert len(video.child_ids) == 2
        for child_id in video.child_ids:
            source = result.session.elements.get(child_id)
            assert len(source.child_ids) == 0

    def test_iframe(self, rendered) -> None:
        @component
        def App() -> None:
            h.Iframe(src="https://example.com", title="Example", width=800, height=600)

        result = rendered(App)
        iframe = result.session.elements.get(result.root_element.child_ids[0])
        assert iframe.component.name == "Iframe"
        assert iframe.properties["src"] == "https://example.com"
        assert iframe.properties["title"] == "Example"
        assert iframe.properties["width"] == 800


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
