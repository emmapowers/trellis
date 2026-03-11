"""Generated HTML embedded content runtime wrappers.

Internal codegen artifact for trellis.html.
Reference: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements

Generated at: 2026-03-11T22:46:25.136Z
"""

from __future__ import annotations

from trellis.html._runtime_factory import create_html_element

__all__ = [
    "Canvas",
    "Embed",
    "Iframe",
    "Object",
    "Param",
]

Canvas = create_html_element(
    "canvas",
    component_name="Canvas",
    export_name="Canvas",
    is_container=True,
    doc="Generated wrapper for `<canvas>`.\n\nMaps to the standard HTML `<canvas>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/canvas",
)
Embed = create_html_element(
    "embed",
    component_name="Embed",
    export_name="Embed",
    doc="Generated wrapper for `<embed>`.\n\nMaps to the standard HTML `<embed>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/embed",
)
Iframe = create_html_element(
    "iframe",
    component_name="Iframe",
    export_name="Iframe",
    doc="Generated wrapper for `<iframe>`.\n\nMaps to the standard HTML `<iframe>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/iframe",
)
Object = create_html_element(
    "object",
    component_name="Object",
    export_name="Object",
    is_container=True,
    doc="Generated wrapper for `<object>`.\n\nMaps to the standard HTML `<object>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/object",
)
Param = create_html_element(
    "param",
    component_name="Param",
    export_name="Param",
    doc="Generated wrapper for `<param>`.\n\nMaps to the standard HTML `<param>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/param",
)
