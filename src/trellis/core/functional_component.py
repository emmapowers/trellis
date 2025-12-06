from __future__ import annotations

import typing as tp
from dataclasses import dataclass

from trellis.core.base_component import Component
from trellis.core.rendering import Element, Elements

T = tp.TypeVar("T", bound=Element, default=Element)


class RenderFunc(tp.Generic[T], tp.Protocol):
    def __call__(self, /, **props: tp.Any) -> T: ...


@dataclass(kw_only=True)
class FunctionalComponent(Component[T], tp.Generic[T]):
    render_func: RenderFunc[Element]

    def _render_imp(self, /, element: T, **props: tp.Any) -> Elements:
        return self.render_func(**props)

    def __hash__(self):
        # TODO: Find a less naive way to do this
        return id(self)


def component(render_func: RenderFunc) -> callable:
    return FunctionalComponent(
        name=render_func.__name__,
        render_func=render_func,
    )
