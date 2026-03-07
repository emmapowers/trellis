"""HotKey — mount-scoped global keyboard shortcut.

Active when this component is in the tree and enabled=True.
No focus required — registers on the document.
Multiple HotKey components with the same filter resolve by tree depth
(deepest wins). If a handler returns False (pass), the next-deepest
gets a chance.
"""

from __future__ import annotations

import typing as tp

from trellis.core.components.composition import component
from trellis.core.keys import EventType, KeyFilter, KeySequence, parse_key_filter
from trellis.core.rendering.on_key_trait import (
    KeyBindingSpec,
    _serialize_binding,
)
from trellis.core.rendering.session import get_active_session

if tp.TYPE_CHECKING:
    from trellis.core.hotkey_types import Hotkey


@component
def HotKey(
    filter: Hotkey | KeyFilter | KeySequence,
    handler: tp.Callable[..., tp.Any],
    *,
    event_type: EventType = "keydown",
    require_reset: bool = True,
    ignore_in_inputs: bool | None = None,
    enabled: bool = True,
) -> None:
    """Mount-scoped global keyboard shortcut.

    Active when this component is in the tree and enabled=True.
    No focus required — registers on the document.
    """
    if not enabled:
        return

    parsed: KeyFilter | KeySequence
    if isinstance(filter, str):
        parsed = parse_key_filter(filter)
    else:
        parsed = filter

    binding = KeyBindingSpec(
        filter=parsed,
        handler=handler,
        event_type=event_type,
        require_reset=require_reset,
        ignore_in_inputs=ignore_in_inputs,
        enabled=enabled,
    )

    session = get_active_session()
    if session is None or session.active is None:
        return

    element_id = session.active.current_element_id
    if element_id is None:
        return

    element = session.elements.get(element_id)
    if element is None:
        return

    # Compute tree depth from element ID (count "/" separators)
    depth = element_id.count("/")

    serialized = _serialize_binding(binding, 0)
    serialized["depth"] = depth

    element.props["__global_key_filters__"] = [serialized]
