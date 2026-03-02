"""Base classes and helpers for HTML elements.

This module provides the HtmlElement class that powers all native HTML
element wrappers, plus the @html_element decorator for defining elements.
"""

from __future__ import annotations

import functools
import inspect
import typing as tp
from collections.abc import Callable
from typing import Literal, ParamSpec, TypeVar, overload

from trellis.core.components.base import Component, ElementKind
from trellis.core.rendering.element import ContainerElement, Element
from trellis.core.rendering.traits import ContainerTrait

__all__ = [
    "HtmlContainerTrait",
    "HtmlElement",
    "Style",
    "html_element",
]

# Type alias for inline styles
Style = dict[str, str | int | float]

# ParamSpec for preserving function signatures through the decorator
P = ParamSpec("P")
E = TypeVar("E", bound=Element)


class HtmlContainerTrait(ContainerTrait):
    """ContainerTrait with HTML-specific hybrid text/container check.

    HTML elements can be used in text mode (e.g. ``P("hello")``) or container
    mode (e.g. ``with P(): ...``). The two modes are mutually exclusive —
    entering a ``with`` block when ``_text`` is set raises TypeError.
    """

    def __enter__(self) -> tp.Self:
        if "_text" in self.props:
            raise TypeError(
                f"Cannot use 'with {self.component.name}(...)' with text content. "
                f'Use either text mode ({self.component.name}("text")) or '
                f"container mode (with {self.component.name}(): ...)."
            )
        return super().__enter__()


# Default element class for HTML container elements.
# Uses HtmlContainerTrait (not plain ContainerTrait) so that the hybrid
# text/container check is enforced for all HTML elements.
HtmlContainerElement = type("HtmlContainerElement", (HtmlContainerTrait, Element), {})


class HtmlElement(Component):
    """Base class for native HTML elements like div, span, button, etc.

    HtmlElement provides type-safe wrappers around standard HTML tags. Elements
    are rendered directly as native DOM elements on the client (not as React
    components), enabling full HTML/CSS capabilities with Python type hints.

    Use the `@html_element` decorator to define elements rather than
    subclassing directly. See `trellis.html` for pre-defined elements.

    Example:
        ```python
        from trellis import html as h

        # Leaf element
        h.Button("Click me", onClick=handler)

        # Container element
        with h.Div(className="card", style={"padding": "20px"}):
            h.H1("Title")
            h.P("Content")
        ```
    """

    # Subclasses must set this
    _tag: tp.ClassVar[str] = ""

    # Whether this component accepts children via `with` block (class var)
    _is_container: tp.ClassVar[bool] = False

    @property
    def is_container(self) -> bool:
        """Whether this element accepts children via with block."""
        return self.__class__._is_container

    @property
    def element_kind(self) -> ElementKind:
        """HTML elements are JSX intrinsic elements."""
        return ElementKind.JSX_ELEMENT

    @property
    def element_name(self) -> str:
        """Return the HTML tag name for native DOM rendering."""
        if not self.__class__._tag:
            raise NotImplementedError(f"{self.__class__.__name__} must set _tag class attribute")
        return self.__class__._tag

    def execute(self, /, **props: tp.Any) -> None:
        """Render this element.

        For leaf elements (no children), this is a no-op.
        For container elements, this mounts the children.

        Args:
            **props: Properties including `children` for containers
        """
        # If this is a container, mount the children
        children = props.get("children")
        if children:
            for child in children:
                child()


@overload
def html_element(
    tag: str,
    *,
    is_container: Literal[True],
    name: str | None = None,
    element_class: Literal[None] = None,
) -> Callable[[Callable[P, tp.Any]], Callable[P, ContainerElement]]: ...


@overload
def html_element(
    tag: str,
    *,
    is_container: Literal[False] = ...,
    name: str | None = None,
    element_class: Literal[None] = None,
) -> Callable[[Callable[P, tp.Any]], Callable[P, Element]]: ...


@overload
def html_element(
    tag: str,
    *,
    is_container: bool = ...,
    name: str | None = None,
    element_class: type[E],
) -> Callable[[Callable[P, tp.Any]], Callable[P, E]]: ...


def html_element(
    tag: str,
    *,
    is_container: bool = False,
    name: str | None = None,
    element_class: type[E] | None = None,
) -> Callable[[Callable[P, tp.Any]], Callable[P, Element | E]]:
    """Decorator to create an HtmlElement from a function signature.

    This is the standard way to define HTML elements. The function body is
    ignored; only the signature is used for documentation and type hints.
    Internally, a singleton HtmlElement instance is created.

    Args:
        tag: The HTML tag name (e.g., "div", "span", "button")
        is_container: Whether this element accepts children via `with` block.
            When True, the element supports `with` blocks via HtmlContainerTrait.
            When False (default), returns a plain Element.
        name: Optional name override (defaults to function name). Useful for
            internal functions prefixed with underscore.
        element_class: Optional Element subclass to use for elements created by
            this element. When is_container=True, the class must include
            HtmlContainerTrait in its MRO.

    Returns:
        A decorator that creates a callable returning Elements
    """
    if element_class is not None:
        resolved_element_class = element_class
        if is_container and HtmlContainerTrait not in element_class.__mro__:
            raise TypeError(
                "@html_element(is_container=True, element_class=...) requires "
                f"element_class to include HtmlContainerTrait in its MRO. "
                f"Got {element_class.__name__}. "
                "Define a class like "
                f"'class {element_class.__name__}Container(HtmlContainerTrait, "
                f"{element_class.__name__}): ...'."
            )
    else:
        resolved_element_class = HtmlContainerElement if is_container else Element

    def decorator(
        func: Callable[P, tp.Any],
    ) -> Callable[P, Element | E]:
        # Use provided name or function name
        element_name = name or func.__name__
        signature = inspect.signature(func)
        var_keyword_param = next(
            (
                param.name
                for param in signature.parameters.values()
                if param.kind == inspect.Parameter.VAR_KEYWORD
            ),
            None,
        )
        has_text_keyword = "_text" in signature.parameters
        has_text_positional = "text" in signature.parameters

        # Create a generated class with the element name
        class _Generated(HtmlElement):
            _tag = tag
            _is_container = is_container

        # Create singleton instance with explicit name and element_class
        _singleton = _Generated(element_name, element_class=resolved_element_class)

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Element | E:
            if len(args) > 1:
                raise TypeError(
                    f"{element_name}() accepts at most one positional argument for text content."
                )
            if args and "_text" in kwargs:
                raise TypeError(
                    f"{element_name}() received both positional text and '_text' keyword argument."
                )

            validation_args: tuple[tp.Any, ...] = args
            validation_kwargs = dict(kwargs)
            if args and has_text_keyword:
                validation_args = ()
                validation_kwargs["_text"] = args[0]

            bound = signature.bind_partial(*validation_args, **validation_kwargs)
            if has_text_keyword or has_text_positional:
                # Preserve previous hybrid-wrapper behavior where default props
                # were forwarded (e.g. HtmlButton(type="button")).
                bound.apply_defaults()
            props = dict(bound.arguments)
            if var_keyword_param and var_keyword_param in props:
                var_kwargs = props.pop(var_keyword_param)
                props.update(var_kwargs)

            if "text" in props:
                text_value = props.pop("text")
                if text_value is not None:
                    props["_text"] = text_value

            if "_text" in props and props["_text"] is None:
                del props["_text"]

            return _singleton._place(**props)

        # Expose the underlying component for introspection
        wrapper._component = _singleton  # type: ignore[attr-defined]

        return wrapper

    return decorator
