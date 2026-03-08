"""Native HTML and CSS wrappers for Trellis.

Provides Python wrappers for standard HTML elements plus typed CSS helpers that
render directly to native DOM elements in React, without requiring separate
React components.

Example:
    ```python
    from trellis import html as h

    with h.Div(class_name="container", style=h.Style(padding=16)):
        h.H1("Welcome", style=h.Style(color="blue"))
        h.P("This is a paragraph.")
        h.A("Click here", href="/about")
    ```

Categories:
    - Layout: Div, Span, Section, Article, Header, Footer, Nav, Main, Aside,
              Blockquote, Address, Details, Summary, Figure, Figcaption
    - Text: P, H1-H6, Strong, Em, Code, Pre, Br, Hr, Small, Mark, Sub, Sup,
            Abbr, Time
    - Lists: Ul, Ol, Li, Dl, Dt, Dd
    - Links: A, Img
    - Forms: Form, Input, Button, Textarea, Select, Option, Label,
             Fieldset, Legend, Optgroup, Progress, Meter, Output, Datalist
    - Tables: Table, Thead, Tbody, Tfoot, Tr, Th, Td, Caption
    - Media: Video, Audio, Source, Iframe
    - CSS: Style, media, px, rem, rgb, border, padding, margin, shadow
"""

from trellis.html import _generated_events as _generated_events
from trellis.html import _generated_runtime as _generated_runtime
from trellis.html import _generated_style_types as _generated_style_types
from trellis.html import _style_runtime as _style_runtime
from trellis.html._generated_events import *
from trellis.html._generated_runtime import *
from trellis.html._style_runtime import *
from trellis.html.base import HtmlContainerTrait, HtmlElement
from trellis.html.links import A
from trellis.html.text import Text

_event_exports = [
    name for name in _generated_events.__all__ if name not in {"EVENT_TYPE_MAP", "get_event_class"}
]

_css_exports = [
    "MediaRule",
    "Style",
    "StyleInput",
    "border",
    "calc",
    "clamp",
    "color",
    "color_space",
    "deg",
    "em",
    "hsl",
    "hwb",
    "inset",
    "lab",
    "lch",
    "margin",
    "max_",
    "media",
    "min_",
    "ms",
    "oklab",
    "oklch",
    "padding",
    "pct",
    "px",
    "raw",
    "rem",
    "rgb",
    "rgba",
    "rotate",
    "scale",
    "sec",
    "shadow",
    "translate",
    "var",
    "vh",
    "vw",
]
MediaRule = _generated_style_types.MediaRule

__all__ = [
    "A",
    "HtmlContainerTrait",
    "HtmlElement",
    "Text",
]
__all__.extend(_generated_runtime.__all__)
__all__.extend(_event_exports)
__all__.extend(_css_exports)
