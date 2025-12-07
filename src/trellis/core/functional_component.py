from __future__ import annotations

import inspect
import typing as tp
from dataclasses import dataclass, field

from trellis.core.base_component import Component
from trellis.core.rendering import Element

T = tp.TypeVar("T", bound=Element, default=Element)


class RenderFunc(tp.Protocol):
    def __call__(self, /, **props: tp.Any) -> None: ...


@dataclass(kw_only=True)
class FunctionalComponent(Component[T], tp.Generic[T]):
    render_func: RenderFunc
    _has_children_param: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        sig = inspect.signature(self.render_func)
        self._has_children_param = "children" in sig.parameters

    def _render_imp(self, /, element: T, **props: tp.Any) -> None:
        # If component has 'children' param, defer rendering until __exit__
        # (children will be collected during the 'with' block)
        if self._has_children_param:
            return
        self.render_func(**props)

    def __hash__(self):
        # TODO: Find a less naive way to do this
        return id(self)


def component(render_func: RenderFunc) -> FunctionalComponent[Element]:
    return FunctionalComponent(
        name=render_func.__name__,
        render_func=render_func,
    )
