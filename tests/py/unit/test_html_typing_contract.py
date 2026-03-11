"""Static typing contracts for HTML wrapper return types."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path


def test_container_html_wrappers_type_as_html_container_element(tmp_path: Path) -> None:
    """Container wrappers should narrow to HtmlContainerElement for static typing."""
    snippet = textwrap.dedent(
        """
        from typing import assert_type

        from trellis import html as h
        from trellis.core.rendering.element import Element
        from trellis.html._generated_interactive_elements import _A
        from trellis.html.base import HtmlContainerElement

        assert_type(_A(), HtmlContainerElement)
        assert_type(h.Div(), HtmlContainerElement)
        assert_type(h.Div(class_name="shell", data={"test-id": "hero"}), HtmlContainerElement)
        assert_type(h.P(), HtmlContainerElement)
        assert_type(h.A(), HtmlContainerElement)
        assert_type(h.A(href="/docs", aria_label="Docs"), HtmlContainerElement)
        assert_type(h.Audio(auto_play=True, controls=True), HtmlContainerElement)
        assert_type(h.P("hello"), Element)
        assert_type(h.Style(color="red", background_color="blue"), h.Style)
        assert_type(h.Style(backgroundColor="red"), h.Style)
        assert_type(h.media(min_width=640, style=h.Style(color="red")), h.MediaRule)
        """
    )
    snippet_path = tmp_path / "html_typing_contract.py"
    snippet_path.write_text(snippet)

    result = subprocess.run(
        [sys.executable, "-m", "mypy", str(snippet_path)],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[4],
    )

    assert result.returncode == 0, result.stdout + result.stderr
