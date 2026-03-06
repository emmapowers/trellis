"""Native HTML element wrappers for Trellis.

Provides Python wrappers for common HTML elements that render directly
as native DOM elements in React, without requiring separate React components.

Example:
    ```python
    from trellis import html as h

    with h.Div(class_name="container", style={"padding": "16px"}):
        h.H1("Welcome", style={"color": "blue"})
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
    - Forms: Form, Input, HtmlButton, Textarea, Select, Option, HtmlLabel,
             Fieldset, Legend, Optgroup, Progress, Meter, Output, Datalist
    - Tables: Table, Thead, Tbody, Tfoot, Tr, Th, Td, Caption
    - Media: Video, Audio, Source, Iframe
"""

# Base types
from trellis.html.base import HtmlContainerTrait, HtmlElement, Style

# Event types
from trellis.html.events import (
    ChangeEvent,
    ChangeEventHandler,
    DataTransfer,
    DragEvent,
    DragEventHandler,
    Event,
    EventHandler,
    File,
    FocusEvent,
    FocusEventHandler,
    InputEvent,
    InputEventHandler,
    KeyboardEvent,
    KeyboardEventHandler,
    MouseEvent,
    MouseEventHandler,
    SubmitEvent,
    SubmitEventHandler,
    UIEvent,
    UIEventHandler,
    WheelEvent,
    WheelEventHandler,
)

# Form elements
from trellis.html.forms import (
    Datalist,
    Fieldset,
    Form,
    HtmlButton,
    HtmlLabel,
    Input,
    Legend,
    Meter,
    Optgroup,
    Option,
    Output,
    Progress,
    Select,
    Textarea,
)

# Layout elements
from trellis.html.layout import (
    Address,
    Article,
    Aside,
    Blockquote,
    Details,
    Div,
    Figcaption,
    Figure,
    Footer,
    Header,
    Main,
    Nav,
    Section,
    Span,
    Summary,
)

# Link and media elements
from trellis.html.links import (
    A,
    Img,
)

# List elements
from trellis.html.lists import (
    Dd,
    Dl,
    Dt,
    Li,
    Ol,
    Ul,
)

# Media elements
from trellis.html.media import (
    Audio,
    Iframe,
    Source,
    Video,
)

# Table elements
from trellis.html.tables import (
    Caption,
    Table,
    Tbody,
    Td,
    Tfoot,
    Th,
    Thead,
    Tr,
)

# Text elements
from trellis.html.text import (
    H1,
    H2,
    H3,
    H4,
    H5,
    H6,
    Abbr,
    Br,
    Code,
    Em,
    Hr,
    Mark,
    P,
    Pre,
    Small,
    Strong,
    Sub,
    Sup,
    Text,
    Time,
)

__all__ = [
    "H1",
    "H2",
    "H3",
    "H4",
    "H5",
    "H6",
    "A",
    "Abbr",
    "Address",
    "Article",
    "Aside",
    "Audio",
    "Blockquote",
    "Br",
    "Caption",
    "ChangeEvent",
    "ChangeEventHandler",
    "Code",
    "DataTransfer",
    "Datalist",
    "Dd",
    "Details",
    "Div",
    "Dl",
    "DragEvent",
    "DragEventHandler",
    "Dt",
    "Em",
    "Event",
    "EventHandler",
    "Fieldset",
    "Figcaption",
    "Figure",
    "File",
    "FocusEvent",
    "FocusEventHandler",
    "Footer",
    "Form",
    "Header",
    "Hr",
    "HtmlButton",
    "HtmlContainerTrait",
    "HtmlElement",
    "HtmlLabel",
    "Iframe",
    "Img",
    "Input",
    "InputEvent",
    "InputEventHandler",
    "KeyboardEvent",
    "KeyboardEventHandler",
    "Legend",
    "Li",
    "Main",
    "Mark",
    "Meter",
    "MouseEvent",
    "MouseEventHandler",
    "Nav",
    "Ol",
    "Optgroup",
    "Option",
    "Output",
    "P",
    "Pre",
    "Progress",
    "Section",
    "Select",
    "Small",
    "Source",
    "Span",
    "Strong",
    "Style",
    "Sub",
    "SubmitEvent",
    "SubmitEventHandler",
    "Summary",
    "Sup",
    "Table",
    "Tbody",
    "Td",
    "Text",
    "Textarea",
    "Tfoot",
    "Th",
    "Thead",
    "Time",
    "Tr",
    "UIEvent",
    "UIEventHandler",
    "Ul",
    "Video",
    "WheelEvent",
    "WheelEventHandler",
]
