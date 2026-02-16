"""Integration tests for Markdown widget."""

from trellis.core.components.composition import component
from trellis.widgets import Markdown


class TestMarkdownWidget:
    """Tests for Markdown widget props."""

    def test_markdown_stores_content_and_base_path(self, rendered) -> None:
        """Markdown stores markdown content and base_path."""

        @component
        def App() -> None:
            Markdown(content="# Hello", base_path="/tmp/project")

        result = rendered(App)

        markdown = result.session.elements.get(result.root_element.child_ids[0])
        assert markdown.component.name == "Markdown"
        assert markdown.properties["content"] == "# Hello"
        assert markdown.properties["base_path"] == "/tmp/project"

    def test_markdown_defaults_to_no_base_path(self, rendered) -> None:
        """Markdown defaults to base_path=None."""

        @component
        def App() -> None:
            Markdown(content="plain text")

        result = rendered(App)

        markdown = result.session.elements.get(result.root_element.child_ids[0])
        assert markdown.properties.get("base_path") is None
