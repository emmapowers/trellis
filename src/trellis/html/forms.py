"""Form HTML elements.

Elements for user input and form handling.
"""

from __future__ import annotations

import typing as tp
from typing import overload

from trellis.core.rendering.element import Element
from trellis.html.base import HtmlContainerElement, Style, html_element
from trellis.html.events import (
    EventHandler,
    FocusEventHandler,
    InputEventHandler,
    KeyboardEventHandler,
    MouseEventHandler,
    SubmitEventHandler,
)

__all__ = [
    "Datalist",
    "Fieldset",
    "Form",
    "HtmlButton",
    "HtmlLabel",
    "Input",
    "Legend",
    "Meter",
    "Optgroup",
    "Option",
    "Output",
    "Progress",
    "Select",
    "Textarea",
]


@html_element("form", is_container=True)
def Form(
    *,
    action: str | None = None,
    method: str | None = None,
    enc_type: str | None = None,
    no_validate: bool = False,
    auto_complete: str | None = None,
    on_submit: SubmitEventHandler | None = None,
    on_key_down: KeyboardEventHandler | None = None,
    on_key_up: KeyboardEventHandler | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A form element."""
    ...


@html_element("input")
def Input(
    *,
    type: str = "text",
    value: str | None = None,
    placeholder: str | None = None,
    disabled: bool = False,
    read_only: bool = False,
    name: str | None = None,
    checked: bool | None = None,
    required: bool = False,
    min: str | int | float | None = None,
    max: str | int | float | None = None,
    step: str | int | float | None = None,
    pattern: str | None = None,
    max_length: int | None = None,
    auto_complete: str | None = None,
    auto_focus: bool = False,
    accept: str | None = None,
    multiple: bool = False,
    on_change: EventHandler | None = None,
    on_input: InputEventHandler | None = None,
    on_focus: FocusEventHandler | None = None,
    on_blur: FocusEventHandler | None = None,
    on_key_down: KeyboardEventHandler | None = None,
    on_key_up: KeyboardEventHandler | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """An input element."""
    ...


@html_element("textarea")
def Textarea(
    *,
    value: str | None = None,
    placeholder: str | None = None,
    rows: int | None = None,
    cols: int | None = None,
    disabled: bool = False,
    read_only: bool = False,
    name: str | None = None,
    required: bool = False,
    max_length: int | None = None,
    auto_focus: bool = False,
    on_change: EventHandler | None = None,
    on_input: InputEventHandler | None = None,
    on_focus: FocusEventHandler | None = None,
    on_blur: FocusEventHandler | None = None,
    on_key_down: KeyboardEventHandler | None = None,
    on_key_up: KeyboardEventHandler | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A textarea element."""
    ...


@html_element("select", is_container=True)
def Select(
    *,
    value: str | None = None,
    disabled: bool = False,
    name: str | None = None,
    required: bool = False,
    multiple: bool = False,
    on_change: EventHandler | None = None,
    on_key_down: KeyboardEventHandler | None = None,
    on_key_up: KeyboardEventHandler | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A select dropdown element."""
    ...


@overload
def HtmlButton(
    inner_text: str,
    /,
    *,
    type: str = "button",
    disabled: bool = False,
    name: str | None = None,
    value: str | None = None,
    on_click: MouseEventHandler | None = None,
    on_key_down: KeyboardEventHandler | None = None,
    on_key_up: KeyboardEventHandler | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def HtmlButton(
    *,
    type: str = "button",
    disabled: bool = False,
    name: str | None = None,
    value: str | None = None,
    on_click: MouseEventHandler | None = None,
    on_key_down: KeyboardEventHandler | None = None,
    on_key_up: KeyboardEventHandler | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> HtmlContainerElement: ...


@html_element("button", is_container=True)
def HtmlButton(
    inner_text: str | None = None,
    /,
    *,
    type: str = "button",
    disabled: bool = False,
    name: str | None = None,
    value: str | None = None,
    on_click: MouseEventHandler | None = None,
    on_key_down: KeyboardEventHandler | None = None,
    on_key_up: KeyboardEventHandler | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A native HTML button element.

    Note: Named HtmlButton to avoid conflict with trellis.widgets.Button.

    Can be used as text-only or as a container:
        h.HtmlButton("Click me", on_click=handler)  # Text only
        with h.HtmlButton(on_click=handler):        # Container
            h.Span("Icon")
            h.Span("Text")
    """
    ...


@html_element("option")
def Option(
    inner_text: str | None = None,
    /,
    *,
    value: str | None = None,
    disabled: bool = False,
    selected: bool = False,
    **props: tp.Any,
) -> Element:
    """An option element for use within Select."""
    ...


@overload
def HtmlLabel(
    inner_text: str,
    /,
    *,
    html_for: str | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def HtmlLabel(
    *,
    html_for: str | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    **props: tp.Any,
) -> HtmlContainerElement: ...


@html_element("label", is_container=True)
def HtmlLabel(
    inner_text: str | None = None,
    /,
    *,
    html_for: str | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    **props: tp.Any,
) -> Element:
    """A label element.

    Note: Named HtmlLabel to avoid conflict with trellis.widgets.Label.

    Can be used as text-only or as a container:
        h.HtmlLabel("Name:", html_for="name-input")  # Text only
        with h.HtmlLabel(html_for="name-input"):     # Container
            h.Span("Name")
            h.Input(id="name-input")
    """
    ...


# New form elements


@html_element("fieldset", is_container=True)
def Fieldset(
    *,
    disabled: bool = False,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A fieldset element for grouping form controls."""
    ...


@overload
def Legend(
    inner_text: str,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Legend(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> HtmlContainerElement: ...


@html_element("legend", is_container=True)
def Legend(
    inner_text: str | None = None,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A legend element for labeling a fieldset."""
    ...


@html_element("optgroup", is_container=True)
def Optgroup(
    *,
    label: str | None = None,
    disabled: bool = False,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """An option group element for organizing select options."""
    ...


@html_element("progress")
def Progress(
    *,
    value: float | None = None,
    max: float | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A progress indicator element."""
    ...


@html_element("meter")
def Meter(
    *,
    value: float | None = None,
    min: float | None = None,
    max: float | None = None,
    low: float | None = None,
    high: float | None = None,
    optimum: float | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A scalar measurement element."""
    ...


@overload
def Output(
    inner_text: str,
    /,
    *,
    html_for: str | None = None,
    name: str | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Output(
    *,
    html_for: str | None = None,
    name: str | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> HtmlContainerElement: ...


@html_element("output", is_container=True)
def Output(
    inner_text: str | None = None,
    /,
    *,
    html_for: str | None = None,
    name: str | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """An output element for calculation results."""
    ...


@html_element("datalist", is_container=True)
def Datalist(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A datalist element for providing autocomplete suggestions."""
    ...
