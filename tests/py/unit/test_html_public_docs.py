from __future__ import annotations

from trellis import html as h


def test_html_public_css_api_has_user_facing_docstrings() -> None:
    assert h.Style.__doc__ is not None
    assert "CSS properties" in h.Style.__doc__
    assert "raw dicts" in h.Style.__doc__ or "CssClass" in h.Style.__doc__

    assert h.media.__doc__ is not None
    assert "typed CSS media rule" in h.media.__doc__

    assert h.px.__doc__ == "Return a CSS length in pixels."
    assert h.border.__doc__ is not None
    assert "border" in h.border.__doc__
    assert "shorthand value" in h.border.__doc__


def test_html_public_link_and_text_docs_explain_trellis_behavior() -> None:
    assert h.A.__doc__ is not None
    assert "adds Trellis router navigation" in h.A.__doc__
    assert "relative links by default" in h.A.__doc__

    assert h.Text.__doc__ == "A plain text node without any wrapper element."
