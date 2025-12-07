"""Native HTML element wrappers for Trellis.

Provides Python wrappers for common HTML elements that render directly
as native DOM elements in React, without requiring separate React components.

Example:
    ```python
    from trellis import html as h

    with h.Div(className="container", style={"padding": "16px"}):
        h.H1("Welcome", style={"color": "blue"})
        h.P("This is a paragraph.")
        h.A("Click here", href="/about")
    ```

Categories:
    - Layout: Div, Span, Section, Article, Header, Footer, Nav, Main, Aside
    - Text: P, H1-H6, Strong, Em, Code, Pre
    - Lists: Ul, Ol, Li
    - Links: A, Img
    - Forms: Form, Input, HtmlButton, Textarea, Select, Option, HtmlLabel
    - Tables: Table, Thead, Tbody, Tr, Th, Td
"""

# Base types
from trellis.html.base import HtmlElement, Style

# Event types
from trellis.html.events import (
    BaseEvent,
    ChangeEvent,
    ChangeEventHandler,
    ChangeHandler,
    EventHandler,
    FocusEvent,
    FocusEventHandler,
    FocusHandler,
    FormEvent,
    FormEventHandler,
    FormHandler,
    InputEvent,
    InputEventHandler,
    InputHandler,
    KeyboardEvent,
    KeyboardEventHandler,
    KeyboardHandler,
    MouseEvent,
    MouseEventHandler,
    MouseHandler,
)

# Form elements
from trellis.html.forms import (
    Form,
    HtmlButton,
    HtmlLabel,
    Input,
    Option,
    Select,
    Textarea,
)

# Layout elements
from trellis.html.layout import (
    Article,
    Aside,
    Div,
    Footer,
    Header,
    Main,
    Nav,
    Section,
    Span,
)

# Link and media elements
from trellis.html.links import (
    A,
    Img,
)

# List elements
from trellis.html.lists import (
    Li,
    Ol,
    Ul,
)

# Table elements
from trellis.html.tables import (
    Table,
    Tbody,
    Td,
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
    Code,
    Em,
    P,
    Pre,
    Strong,
)

__all__ = [
    "H1",
    "H2",
    "H3",
    "H4",
    "H5",
    "H6",
    "A",
    "Article",
    "Aside",
    "BaseEvent",
    "ChangeEvent",
    "ChangeEventHandler",
    "ChangeHandler",
    "Code",
    "Div",
    "Em",
    "EventHandler",
    "FocusEvent",
    "FocusEventHandler",
    "FocusHandler",
    "Footer",
    "Form",
    "FormEvent",
    "FormEventHandler",
    "FormHandler",
    "Header",
    "HtmlButton",
    "HtmlElement",
    "HtmlLabel",
    "Img",
    "Input",
    "InputEvent",
    "InputEventHandler",
    "InputHandler",
    "KeyboardEvent",
    "KeyboardEventHandler",
    "KeyboardHandler",
    "Li",
    "Main",
    "MouseEvent",
    "MouseEventHandler",
    "MouseHandler",
    "Nav",
    "Ol",
    "Option",
    "P",
    "Pre",
    "Section",
    "Select",
    "Span",
    "Strong",
    "Style",
    "Table",
    "Tbody",
    "Td",
    "Textarea",
    "Th",
    "Thead",
    "Tr",
    "Ul",
]
