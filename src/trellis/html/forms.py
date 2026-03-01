"""Form HTML elements.

Elements for user input and form handling.
"""

from __future__ import annotations

import typing as tp
from typing import overload

from trellis.core.rendering.element import ContainerElement, Element
from trellis.html.base import Style, html_element
from trellis.html.events import (
    ChangeHandler,
    FocusHandler,
    FormHandler,
    InputHandler,
    KeyboardHandler,
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
    encType: str | None = None,
    noValidate: bool = False,
    autoComplete: str | None = None,
    onSubmit: FormHandler | None = None,
    onKeyDown: KeyboardHandler | None = None,
    onKeyUp: KeyboardHandler | None = None,
    className: str | None = None,
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
    readOnly: bool = False,
    name: str | None = None,
    checked: bool | None = None,
    required: bool = False,
    min: str | int | float | None = None,
    max: str | int | float | None = None,
    step: str | int | float | None = None,
    pattern: str | None = None,
    maxLength: int | None = None,
    autoComplete: str | None = None,
    autoFocus: bool = False,
    accept: str | None = None,
    multiple: bool = False,
    onChange: ChangeHandler | None = None,
    onInput: InputHandler | None = None,
    onFocus: FocusHandler | None = None,
    onBlur: FocusHandler | None = None,
    onKeyDown: KeyboardHandler | None = None,
    onKeyUp: KeyboardHandler | None = None,
    className: str | None = None,
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
    readOnly: bool = False,
    name: str | None = None,
    required: bool = False,
    maxLength: int | None = None,
    autoFocus: bool = False,
    onChange: ChangeHandler | None = None,
    onInput: InputHandler | None = None,
    onFocus: FocusHandler | None = None,
    onBlur: FocusHandler | None = None,
    onKeyDown: KeyboardHandler | None = None,
    onKeyUp: KeyboardHandler | None = None,
    className: str | None = None,
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
    onChange: ChangeHandler | None = None,
    onKeyDown: KeyboardHandler | None = None,
    onKeyUp: KeyboardHandler | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A select dropdown element."""
    ...


# Hybrid elements need special handling
@html_element("button", is_container=True, name="HtmlButton")
def _HtmlButton(
    *,
    _text: str | None = None,
    type: str = "button",
    disabled: bool = False,
    name: str | None = None,
    value: str | None = None,
    onClick: MouseHandler | None = None,
    onKeyDown: KeyboardHandler | None = None,
    onKeyUp: KeyboardHandler | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
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
    **props: tp.Any,
) -> Element:
    """A label element."""
    ...


# Public API for hybrid elements with positional text support
@overload
def HtmlButton(
    text: str,
    /,
    *,
    type: str = "button",
    disabled: bool = False,
    name: str | None = None,
    value: str | None = None,
    onClick: MouseHandler | None = None,
    onKeyDown: KeyboardHandler | None = None,
    onKeyUp: KeyboardHandler | None = None,
    className: str | None = None,
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
    onClick: MouseHandler | None = None,
    onKeyDown: KeyboardHandler | None = None,
    onKeyUp: KeyboardHandler | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


def HtmlButton(
    text: str = "",
    /,
    *,
    type: str = "button",
    disabled: bool = False,
    name: str | None = None,
    value: str | None = None,
    onClick: MouseHandler | None = None,
    onKeyDown: KeyboardHandler | None = None,
    onKeyUp: KeyboardHandler | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
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
        name=name,
        value=value,
        onClick=onClick,
        onKeyDown=onKeyDown,
        onKeyUp=onKeyUp,
        className=className,
        style=style,
        id=id,
        **props,
    )


def Option(
    text: str = "",
    /,
    *,
    value: str | None = None,
    disabled: bool = False,
    selected: bool = False,
    **props: tp.Any,
) -> Element:
    """An option element for use within Select."""
    return _Option(
        _text=text if text else None,
        value=value,
        disabled=disabled,
        selected=selected,
        **props,
    )


@overload
def HtmlLabel(
    text: str,
    /,
    *,
    htmlFor: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def HtmlLabel(
    *,
    htmlFor: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


def HtmlLabel(
    text: str = "",
    /,
    *,
    htmlFor: str | None = None,
    className: str | None = None,
    style: Style | None = None,
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
        **props,
    )
