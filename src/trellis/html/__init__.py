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

from trellis.html._generated_events import *
from trellis.html._generated_runtime import *
from trellis.html._style_runtime import *
from trellis.html.base import HtmlContainerTrait as HtmlContainerTrait
from trellis.html.base import HtmlElement as HtmlElement
from trellis.html.links import A as A
from trellis.html.text import Text as Text
