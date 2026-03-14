"""StateDependency protocol for unified watcher tracking.

Both Element and ReactiveEffect satisfy this protocol, allowing Stateful
properties and tracked collections to notify any kind of watcher when
state changes.
"""

from __future__ import annotations

import typing as tp


@tp.runtime_checkable
class StateDependency(tp.Protocol):
    """Something that can be notified when state it depends on changes."""

    def notify_dirty(self) -> None: ...

    def __hash__(self) -> int: ...
