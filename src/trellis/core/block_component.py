from __future__ import annotations

from dataclasses import dataclass, field

from trellis.core.base_component import fixup_children, normalize_elements
from trellis.core.functional_component import FunctionalComponent, RenderFunc
from trellis.core.rendering import Element, Elements


@dataclass(kw_only=True)
class BlockElement(Element):
    active: bool = False
    complete: bool = False
    render_func: RenderFunc | None = None
    pending_elements: list[Element] = field(default_factory=list)

    def __enter__(self) -> BlockElement:
        if self.complete:
            raise RuntimeError(f"You can only use a {self.component.name} component block once!")
        self.active = True
        self.render_context.element_stack.append(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.active = False
        self.complete = True
        self.render_context.element_stack.pop()

        if exc_type is not None:
            return

        assert (
            self.render_func is not None
        ), "No active render function when finishing a component block!"

        if "children" in self.properties:
            raise RuntimeError(
                f"You cannot provide children as a property and use the component in a with block."
                f"Component: {self.component.name}"
            )

        self.properties["children"] = self.pending_elements
        result = self.render_func(**self.properties)
        self.children = normalize_elements(result)
        fixup_children(self, self.children)
        self.render_func = None
        self.pending_elements = []

    def __hash__(self):
        # TODO: Find a less naive way to do this
        return id(self)


@dataclass(kw_only=True)
class BlockComponent(FunctionalComponent[BlockElement]):
    elementType: type[Element] = BlockElement

    def _render_imp(self, /, element: BlockElement, **props) -> Elements:
        # Defer the rendering until the end of the block
        element.render_func = self.render_func
        return None


def blockComponent(render_func: RenderFunc) -> callable:
    return BlockComponent(
        name=render_func.__name__,
        render_func=render_func,
    )
