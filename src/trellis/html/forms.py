"""Form HTML elements.

Elements for user input and form handling.
"""

from __future__ import annotations

import typing as tp

from trellis.core.rendering.element import Element
from trellis.html.base import Style, html_element
from trellis.html.events import (
    ChangeHandler,
    FocusHandler,
    FormHandler,
    MouseHandler,
)

__all__ = [
    "Form",
    "HtmlButton",
    "HtmlLabel",
    "Input",
    "Option",
    "Select",
    "Textarea",
]


@html_element("form", is_container=True)
def Form(
    *,
    action: str | None = None,
    method: str | None = None,
    onSubmit: FormHandler | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
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
    readOnly: bool = False,
    name: str | None = None,
    onChange: ChangeHandler | None = None,
    onFocus: FocusHandler | None = None,
    onBlur: FocusHandler | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> Element:
    """An input element.

    Args:
        type: Input type (text, password, email, number, checkbox, radio, etc.)
        value: Current value
        placeholder: Placeholder text
        disabled: Whether the input is disabled
        readOnly: Whether the input is read-only
        name: Form field name
        onChange: Called when the value changes
        onFocus: Called when the input gains focus
        onBlur: Called when the input loses focus
    """
    ...


@html_element("textarea")
def Textarea(
    *,
    value: str | None = None,
    placeholder: str | None = None,
    rows: int | None = None,
    cols: int | None = None,
    disabled: bool = False,
    readOnly: bool = False,
    name: str | None = None,
    onChange: ChangeHandler | None = None,
    onFocus: FocusHandler | None = None,
    onBlur: FocusHandler | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
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
    onChange: ChangeHandler | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> Element:
    """A select dropdown element."""
    ...


# Hybrid elements need special handling for text vs container mode
@html_element("button", is_container=True, name="HtmlButton")
def _HtmlButton(
    *,
    _text: str | None = None,
    type: str = "button",
    disabled: bool = False,
    onClick: MouseHandler | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> Element:
    """A native HTML button element."""
    ...


@html_element("option", name="Option")
def _Option(
    *,
    _text: str | None = None,
    value: str | None = None,
    disabled: bool = False,
    selected: bool = False,
    key: str | None = None,
    **props: tp.Any,
) -> Element:
    """An option element for use within Select."""
    ...


@html_element("label", is_container=True, name="HtmlLabel")
def _HtmlLabel(
    *,
    _text: str | None = None,
    htmlFor: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> Element:
    """A label element."""
    ...


# Public API for hybrid elements with positional text support
def HtmlButton(
    text: str = "",
    *,
    type: str = "button",
    disabled: bool = False,
    onClick: MouseHandler | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> Element:
    """A native HTML button element.

    Note: Named HtmlButton to avoid conflict with trellis.widgets.Button.

    Can be used as text-only or as a container:
        h.HtmlButton("Click me", onClick=handler)  # Text only
        with h.HtmlButton(onClick=handler):        # Container
            h.Span("Icon")
            h.Span("Text")
    """
    return _HtmlButton(
        _text=text if text else None,
        type=type,
        disabled=disabled,
        onClick=onClick,
        className=className,
        style=style,
        id=id,
        key=key,
        **props,
    )


def Option(
    text: str = "",
    *,
    value: str | None = None,
    disabled: bool = False,
    selected: bool = False,
    key: str | None = None,
    **props: tp.Any,
) -> Element:
    """An option element for use within Select."""
    return _Option(
        _text=text if text else None,
        value=value,
        disabled=disabled,
        selected=selected,
        key=key,
        **props,
    )


def HtmlLabel(
    text: str = "",
    *,
    htmlFor: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> Element:
    """A label element.

    Note: Named HtmlLabel to avoid conflict with trellis.widgets.Label.

    Can be used as text-only or as a container:
        h.HtmlLabel("Name:", htmlFor="name-input")  # Text only
        with h.HtmlLabel(htmlFor="name-input"):     # Container
            h.Span("Name")
            h.Input(id="name-input")
    """
    return _HtmlLabel(
        _text=text if text else None,
        htmlFor=htmlFor,
        className=className,
        style=style,
        key=key,
        **props,
    )
