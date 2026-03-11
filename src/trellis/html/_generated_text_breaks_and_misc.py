"""Generated HTML text breaks and misc runtime wrappers.

Internal codegen artifact for trellis.html.
Reference: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements

Generated at: 2026-03-11T22:46:25.136Z
"""

from __future__ import annotations

from trellis.html._runtime_factory import create_html_element

__all__ = [
    "Br",
    "Hr",
    "Wbr",
]

Br = create_html_element(
    "br",
    component_name="Br",
    export_name="Br",
    doc="Generated wrapper for `<br>`.\n\nMaps to the standard HTML `<br>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/br",
)
Hr = create_html_element(
    "hr",
    component_name="Hr",
    export_name="Hr",
    doc="Generated wrapper for `<hr>`.\n\nMaps to the standard HTML `<hr>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/hr",
)
Wbr = create_html_element(
    "wbr",
    component_name="Wbr",
    export_name="Wbr",
    doc="Generated wrapper for `<wbr>`.\n\nMaps to the standard HTML `<wbr>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/wbr",
)
