from __future__ import annotations

import typing as tp
from abc import ABC, abstractmethod
from dataclasses import dataclass

from trellis.core.rendering import Element, get_active_render_context

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

            # Components must return None - children are auto-collected
            if result is not None:
                raise TypeError(
                    f"Component '{self.name}' returned a value. "
                    f"Components must return None; children are auto-collected."
                )

            # Use auto-collected children from pending_elements
            children = new_element.pending_elements
            fixup_children(new_element, children)
            new_element.children = children
            new_element.pending_elements = []
        finally:
            context.element_stack.pop()

            # Auto-collect: add this element to parent's pending_elements
            if (current := context.current_element) is not None:
                current.pending_elements.append(new_element)

        return new_element

    @abstractmethod
    def _render_imp(self, /, element: T, **props: tp.Any) -> None:
        pass


def fixup_children(parent: Element, children: list[Element]) -> None:
    for child in children:
        child.parent = parent
        child.depth = parent.depth + 1
