"""Form HTML elements.

Elements for user input and form handling.
"""

from __future__ import annotations

import typing as tp

from trellis.core.rendering import ElementNode
from trellis.html.base import HtmlElement, Style, auto_collect_hybrid
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

# Singleton instances
_form = HtmlElement(_tag="form", name="Form", _is_container=True)
_input = HtmlElement(_tag="input", name="Input")  # Self-closing
_button = HtmlElement(_tag="button", name="HtmlButton", _is_container=True)  # Hybrid
_textarea = HtmlElement(_tag="textarea", name="Textarea")
_select = HtmlElement(_tag="select", name="Select", _is_container=True)
_option = HtmlElement(_tag="option", name="Option")  # Text only
_label = HtmlElement(_tag="label", name="HtmlLabel", _is_container=True)  # Hybrid


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
) -> ElementNode:
    """A form element."""
    return _form(
        action=action,
        method=method,
        onSubmit=onSubmit,
        className=className,
        style=style,
        id=id,
        key=key,
        **props,
    )


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
) -> ElementNode:
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
    return _input(
        type=type,
        value=value,
        placeholder=placeholder,
        disabled=disabled,
        readOnly=readOnly,
        name=name,
        onChange=onChange,
        onFocus=onFocus,
        onBlur=onBlur,
        className=className,
        style=style,
        id=id,
        key=key,
        **props,
    )


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
) -> ElementNode:
    """A native HTML button element.

    Note: Named HtmlButton to avoid conflict with trellis.widgets.Button.

    Can be used as text-only or as a container:
        h.HtmlButton("Click me", onClick=handler)  # Text only
        with h.HtmlButton(onClick=handler):        # Container
            h.Span("Icon")
            h.Span("Text")
    """
    desc = _button(
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
    if text:
        auto_collect_hybrid(desc)
    return desc


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
) -> ElementNode:
    """A textarea element."""
    return _textarea(
        value=value,
        placeholder=placeholder,
        rows=rows,
        cols=cols,
        disabled=disabled,
        readOnly=readOnly,
        name=name,
        onChange=onChange,
        onFocus=onFocus,
        onBlur=onBlur,
        className=className,
        style=style,
        id=id,
        key=key,
        **props,
    )


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
) -> ElementNode:
    """A select dropdown element."""
    return _select(
        value=value,
        disabled=disabled,
        name=name,
        onChange=onChange,
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
) -> ElementNode:
    """An option element for use within Select."""
    return _option(
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
) -> ElementNode:
    """A label element.

    Note: Named HtmlLabel to avoid conflict with trellis.widgets.Label.

    Can be used as text-only or as a container:
        h.HtmlLabel("Name:", htmlFor="name-input")  # Text only
        with h.HtmlLabel(htmlFor="name-input"):     # Container
            h.Span("Name")
            h.Input(id="name-input")
    """
    desc = _label(
        _text=text if text else None,
        htmlFor=htmlFor,
        className=className,
        style=style,
        key=key,
        **props,
    )
    if text:
        auto_collect_hybrid(desc)
    return desc
