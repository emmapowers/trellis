"""Generated HTML scripting and templates runtime wrappers.

Internal codegen artifact for trellis.html.
Reference: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements

Generated at: 2026-03-11T22:46:25.136Z
"""

from __future__ import annotations

from trellis.html._runtime_factory import create_html_element

__all__ = [
    "Noscript",
    "Script",
    "Slot",
    "Template",
]

Noscript = create_html_element(
    "noscript",
    component_name="Noscript",
    export_name="Noscript",
    is_container=True,
    doc="Generated wrapper for `<noscript>`.\n\nMaps to the standard HTML `<noscript>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/noscript",
)
Script = create_html_element(
    "script",
    component_name="Script",
    export_name="Script",
    doc="Generated wrapper for `<script>`.\n\nMaps to the standard HTML `<script>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/script",
)
Slot = create_html_element(
    "slot",
    component_name="Slot",
    export_name="Slot",
    is_container=True,
    doc="Generated wrapper for `<slot>`.\n\nMaps to the standard HTML `<slot>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/slot",
)
Template = create_html_element(
    "template",
    component_name="Template",
    export_name="Template",
    is_container=True,
    doc="Generated wrapper for `<template>`.\n\nMaps to the standard HTML `<template>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/template",
)
