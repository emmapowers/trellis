from __future__ import annotations

import typing as tp
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass

from trellis.core.rendering import Element, Elements, get_active_render_context

T = tp.TypeVar("T", bound=Element, default=Element)


@dataclass(kw_only=True)
class Component(ABC, tp.Generic[T]):
    name: str
    elementType: type[Element] = Element

    def __call__(self, /, **props: tp.Any) -> T:
        return self.render(**props)

    def render(self, /, **props: tp.Any) -> T:
        context = get_active_render_context()
        if context is None or not context.rendering:
            raise RuntimeError("Components must be rendered within a RenderContext")

        key = ""
        if "key" in props:
            key = str(props.pop("key"))
        new_element = self.elementType(
            component=self,
            key=key,
            properties=props,
            children=[],
            dirty=True,
            render_context=context,
            parent=context.current_element,
            depth=context.current_element.depth + 1 if context.current_element else 0,
        )
        context.element_stack.append(new_element)
        try:
            result = self._render_imp(new_element, **props)
            children = normalize_elements(result)
            fixup_children(new_element, children)
            new_element.children = children
        finally:
            context.element_stack.pop()

            # special case for block elements, they need to know which elements were created in the block
            if (current_block := context.current_block) is not None:
                current_block.pending_elements.append(new_element)

        return new_element

    @abstractmethod
    def _render_imp(self, /, element: T, **props: tp.Any) -> T:
        pass


def normalize_elements(elements: Elements) -> list[Element]:
    result: list[Element]
    if elements is None:
        result = []
    elif isinstance(elements, list):
        result = elements
    elif isinstance(elements, tuple) or isinstance(elements, Iterable):
        result = list(elements)
    else:
        result = [elements]

    return result


def fixup_children(parent: Element, children: list[Element]) -> None:
    for child in children:
        child.parent = parent
        child.depth = parent.depth + 1
