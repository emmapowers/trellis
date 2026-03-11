"""Generated HTML text edits and ruby runtime wrappers.

Internal codegen artifact for trellis.html.
Reference: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements

Generated at: 2026-03-11T22:46:25.136Z
"""

from __future__ import annotations

from trellis.html._runtime_factory import create_html_element

__all__ = [
    "Del",
    "Ins",
    "Rp",
    "Rt",
    "Ruby",
]

Del = create_html_element(
    "del",
    component_name="Del",
    export_name="Del",
    is_container=True,
    doc="Generated wrapper for `<del>`.\n\nMaps to the standard HTML `<del>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/del",
)
Ins = create_html_element(
    "ins",
    component_name="Ins",
    export_name="Ins",
    is_container=True,
    doc="Generated wrapper for `<ins>`.\n\nMaps to the standard HTML `<ins>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/ins",
)
Rp = create_html_element(
    "rp",
    component_name="Rp",
    export_name="Rp",
    doc="Generated wrapper for `<rp>`.\n\nMaps to the standard HTML `<rp>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/rp",
)
Rt = create_html_element(
    "rt",
    component_name="Rt",
    export_name="Rt",
    is_container=True,
    doc="Generated wrapper for `<rt>`.\n\nMaps to the standard HTML `<rt>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/rt",
)
Ruby = create_html_element(
    "ruby",
    component_name="Ruby",
    export_name="Ruby",
    is_container=True,
    doc="Generated wrapper for `<ruby>`.\n\nMaps to the standard HTML `<ruby>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/ruby",
)
