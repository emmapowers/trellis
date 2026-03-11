"""Generated HTML image and multimedia runtime wrappers.

Internal codegen artifact for trellis.html.
Reference: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements

Generated at: 2026-03-11T22:46:25.136Z
"""

from __future__ import annotations

from trellis.html._runtime_factory import create_html_element

__all__ = [
    "Area",
    "Audio",
    "Img",
    "Map",
    "Picture",
    "Source",
    "Track",
    "Video",
]

Area = create_html_element(
    "area",
    component_name="Area",
    export_name="Area",
    doc="Generated wrapper for `<area>`.\n\nMaps to the standard HTML `<area>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/area",
)
Audio = create_html_element(
    "audio",
    component_name="Audio",
    export_name="Audio",
    is_container=True,
    doc="Generated wrapper for `<audio>`.\n\nMaps to the standard HTML `<audio>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/audio",
)
Img = create_html_element(
    "img",
    component_name="Img",
    export_name="Img",
    doc="Generated wrapper for `<img>`.\n\nMaps to the standard HTML `<img>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/img",
)
Map = create_html_element(
    "map",
    component_name="Map",
    export_name="Map",
    is_container=True,
    doc="Generated wrapper for `<map>`.\n\nMaps to the standard HTML `<map>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/map",
)
Picture = create_html_element(
    "picture",
    component_name="Picture",
    export_name="Picture",
    is_container=True,
    doc="Generated wrapper for `<picture>`.\n\nMaps to the standard HTML `<picture>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/picture",
)
Source = create_html_element(
    "source",
    component_name="Source",
    export_name="Source",
    doc="Generated wrapper for `<source>`.\n\nMaps to the standard HTML `<source>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/source",
)
Track = create_html_element(
    "track",
    component_name="Track",
    export_name="Track",
    doc="Generated wrapper for `<track>`.\n\nMaps to the standard HTML `<track>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/track",
)
Video = create_html_element(
    "video",
    component_name="Video",
    export_name="Video",
    is_container=True,
    doc="Generated wrapper for `<video>`.\n\nMaps to the standard HTML `<video>` element.\nReference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/video",
)
