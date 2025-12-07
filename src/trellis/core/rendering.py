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
    children: list[Element] = field(default_factory=list)
    dirty: bool = False
    render_context: RenderContext | None = None

    parent: Element | None = None
    depth: int = 0
    _mounted: bool = False

    # Local state storage (replaces RenderContext.local_state)
    _local_state: dict[tuple[type, int], tp.Any] = field(default_factory=dict)
    _state_call_count: int = 0

    # Child collection during rendering
    pending_elements: list[Element] = field(default_factory=list)
    _block_active: bool = False

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

    def __enter__(self) -> Element:
        """Enter context manager for collecting children."""
        import inspect

        # Validate that the component accepts a 'children' parameter
        render_func = getattr(self.component, "render_func", None)
        if render_func is not None:
            sig = inspect.signature(render_func)
            if "children" not in sig.parameters:
                raise TypeError(
                    f"Component '{self.component.name}' cannot be used with 'with' statement: "
                    f"it does not have a 'children' parameter"
                )

        if self._block_active:
            raise RuntimeError(f"Component '{self.component.name}' block is already active")

        self._block_active = True
        assert self.render_context is not None
        self.render_context.element_stack.append(self)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: tp.Any,
    ) -> None:
        """Exit context manager, pass collected children to component."""
        from trellis.core.base_component import fixup_children

        assert self.render_context is not None
        self._block_active = False

        if exc_type is not None:
            self.render_context.element_stack.pop()
            return

        # Pass collected children to the component's render function
        if "children" in self.properties:
            self.render_context.element_stack.pop()
            raise RuntimeError(
                f"Cannot provide 'children' as a property and use 'with' block. "
                f"Component: {self.component.name}"
            )

        # Store collected children and clear pending before render
        collected_children = self.pending_elements
        self.pending_elements = []
        self.properties["children"] = collected_children

        # Render with children - element stays on stack so child() works
        render_func = getattr(self.component, "render_func", None)
        if render_func is not None:
            render_func(**self.properties)

        # Now pop from stack
        self.render_context.element_stack.pop()

        # Finalize: use pending_elements populated by child() calls
        self.children = self.pending_elements
        fixup_children(self, self.children)
        self.pending_elements = []

    def __call__(self) -> None:
        """Mount this element at the current render position."""
        assert self.render_context is not None
        current = self.render_context.current_element
        if current is not None:
            current.pending_elements.append(self)

    def __rich_repr__(self):
        if self.key:
            yield self.component.name + f" (d={self.depth}, key={self.key})"
        else:
            yield self.component.name + f" (d={self.depth})"
        yield "properties", self.properties
        yield "children", self.children


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
