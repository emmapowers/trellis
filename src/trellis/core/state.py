import typing as tp
from dataclasses import dataclass, field

from trellis.core.block_component import BlockElement
from trellis.core.rendering import Element, RenderContext, get_active_render_context


@dataclass(kw_only=True)
class StatePropertyInfo:
    """Tracks which elements depend on a state property."""

    name: str
    elements: set[tuple[RenderContext, Element]] = field(default_factory=set)


class Stateful:
    """Base class for reactive state objects.

    Subclasses can use @dataclass or plain classes - your choice:

        @dataclass
        class MyState(Stateful):
            count: int = 0

        # or

        class MyState(Stateful):
            def __init__(self):
                self.count = 0

    State instances are cached per-component during render (like React hooks).
    Accessing state during render registers dependencies for fine-grained updates.
    """

    _state_deps: dict[str, StatePropertyInfo]
    _initialized: bool
    _owner_element: Element | None

    def __init_subclass__(cls, **kwargs: tp.Any) -> None:
        super().__init_subclass__(**kwargs)
        # Wrap __init__ to skip re-initialization on cached instances
        original_init = cls.__init__

        def wrapped_init(self: Stateful, *args: tp.Any, **kw: tp.Any) -> None:
            if getattr(self, "_initialized", False):
                return  # Skip - already initialized (cached instance)
            original_init(self, *args, **kw)
            object.__setattr__(self, "_initialized", True)

        cls.__init__ = wrapped_init  # type: ignore[assignment,method-assign]

    def __new__(cls, *args: tp.Any, **kwargs: tp.Any) -> "Stateful":
        """Cache instances per-element during render (like React hooks)."""
        ctx = get_active_render_context()

        # Outside render context - create normally
        if ctx is None or not ctx.rendering:
            return object.__new__(cls)

        current = ctx.current_element
        rerender_target = ctx._rerender_target

        # Determine which element to use for state storage:
        # - If we're re-rendering and the current element is the one being re-rendered
        #   (same parent as rerender_target), use the OLD element (rerender_target)
        # - Otherwise use current_element (for children during re-render, or first render)
        element: Element | None = None
        if rerender_target is not None and current is not None:
            # Check if this is the element being re-rendered (not a child)
            if current.parent == rerender_target.parent:
                element = rerender_target
            else:
                element = current
        elif current is not None:
            element = current
        elif rerender_target is not None:
            element = rerender_target

        if element is None:
            return object.__new__(cls)

        # Simple key: just (class, call_index) - element is implicit via storage location
        call_idx = element._state_call_count
        element._state_call_count += 1
        key = (cls, call_idx)

        if key in element._local_state:
            return element._local_state[key]  # Return cached instance

        # Create new instance and cache it on the element
        instance = object.__new__(cls)
        object.__setattr__(instance, "_owner_element", element)
        element._local_state[key] = instance
        return instance

    def __getattribute__(self, name: str) -> tp.Any:
        value = object.__getattribute__(self, name)

        # Skip internal attributes
        if name.startswith("_"):
            return value

        # Register dependency during render
        context = get_active_render_context()
        if context is not None and context.rendering:
            current_element = context.current_element
            if current_element is not None:
                # Lazy init _state_deps (needed when @dataclass doesn't call super().__init__)
                try:
                    deps = object.__getattribute__(self, "_state_deps")
                except AttributeError:
                    deps = {}
                    object.__setattr__(self, "_state_deps", deps)

                if name not in deps:
                    deps[name] = StatePropertyInfo(name=name)
                state_info = deps[name]

                if isinstance(current_element, BlockElement):
                    state_info.elements.add((context, current_element.parent))
                else:
                    state_info.elements.add((context, current_element))

        return value

    def __setattr__(self, name: str, value: tp.Any) -> None:
        # Always set the value first
        object.__setattr__(self, name, value)

        # Skip internal attributes
        if name.startswith("_"):
            return

        # Mark dependent elements as dirty (if we have deps tracking initialized)
        try:
            deps = object.__getattribute__(self, "_state_deps")
        except AttributeError:
            return  # Not initialized yet

        if name in deps:
            state_info = deps[name]
            for context, element in state_info.elements:
                context.mark_dirty(element)

    def on_mount(self) -> None:
        """Called after owning element mounts. Override for initialization."""
        pass

    def on_unmount(self) -> None:
        """Called before owning element unmounts. Override for cleanup."""
        pass

    @property
    def owner_element(self) -> Element | None:
        """The element that owns this state instance."""
        try:
            return object.__getattribute__(self, "_owner_element")
        except AttributeError:
            return None
