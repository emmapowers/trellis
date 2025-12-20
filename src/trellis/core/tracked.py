"""Reactive tracked collections for fine-grained dependency tracking.

TrackedList, TrackedDict, and TrackedSet wrap Python's built-in collections
to provide reactive updates. When accessed during render, they register
dependencies by item identity (list/set) or key (dict). Mutations trigger
re-renders only for components that depend on the affected items.

Special tracking:
- ITER_KEY: Registered when iterating or checking length
- Mutations that change length/structure mark ITER_KEY dirty

Auto-conversion:
- Stateful.__setattr__ recursively converts collections on assignment
- Plain list/dict/set values become TrackedList/Dict/Set automatically

Example:
    @dataclass
    class TodosState(Stateful):
        todos: list[Todo] = field(default_factory=list)

    @component
    def TodoItem(index: int) -> None:
        state = TodosState.from_context()
        todo = state.todos[index]  # Registers dependency on this item
        Label(text=todo.text)

    # Modifying state.todos[5] only re-renders components that accessed that item
"""

from __future__ import annotations

import typing as tp
import weakref
from collections.abc import Iterable, Iterator
from typing import SupportsIndex

if tp.TYPE_CHECKING:
    from trellis.core.rendering import RenderTree
    from trellis.core.state import Stateful

from trellis.core.rendering import get_active_render_tree

T = tp.TypeVar("T")
KT = tp.TypeVar("KT")
VT = tp.TypeVar("VT")

__all__ = ["ITER_KEY", "TrackedDict", "TrackedList", "TrackedSet"]

# Special key for iteration/length tracking
ITER_KEY = "__iter__"


class _TrackedMixin:
    """Mixin providing common tracking infrastructure for collections.

    Attributes:
        _owner: Weak reference to the owning Stateful instance
        _attr: The attribute name on the owner this collection is stored in
        _deps: Dict mapping dep_key -> {node_id -> weakref(RenderTree)}
    """

    _owner: weakref.ref[Stateful] | None
    _attr: str
    _deps: dict[tp.Any, dict[str, weakref.ref[RenderTree]]]

    def _init_tracking(
        self,
        owner: Stateful | None = None,
        attr: str = "",
    ) -> None:
        """Initialize tracking state.

        Args:
            owner: The Stateful instance that owns this collection (optional)
            attr: The attribute name on owner where this is stored
        """
        object.__setattr__(self, "_owner", weakref.ref(owner) if owner else None)
        object.__setattr__(self, "_attr", attr)
        object.__setattr__(self, "_deps", {})

    def _bind(self, owner: Stateful, attr: str) -> None:
        """Bind this collection to an owner Stateful and attribute.

        Called by Stateful.__setattr__ when assigning a collection.
        """
        object.__setattr__(self, "_owner", weakref.ref(owner))
        object.__setattr__(self, "_attr", attr)

    def _check_no_render_mutation(self) -> None:
        """Raise if trying to mutate during render."""
        ctx = get_active_render_tree()
        if ctx is not None and ctx._current_node_id is not None:
            attr = object.__getattribute__(self, "_attr")
            raise RuntimeError(
                f"Cannot modify tracked collection '{attr}' during render. "
                f"Mutations must happen outside of component execution "
                f"(e.g., in callbacks, mount/unmount hooks, or timers)."
            )

    def _register_access(self, dep_key: tp.Any) -> None:
        """Register that current render context accessed this dependency key.

        Called during __getitem__, __iter__, etc. to track which nodes
        depend on which parts of the collection.
        """
        ctx = get_active_render_tree()
        if ctx is None or ctx._current_node_id is None:
            return

        node_id = ctx._current_node_id
        deps = object.__getattribute__(self, "_deps")

        if dep_key not in deps:
            deps[dep_key] = {}
        deps[dep_key][node_id] = weakref.ref(ctx)

        # Also register in ElementState.watched_deps for cleanup
        # Use a composite key: (id(self), dep_key)
        element_state = ctx.get_element_state(node_id)
        tracked_id = id(self)
        composite_key = (tracked_id, dep_key)

        if tracked_id in element_state.watched_deps:
            # Existing entry - add to dep_keys set
            existing = element_state.watched_deps[tracked_id]
            existing[1].add(composite_key)
        else:
            # New entry - store (self, {composite_keys})
            element_state.watched_deps[tracked_id] = (self, {composite_key})

    def _mark_dirty(self, dep_key: tp.Any) -> None:
        """Mark all nodes that depend on this key as dirty.

        Called when the collection is mutated at this key.
        """
        deps = object.__getattribute__(self, "_deps")
        if dep_key not in deps:
            return

        stale_nodes: list[str] = []
        for node_id, tree_ref in deps[dep_key].items():
            tree = tree_ref()
            if tree is not None:
                tree.mark_dirty_id(node_id)
            else:
                stale_nodes.append(node_id)

        # Clean up stale references
        for node_id in stale_nodes:
            deps[dep_key].pop(node_id, None)

        # Remove empty dep_key entries
        if not deps.get(dep_key):
            deps.pop(dep_key, None)

    def _mark_iter_dirty(self) -> None:
        """Mark nodes that depend on iteration/length as dirty."""
        self._mark_dirty(ITER_KEY)

    def _clear_dep(self, node_id: str, dep_key: tp.Any) -> None:
        """Clear a specific dependency for a node.

        Called by clear_node_dependencies during cleanup.
        """
        deps = object.__getattribute__(self, "_deps")
        if dep_key in deps:
            deps[dep_key].pop(node_id, None)
            if not deps[dep_key]:
                del deps[dep_key]


class TrackedList(list[T], _TrackedMixin):
    """A reactive list that tracks access by item identity.

    Access tracking:
    - `lst[i]` registers dependency on id(item) at position i
    - `for x in lst` / `len(lst)` registers dependency on ITER_KEY
    - `item in lst` registers ITER_KEY (must iterate to check)

    Mutation effects:
    - `lst[i] = new` marks id(old_item) and id(new_item) dirty
    - `lst.append(x)` marks ITER_KEY dirty (length changed)
    - `lst.remove(x)` marks id(x) and ITER_KEY dirty
    - `lst.sort()` marks ITER_KEY dirty (order changed)

    Nested auto-conversion:
    - When accessing `lst[i]` where `lst[i]` is a plain list/dict/set,
      it is auto-converted to a Tracked version with the same owner.
    """

    def __new__(
        cls,
        iterable: Iterable[T] = (),
        *,
        owner: Stateful | None = None,
        attr: str = "",
    ) -> TrackedList[T]:
        return super().__new__(cls)

    def __init__(
        self,
        iterable: Iterable[T] = (),
        *,
        owner: Stateful | None = None,
        attr: str = "",
    ) -> None:
        super().__init__(iterable)
        self._init_tracking(owner, attr)

    @tp.overload
    def __getitem__(self, index: SupportsIndex) -> T: ...

    @tp.overload
    def __getitem__(self, index: slice) -> list[T]: ...

    def __getitem__(self, index: SupportsIndex | slice) -> T | list[T]:
        if isinstance(index, slice):
            # Slice access - register ITER_KEY (iterating over range)
            self._register_access(ITER_KEY)
            return list(super().__getitem__(index))

        value = super().__getitem__(index)
        self._register_access(id(value))
        return value

    @tp.overload
    def __setitem__(self, index: SupportsIndex, value: T) -> None: ...

    @tp.overload
    def __setitem__(self, index: slice, value: Iterable[T]) -> None: ...

    def __setitem__(self, index: SupportsIndex | slice, value: T | Iterable[T]) -> None:
        self._check_no_render_mutation()

        if isinstance(index, slice):
            # Slice assignment - complex case, mark ITER_KEY
            old_items = list.__getitem__(self, index)
            for item in old_items:
                self._mark_dirty(id(item))
            list.__setitem__(self, index, value)  # type: ignore[assignment]
            self._mark_iter_dirty()
            return

        # Single item assignment
        old_value = list.__getitem__(self, index)
        self._mark_dirty(id(old_value))
        list.__setitem__(self, index, value)  # type: ignore[misc]
        self._mark_dirty(id(value))

    def __delitem__(self, index: SupportsIndex | slice) -> None:
        self._check_no_render_mutation()

        if isinstance(index, slice):
            old_items = list.__getitem__(self, index)
            for item in old_items:
                self._mark_dirty(id(item))
        else:
            old_value = list.__getitem__(self, index)
            self._mark_dirty(id(old_value))

        list.__delitem__(self, index)
        self._mark_iter_dirty()

    def __iter__(self) -> Iterator[T]:
        self._register_access(ITER_KEY)
        return list.__iter__(self)

    def __len__(self) -> int:
        self._register_access(ITER_KEY)
        return list.__len__(self)

    def __contains__(self, item: object) -> bool:
        self._register_access(ITER_KEY)
        return list.__contains__(self, item)

    def index(
        self, value: T, start: SupportsIndex = 0, stop: SupportsIndex = 9223372036854775807
    ) -> int:
        """Return index of value, tracking ITER_KEY since it searches the list."""
        self._register_access(ITER_KEY)
        return list.index(self, value, start, stop)

    def count(self, value: T) -> int:
        """Return count of value, tracking ITER_KEY since it searches the list."""
        self._register_access(ITER_KEY)
        return list.count(self, value)

    def append(self, item: T) -> None:
        self._check_no_render_mutation()
        list.append(self, item)
        self._mark_dirty(id(item))
        self._mark_iter_dirty()

    def extend(self, items: Iterable[T]) -> None:
        self._check_no_render_mutation()
        items_list = list(items)
        list.extend(self, items_list)
        for item in items_list:
            self._mark_dirty(id(item))
        self._mark_iter_dirty()

    def insert(self, index: SupportsIndex, item: T) -> None:
        self._check_no_render_mutation()
        list.insert(self, index, item)
        self._mark_dirty(id(item))
        self._mark_iter_dirty()

    def remove(self, item: T) -> None:
        self._check_no_render_mutation()
        self._mark_dirty(id(item))
        list.remove(self, item)
        self._mark_iter_dirty()

    def pop(self, index: SupportsIndex = -1) -> T:
        self._check_no_render_mutation()
        item = list.pop(self, index)
        self._mark_dirty(id(item))
        self._mark_iter_dirty()
        return item

    def clear(self) -> None:
        self._check_no_render_mutation()
        for item in list.__iter__(self):
            self._mark_dirty(id(item))
        list.clear(self)
        self._mark_iter_dirty()

    def sort(self, *, key: tp.Callable[[T], tp.Any] | None = None, reverse: bool = False) -> None:
        self._check_no_render_mutation()
        list.sort(self, key=key, reverse=reverse)  # type: ignore[type-var,arg-type]
        self._mark_iter_dirty()

    def reverse(self) -> None:
        self._check_no_render_mutation()
        list.reverse(self)
        self._mark_iter_dirty()

    def copy(self) -> list[T]:
        """Return a plain list copy (not tracked)."""
        return list(self)

    def __add__(self, other: list[T]) -> list[T]:  # type: ignore[override]
        """Concatenation returns a plain list (not TrackedList)."""
        return list(self) + other

    def __radd__(self, other: list[T]) -> list[T]:
        """Reverse concatenation returns a plain list."""
        return other + list(self)

    def __iadd__(self, other: Iterable[T]) -> TrackedList[T]:  # type: ignore[override]
        """In-place concatenation."""
        self.extend(other)
        return self

    def __mul__(self, n: SupportsIndex) -> list[T]:
        """Repetition returns a plain list."""
        return list(self) * n

    def __rmul__(self, n: SupportsIndex) -> list[T]:
        """Reverse repetition returns a plain list."""
        return n * list(self)

    def __imul__(self, n: SupportsIndex) -> TrackedList[T]:
        """In-place repetition."""
        self._check_no_render_mutation()
        n_int = n.__index__()
        if n_int <= 0:
            self.clear()
        else:
            original = list(self)
            for _ in range(n_int - 1):
                self.extend(original)
        return self

    def __repr__(self) -> str:
        return f"TrackedList({list.__repr__(self)})"


class TrackedDict(dict[KT, VT], _TrackedMixin):
    """A reactive dict that tracks access by key.

    Access tracking:
    - `d[key]` / `d.get(key)` / `key in d` registers dependency on key
    - `for k in d` / `len(d)` registers ITER_KEY

    Mutation effects:
    - `d[key] = value` marks key dirty
    - `del d[key]` marks key and ITER_KEY dirty
    - `d.pop(key)` marks key and ITER_KEY dirty
    - `d.update(...)` marks all affected keys and ITER_KEY dirty
    """

    def __new__(
        cls,
        mapping: tp.Mapping[KT, VT] | Iterable[tuple[KT, VT]] = (),
        *,
        owner: Stateful | None = None,
        attr: str = "",
        **kwargs: VT,
    ) -> TrackedDict[KT, VT]:
        return super().__new__(cls)

    def __init__(
        self,
        mapping: tp.Mapping[KT, VT] | Iterable[tuple[KT, VT]] = (),
        *,
        owner: Stateful | None = None,
        attr: str = "",
        **kwargs: VT,
    ) -> None:
        super().__init__(mapping, **kwargs)
        self._init_tracking(owner, attr)

    def __getitem__(self, key: KT) -> VT:
        value = dict.__getitem__(self, key)
        self._register_access(key)
        return value

    def __setitem__(self, key: KT, value: VT) -> None:
        self._check_no_render_mutation()
        is_new = key not in dict.keys(self)
        dict.__setitem__(self, key, value)
        self._mark_dirty(key)
        if is_new:
            self._mark_iter_dirty()

    def __delitem__(self, key: KT) -> None:
        self._check_no_render_mutation()
        dict.__delitem__(self, key)
        self._mark_dirty(key)
        self._mark_iter_dirty()

    def __iter__(self) -> Iterator[KT]:
        self._register_access(ITER_KEY)
        return dict.__iter__(self)

    def __len__(self) -> int:
        self._register_access(ITER_KEY)
        return dict.__len__(self)

    def __contains__(self, key: object) -> bool:
        self._register_access(key)
        return dict.__contains__(self, key)

    @tp.overload  # type: ignore[override]
    def get(self, key: KT) -> VT | None: ...

    @tp.overload
    def get(self, key: KT, default: VT) -> VT: ...

    @tp.overload
    def get(self, key: KT, default: T) -> VT | T: ...

    def get(self, key: KT, default: VT | T | None = None) -> VT | T | None:
        self._register_access(key)
        if key in dict.keys(self):
            return dict.__getitem__(self, key)
        return default

    def keys(self) -> tp.KeysView[KT]:  # type: ignore[override]
        self._register_access(ITER_KEY)
        return dict.keys(self)

    def values(self) -> tp.ValuesView[VT]:  # type: ignore[override]
        self._register_access(ITER_KEY)
        return dict.values(self)

    def items(self) -> tp.ItemsView[KT, VT]:  # type: ignore[override]
        self._register_access(ITER_KEY)
        return dict.items(self)

    def pop(self, key: KT, *default: tp.Any) -> tp.Any:
        self._check_no_render_mutation()
        had_key = key in self
        result = dict.pop(self, key, *default)
        if had_key:
            self._mark_dirty(key)
            self._mark_iter_dirty()
        return result

    def popitem(self) -> tuple[KT, VT]:
        self._check_no_render_mutation()
        key, value = dict.popitem(self)
        self._mark_dirty(key)
        self._mark_iter_dirty()
        return key, value

    def clear(self) -> None:
        self._check_no_render_mutation()
        for key in list(dict.keys(self)):
            self._mark_dirty(key)
        dict.clear(self)
        self._mark_iter_dirty()

    def update(  # type: ignore[override]
        self,
        other: tp.Mapping[KT, VT] | Iterable[tuple[KT, VT]] = (),
        **kwargs: VT,
    ) -> None:
        self._check_no_render_mutation()

        # Determine which keys will be added (new) vs updated
        if isinstance(other, tp.Mapping):
            other_keys: set[tp.Any] = set(other.keys())
        else:
            other = dict(other)
            other_keys = set(other.keys())

        existing_keys: set[tp.Any] = set(dict.keys(self))
        new_keys = other_keys - existing_keys
        new_keys.update(set(kwargs.keys()) - existing_keys)
        all_keys = other_keys | set(kwargs.keys())

        dict.update(self, other, **kwargs)

        for key in all_keys:
            self._mark_dirty(key)
        if new_keys:
            self._mark_iter_dirty()

    def setdefault(self, key: KT, default: VT | None = None) -> VT | None:  # type: ignore[override]
        self._check_no_render_mutation()
        is_new = key not in self
        result = dict.setdefault(self, key, default)  # type: ignore[arg-type]
        if is_new:
            self._mark_dirty(key)
            self._mark_iter_dirty()
        return result

    def copy(self) -> dict[KT, VT]:
        """Return a plain dict copy (not tracked)."""
        return dict(self)

    def __repr__(self) -> str:
        return f"TrackedDict({dict.__repr__(self)})"


class TrackedSet(set[T], _TrackedMixin):
    """A reactive set that tracks access by item value.

    Access tracking:
    - `item in s` registers dependency on the item value
    - `for x in s` / `len(s)` registers ITER_KEY

    Mutation effects:
    - `s.add(x)` marks x and ITER_KEY dirty (if new)
    - `s.remove(x)` marks x and ITER_KEY dirty
    - `s.discard(x)` marks x and ITER_KEY dirty (if existed)

    Note: Items must be hashable (as required by set), so we track by
    value rather than identity. This ensures `"foo" in s` followed by
    `s.add("foo")` triggers re-render even if the string objects differ.
    """

    def __new__(
        cls,
        iterable: Iterable[T] = (),
        *,
        owner: Stateful | None = None,
        attr: str = "",
    ) -> TrackedSet[T]:
        return super().__new__(cls)

    def __init__(
        self,
        iterable: Iterable[T] = (),
        *,
        owner: Stateful | None = None,
        attr: str = "",
    ) -> None:
        super().__init__(iterable)
        self._init_tracking(owner, attr)

    def __iter__(self) -> Iterator[T]:
        self._register_access(ITER_KEY)
        return set.__iter__(self)

    def __len__(self) -> int:
        self._register_access(ITER_KEY)
        return set.__len__(self)

    def __contains__(self, item: object) -> bool:
        # Track by value so `"foo" in s` + `s.add("foo")` triggers re-render
        # even if the string objects have different identities
        self._register_access(item)
        return set.__contains__(self, item)

    def add(self, item: T) -> None:
        self._check_no_render_mutation()
        is_new = not set.__contains__(self, item)
        set.add(self, item)
        self._mark_dirty(item)
        if is_new:
            self._mark_iter_dirty()

    def remove(self, item: T) -> None:
        self._check_no_render_mutation()
        self._mark_dirty(item)
        set.remove(self, item)
        self._mark_iter_dirty()

    def discard(self, item: T) -> None:
        self._check_no_render_mutation()
        existed = set.__contains__(self, item)
        if existed:
            self._mark_dirty(item)
            set.discard(self, item)
            self._mark_iter_dirty()

    def pop(self) -> T:
        self._check_no_render_mutation()
        item = set.pop(self)
        self._mark_dirty(item)
        self._mark_iter_dirty()
        return item

    def clear(self) -> None:
        self._check_no_render_mutation()
        for item in set.__iter__(self):
            self._mark_dirty(item)
        set.clear(self)
        self._mark_iter_dirty()

    def update(self, *others: Iterable[T]) -> None:
        self._check_no_render_mutation()
        new_items: set[T] = set()
        for other in others:
            for item in other:
                if not set.__contains__(self, item):
                    new_items.add(item)

        set.update(self, *others)

        for item in new_items:
            self._mark_dirty(item)
        if new_items:
            self._mark_iter_dirty()

    def intersection_update(self, *others: Iterable[T]) -> None:
        self._check_no_render_mutation()
        to_keep: set[T] = set(self)
        for other in others:
            to_keep &= set(other)
        to_remove = set(self) - to_keep

        set.intersection_update(self, *others)

        for item in to_remove:
            self._mark_dirty(item)
        if to_remove:
            self._mark_iter_dirty()

    def difference_update(self, *others: Iterable[T]) -> None:
        self._check_no_render_mutation()
        to_remove: set[T] = set()
        for other in others:
            to_remove.update(set(self) & set(other))

        set.difference_update(self, *others)

        for item in to_remove:
            self._mark_dirty(item)
        if to_remove:
            self._mark_iter_dirty()

    def symmetric_difference_update(self, other: Iterable[T]) -> None:
        self._check_no_render_mutation()
        other_set = set(other)
        removed = set(self) & other_set
        added = other_set - set(self)

        set.symmetric_difference_update(self, other)

        for item in removed | added:
            self._mark_dirty(item)
        if removed or added:
            self._mark_iter_dirty()

    def copy(self) -> set[T]:
        """Return a plain set copy (not tracked)."""
        return set(self)

    def issubset(self, other: Iterable[T]) -> bool:
        """Test if all elements are in other, tracking ITER_KEY."""
        self._register_access(ITER_KEY)
        return set.issubset(self, set(other))

    def issuperset(self, other: Iterable[T]) -> bool:
        """Test if all elements of other are in self, tracking ITER_KEY."""
        self._register_access(ITER_KEY)
        return set.issuperset(self, set(other))

    def isdisjoint(self, other: Iterable[T]) -> bool:
        """Test if no elements are in common, tracking ITER_KEY."""
        self._register_access(ITER_KEY)
        return set.isdisjoint(self, set(other))

    # Set operations return plain sets (not TrackedSet).
    # We use type: ignore[override] because we intentionally change return types.
    def __and__(self, other: tp.AbstractSet[T]) -> set[T]:  # type: ignore[override]
        return set(self) & set(other)

    def __or__(self, other: tp.AbstractSet[T]) -> set[T]:  # type: ignore[override]
        return set(self) | set(other)

    def __sub__(self, other: tp.AbstractSet[T]) -> set[T]:  # type: ignore[override]
        return set(self) - set(other)

    def __xor__(self, other: tp.AbstractSet[T]) -> set[T]:  # type: ignore[override]
        return set(self) ^ set(other)

    def __iand__(self, other: tp.AbstractSet[T]) -> TrackedSet[T]:  # type: ignore[override]
        self.intersection_update(other)
        return self

    def __ior__(self, other: tp.AbstractSet[T]) -> TrackedSet[T]:  # type: ignore[override]
        self.update(other)
        return self

    def __isub__(self, other: tp.AbstractSet[T]) -> TrackedSet[T]:  # type: ignore[override]
        self.difference_update(other)
        return self

    def __ixor__(self, other: tp.AbstractSet[T]) -> TrackedSet[T]:  # type: ignore[override]
        self.symmetric_difference_update(other)
        return self

    def __repr__(self) -> str:
        return f"TrackedSet({set.__repr__(self)})"
