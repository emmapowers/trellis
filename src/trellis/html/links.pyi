from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, overload

from trellis.core.rendering.element import Element
from trellis.html._generated_runtime import Img
from trellis.html._style_runtime import StyleInput
from trellis.html.base import HtmlContainerElement

__all__ = [
    "A",
    "Img",
]

type DataValue = str | int | float | bool | None

@overload
def A(
    inner_text: str,
    /,
    *,
    href: str | None = None,
    target: (
        Literal["_self"] | Literal["_blank"] | Literal["_parent"] | Literal["_top"] | str | None
    ) = None,
    rel: str | None = None,
    class_name: str | None = None,
    style: StyleInput | None = None,
    aria_label: str | None = None,
    on_click: Any = None,
    data: Mapping[str, DataValue] | None = None,
    use_router: bool = True,
    **extra_props: Any,
) -> Element: ...
@overload
def A(
    inner_text: None = None,
    /,
    *,
    href: str | None = None,
    target: (
        Literal["_self"] | Literal["_blank"] | Literal["_parent"] | Literal["_top"] | str | None
    ) = None,
    rel: str | None = None,
    class_name: str | None = None,
    style: StyleInput | None = None,
    aria_label: str | None = None,
    on_click: Any = None,
    data: Mapping[str, DataValue] | None = None,
    use_router: bool = True,
    **extra_props: Any,
) -> HtmlContainerElement: ...
