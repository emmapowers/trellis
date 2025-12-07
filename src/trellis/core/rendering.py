from __future__ import annotations

import threading
import typing as tp
from dataclasses import dataclass, field, fields

from trellis.util.lock_helper import with_lock

type Elements = None | "Element" | tp.Iterable["Element"] | tuple["Element", ...]

g_active_render_context: RenderContext | None = None


def get_active_render_context() -> RenderContext | None:
    return g_active_render_context


def set_active_render_context(ctx: RenderContext | None) -> None:
    global g_active_render_context
    g_active_render_context = ctx


class IComponent(tp.Protocol):
    name: str

    def __call__(self, /, **props: tp.Any) -> Element: ...


@dataclass(kw_only=True)
class Element:
    component: IComponent
    key: str = ""
    properties: dict[str, tp.Any] = field(default_factory=dict)
    children: list[IComponent] = field(default_factory=list)
    dirty: bool = False
    render_context: RenderContext | None = None

    parent: Element | None = None
    depth: int = 0
    _mounted: bool = False

    # Local state storage (replaces RenderContext.local_state)
    _local_state: dict[tuple[type, int], tp.Any] = field(default_factory=dict)
    _state_call_count: int = 0

    def __hash__(self) -> int:
        # TODO: Find a less naive way to do this
        return id(self)

    def replace(self, other: Element) -> None:
        assert type(self) is type(
            other
        ), "Can only replace an element with another of the same type!"
        for f in fields(self):
            setattr(self, f.name, getattr(other, f.name))

    def on_mount(self) -> None:
        """Called when element is added to tree. Override in subclasses."""
        pass

    def on_unmount(self) -> None:
        """Called when element is removed from tree. Override in subclasses."""
        pass

    def __rich_repr__(self):
        if self.key:
            yield self.component.name + f" (d={self.depth}, key={self.key})"
        else:
            yield self.component.name + f" (d={self.depth})"
        yield "properties", self.properties
        yield "children", self.children


class IActiveBlock(tp.Protocol):
    pending_elements = list[Element]


@dataclass(kw_only=True)
class LeafElement(Element):
    pass


class RenderContext:
    root_component: IComponent
    root_element: Element | None
    dirty_elements: set[Element]
    lock: threading.RLock

    # Render state
    rendering: bool
    element_stack: list[Element]
    block_stack: list[IActiveBlock]
    _rerender_target: Element | None  # Old element being re-rendered (has existing state)

    def __init__(self, root: IComponent) -> None:
        self.root_component = root
        self.root_element = None
        self.dirty_elements = set()
        self.lock = threading.RLock()
        self.rendering = False
        self.element_stack = []
        self._rerender_target = None

    @with_lock
    def render(self, from_element: Element | None) -> None:
        from trellis.core.reconcile import mount_tree, reconcile_element

        if (
            get_active_render_context()
        ):  #  Todo: this really should throw when we set, otherwise it's a race
            raise RuntimeError("Attempted to start rending with another context active!")

        try:
            self.rendering = True
            self.element_stack = []
            set_active_render_context(self)

            if from_element is None:
                # First render
                new_element = self.root_component()
                if self.root_element is None:
                    self.root_element = new_element
                    mount_tree(new_element, self)
                else:
                    self.root_element.replace(new_element)
            else:
                # Re-render: set target so Stateful.__new__ uses old element's state
                self._rerender_target = from_element
                from_element._state_call_count = 0  # Reset for consistent hook ordering
                if from_element.parent is not None:
                    self.element_stack.append(from_element.parent)
                new_element = from_element.component(**from_element.properties)
                reconcile_element(from_element, new_element, self)

        finally:
            self.rendering = False
            self.element_stack = []
            self._rerender_target = None
            set_active_render_context(None)

    @with_lock
    def render_dirty(self) -> None:
        elements = list(self.dirty_elements)
        # sort elements by depth, shallowest first
        elements.sort(key=lambda e: e.depth)

        for element in elements:
            if element.dirty:  # The element may have already been rendered as part of a parent
                self.render(from_element=element)
                element.dirty = False
        self.dirty_elements.clear()

    @with_lock
    def mark_dirty(self, element: Element) -> None:
        self.dirty_elements.add(element)
        element.dirty = True

    @property
    @with_lock
    def current_element(self) -> Element | None:
        if not self.element_stack:
            return None
        return self.element_stack[-1]

    @property
    @with_lock
    def current_block(self) -> IActiveBlock | None:
        if self.current_element and hasattr(self.current_element, "pending_elements"):
            return self.current_element

        return None
