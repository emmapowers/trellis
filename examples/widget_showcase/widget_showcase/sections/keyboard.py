"""Keyboard handling section of the widget showcase."""

import typing as tp

from trellis import HotKey, Stateful, component, mutable, sequence
from trellis import widgets as w

from ..components import ExampleCard
from ..example import example


class KeyLogState(Stateful):
    """Shared state for keyboard demos — holds an event log."""

    def __init__(self) -> None:
        self.log: list[str] = []


class ToggleState(Stateful):
    """State for the enabled-toggle demo."""

    def __init__(self) -> None:
        self.log: list[str] = []
        self.active: bool = False


def _log_action(state: KeyLogState | ToggleState, action: str) -> tp.Callable[[], bool]:
    """Create a handler that appends to the log and returns True (handled)."""

    def handler() -> bool:
        state.log = [*state.log[-9:], action]
        return True

    return handler


@example("Focus-scoped (.on_key)", includes=[KeyLogState])
def FocusScopedDemo() -> None:
    """Key handlers that fire only when the element has focus."""
    state = KeyLogState()

    with w.Column(gap=8):
        w.Label("1. Focus input, press Enter")
        w.TextInput(placeholder="Enter to submit").on_key("Enter", _log_action(state, "submit"))

        w.Label("2. Focus input, press Escape")
        w.TextInput(placeholder="Escape to cancel").on_key("Escape", _log_action(state, "cancel"))

        w.Label("3. Shift+Enter should not submit")
        w.TextInput(placeholder="Shift+Enter test").on_key(
            "Enter", _log_action(state, "submit-shift-test")
        )

        w.Label("Event log:")
        for entry in state.log:
            w.Label(f"  {entry}")


@example("Mount-scoped (HotKey)", includes=[KeyLogState])
def MountScopedDemo() -> None:
    """Global shortcuts that fire regardless of focus."""
    state = KeyLogState()

    with w.Column(gap=8):
        w.Label("4. Mod+S to save (global)")
        HotKey(filter="Mod+S", handler=_log_action(state, "save"))

        w.Label("5. K to search (ignored in inputs)")
        HotKey(filter="K", handler=_log_action(state, "search"))
        w.TextInput(placeholder="K should NOT fire here")

        w.Label("Event log:")
        for entry in state.log:
            w.Label(f"  {entry}")


@example("Conflict Resolution", includes=[KeyLogState])
def ConflictResolutionDemo() -> None:
    """Deeper HotKey wins; pass falls through to shallower."""
    state = KeyLogState()

    def pass_handler() -> bool:
        state.log = [*state.log[-9:], "inner: passing"]
        return False

    with w.Column(gap=8):
        w.Label("6. Escape: inner passes, outer handles")
        HotKey(filter="Escape", handler=_log_action(state, "outer escape"))
        InnerEscapeDemo(pass_handler=pass_handler)

        w.Label("Event log:")
        for entry in state.log:
            w.Label(f"  {entry}")


@component
def InnerEscapeDemo(*, pass_handler: tp.Callable[[], bool]) -> None:
    """Deeper component with Escape that passes."""
    HotKey(filter="Escape", handler=pass_handler)
    w.Label("(inner Escape registered here)")


@example("Enabled Toggle", includes=[ToggleState])
def EnabledToggleDemo() -> None:
    """Hotkey that can be toggled on/off."""
    state = ToggleState()

    def handler() -> bool:
        state.log = [*state.log[-9:], "mod+d fired"]
        return True

    with w.Column(gap=8):
        w.Label("7. Mod+D only when toggled on")
        w.Checkbox(
            label="Enable Mod+D",
            checked=mutable(state.active),
        )
        HotKey(filter="Mod+D", handler=handler, enabled=state.active)

        w.Label("Event log:")
        for entry in state.log:
            w.Label(f"  {entry}")


@example("Sequences", includes=[KeyLogState])
def SequenceDemo() -> None:
    """Key sequences and chords."""
    state = KeyLogState()

    with w.Column(gap=8):
        w.Label("8. G G to go to top")
        HotKey(filter=sequence("G", "G"), handler=_log_action(state, "gg: go to top"))

        w.Label("9. Mod+K then Mod+S for special save")
        HotKey(
            filter=sequence("Mod+K", "Mod+S"),
            handler=_log_action(state, "chord: special save"),
        )

        w.Label("Event log:")
        for entry in state.log:
            w.Label(f"  {entry}")


@component
def KeyboardSection() -> None:
    """Keyboard handling examples."""
    with w.Column(gap=16):
        ExampleCard(example=FocusScopedDemo)
        ExampleCard(example=MountScopedDemo)
        ExampleCard(example=ConflictResolutionDemo)
        ExampleCard(example=EnabledToggleDemo)
        ExampleCard(example=SequenceDemo)
