"""OnKeyTrait — focus-scoped key handler for elements.

Attaches filtered key handlers to an element's DOM node via a wrapper div.
Fires only when the element or its descendants have focus.
"""

from __future__ import annotations

import typing as tp
from dataclasses import dataclass, field

from trellis.core.keys import EventType, KeyFilter, KeySequence, parse_key_filter

if tp.TYPE_CHECKING:
    from typing import Self

    from trellis.core.hotkey_types import Hotkey
    from trellis.core.rendering.element import Element
    from trellis.core.rendering.element_state import ElementState
    from trellis.core.rendering.session import RenderSession


@dataclass
class KeyBindingSpec:
    """A single key binding specification."""

    filter: KeyFilter | KeySequence
    handler: tp.Callable[..., tp.Any]
    event_type: EventType = "keydown"
    require_reset: bool = True
    ignore_in_inputs: bool | None = None
    enabled: bool = True


@dataclass
class OnKeyTraitState:
    """Per-element state for OnKeyTrait, stored via ElementState.trait()."""

    bindings: list[KeyBindingSpec] = field(default_factory=list)


def _resolve_ignore_in_inputs(ignore: bool | None, filter: KeyFilter | KeySequence) -> bool:
    """Apply smart defaults for ignore_in_inputs.

    - Modifier combos (Mod+S, Control+X): False — fire even in inputs
    - Escape: False — always fires
    - Bare keys (K, Space), Shift+key, Alt+key: True — ignored in inputs
    - Sequences: True — ignored in inputs
    """
    if ignore is not None:
        return ignore

    if isinstance(filter, KeySequence):
        return True

    if filter.key == "Escape":
        return False

    if filter.mod or filter.ctrl or filter.meta:
        return False

    return True


def _serialize_binding(binding: KeyBindingSpec, index: int) -> dict[str, tp.Any]:
    """Serialize a single binding for client consumption."""
    ignore = _resolve_ignore_in_inputs(binding.ignore_in_inputs, binding.filter)

    result: dict[str, tp.Any] = {
        "event_type": binding.event_type,
        "require_reset": binding.require_reset,
        "ignore_in_inputs": ignore,
        "handler": binding.handler,
    }

    if isinstance(binding.filter, KeySequence):
        result["sequence"] = binding.filter.to_dict()
    else:
        result["filter"] = binding.filter.to_dict()

    return result


class OnKeyTrait:
    """Trait providing focus-scoped key binding via .on_key().

    Fires only when this element or its descendants have focus.
    Handler returns bool (True=handled, False=pass to parent).
    """

    id: str  # Provided by Element
    _session_ref: tp.Any  # Provided by Element

    def on_key(
        self,
        filter: Hotkey | KeyFilter | KeySequence,
        handler: tp.Callable[..., tp.Any],
        *,
        event_type: EventType = "keydown",
        require_reset: bool = True,
        ignore_in_inputs: bool | None = None,
        enabled: bool = True,
    ) -> Self:
        """Register a focus-scoped key binding on this element.

        Fires only when this element or its descendants have focus.
        Handler returns bool (True=handled, False=pass to parent).
        """
        session = self._session_ref()
        if session is None:
            raise RuntimeError("Cannot attach key binding: session has been garbage collected")

        parsed: KeyFilter | KeySequence
        if isinstance(filter, str):
            parsed = parse_key_filter(filter)
        else:
            parsed = filter

        if not hasattr(self, "_on_key_bindings"):
            self._on_key_bindings: list[KeyBindingSpec] = []

        if enabled:
            self._on_key_bindings.append(
                KeyBindingSpec(
                    filter=parsed,
                    handler=handler,
                    event_type=event_type,
                    require_reset=require_reset,
                    ignore_in_inputs=ignore_in_inputs,
                    enabled=enabled,
                )
            )

        return self

    def _after_execute(self, element: Element, state: ElementState, session: RenderSession) -> None:
        """Inject __key_filters__ prop for client-side wrapper div."""
        bindings: list[KeyBindingSpec] = getattr(element, "_on_key_bindings", [])
        if not bindings:
            return

        ts = state.trait(OnKeyTraitState)
        ts.bindings = bindings

        serialized = [_serialize_binding(b, i) for i, b in enumerate(bindings)]
        element.props["__key_filters__"] = serialized
