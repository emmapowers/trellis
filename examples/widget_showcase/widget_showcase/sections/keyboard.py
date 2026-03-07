"""Keyboard handling section of the widget showcase."""

import typing as tp
from dataclasses import dataclass, field

from trellis import HotKey, Stateful, component, mutable, sequence
from trellis import html as h
from trellis import widgets as w
from trellis.app import theme

from ..components import ExampleCard
from ..example import example


@dataclass
class KeyLogState(Stateful):
    """Shared state for keyboard demos — holds an event log."""

    log: list[str] = field(default_factory=list)


@dataclass
class ToggleState(Stateful):
    """State for the enabled-toggle demo."""

    log: list[str] = field(default_factory=list)
    active: bool = False


def _log_action(state: KeyLogState | ToggleState, action: str) -> tp.Callable[[], bool]:
    """Create a handler that appends to the log and returns True (handled)."""

    def handler() -> bool:
        state.log = [*state.log[-4:], action]
        return True

    return handler


@component
def ActionFeed(*, log: list[str]) -> None:
    """Compact activity feed showing recent keyboard events."""
    if not log:
        with h.Div(
            style={
                "padding": "8px 12px",
                "borderRadius": "6px",
                "border": f"1px dashed {theme.border_default}",
                "color": theme.text_muted,
                "fontSize": "12px",
                "letterSpacing": "0.02em",
            },
        ):
            w.Label(
                text="Waiting for input\u2026",
                font_size=12,
                color=theme.text_muted,
                italic=True,
            )
        return

    with h.Div(
        style={
            "display": "flex",
            "flexDirection": "column",
            "gap": "2px",
        },
    ):
        for i, entry in enumerate(log):
            is_latest = i == len(log) - 1
            with h.Div(
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "8px",
                    "padding": "4px 10px",
                    "borderRadius": "4px",
                    "background": theme.accent_subtle if is_latest else "transparent",
                },
            ):
                # Accent dot for latest entry
                if is_latest:
                    with h.Div(
                        style={
                            "width": "5px",
                            "height": "5px",
                            "borderRadius": "50%",
                            "background": theme.accent_primary,
                            "flexShrink": "0",
                        },
                    ):
                        pass
                w.Label(
                    text=entry,
                    font_size=12,
                    color=theme.text_primary if is_latest else theme.text_muted,
                    style={
                        "fontFamily": "ui-monospace, SFMono-Regular, Menlo, monospace",
                    },
                )


@component
def KeyHint(*, keys: str, label: str) -> None:
    """Keyboard shortcut hint: [keys] description."""
    with h.Div(
        style={
            "display": "flex",
            "alignItems": "center",
            "gap": "8px",
        },
    ):
        Kbd(keys=keys)
        w.Label(text=label, font_size=13, color=theme.text_secondary)


@component
def Kbd(*, keys: str) -> None:
    """Render a keyboard shortcut as styled key caps."""
    parts = keys.replace("+", " + ").split()
    with h.Div(
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "gap": "3px",
        },
    ):
        for part in parts:
            if part == "+":
                w.Label(
                    text="+",
                    font_size=11,
                    color=theme.text_muted,
                )
            else:
                with h.Div(
                    style={
                        "display": "inline-flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "minWidth": "22px",
                        "height": "22px",
                        "padding": "0 5px",
                        "borderRadius": "4px",
                        "border": f"1px solid {theme.border_default}",
                        "background": theme.bg_surface_raised,
                        "boxShadow": f"0 1px 0 {theme.border_default}",
                    },
                ):
                    w.Label(
                        text=part,
                        font_size=11,
                        color=theme.text_primary,
                        style={
                            "fontFamily": ("ui-monospace, SFMono-Regular, Menlo, monospace"),
                            "lineHeight": "1",
                        },
                    )


@example("Focus-scoped (.on_key)", includes=[KeyLogState, ActionFeed, KeyHint, Kbd])
def FocusScopedDemo() -> None:
    """Key handlers that fire only when the element has focus."""
    state = KeyLogState()

    with w.Column(gap=12):
        with w.Column(gap=6):
            KeyHint(keys="Enter", label="Submit (Shift+Enter does not trigger)")
            w.TextInput(placeholder="Focus and press Enter").on_key(
                "Enter", _log_action(state, "submitted")
            )

        with w.Column(gap=6):
            KeyHint(keys="Escape", label="Cancel")
            w.TextInput(placeholder="Focus and press Escape").on_key(
                "Escape", _log_action(state, "cancelled")
            )

        ActionFeed(log=state.log)


@example("Mount-scoped (HotKey)", includes=[KeyLogState, ActionFeed, KeyHint, Kbd])
def MountScopedDemo() -> None:
    """Global shortcuts that fire regardless of focus."""
    state = KeyLogState()

    with w.Column(gap=12):
        with w.Column(gap=6):
            KeyHint(keys="Mod+S", label="Save (global — works anywhere on page)")
            HotKey(filter="Mod+S", handler=_log_action(state, "saved"))

        with w.Column(gap=6):
            KeyHint(keys="K", label="Search (ignored when typing in inputs)")
            HotKey(filter="K", handler=_log_action(state, "search opened"))
            w.TextInput(placeholder="Type here — K won't trigger")

        ActionFeed(log=state.log)


@example("Enabled Toggle", includes=[ToggleState, ActionFeed, KeyHint, Kbd])
def EnabledToggleDemo() -> None:
    """Hotkey that can be toggled on/off at runtime."""
    state = ToggleState()

    def handler() -> bool:
        state.log = [*state.log[-4:], "Mod+D fired"]
        return True

    with w.Column(gap=12):
        with w.Row(gap=12, align="center"):
            KeyHint(keys="Mod+D", label="")
            w.Checkbox(
                label="Enable shortcut",
                checked=mutable(state.active),
            )
        HotKey(filter="Mod+D", handler=handler, enabled=state.active)

        ActionFeed(log=state.log)


@example("Sequences", includes=[KeyLogState, ActionFeed, KeyHint, Kbd])
def SequenceDemo() -> None:
    """Multi-key sequences and chords."""
    state = KeyLogState()

    with w.Column(gap=12):
        with w.Column(gap=6):
            with h.Div(
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "8px",
                },
            ):
                Kbd(keys="G")
                w.Label(text="then", font_size=11, color=theme.text_muted)
                Kbd(keys="G")
                w.Label(text="Go to top", font_size=13, color=theme.text_secondary)
            HotKey(
                filter=sequence("G", "G"),
                handler=_log_action(state, "go to top"),
            )

        with w.Column(gap=6):
            with h.Div(
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "8px",
                },
            ):
                Kbd(keys="Mod+K")
                w.Label(text="then", font_size=11, color=theme.text_muted)
                Kbd(keys="Mod+S")
                w.Label(
                    text="Command palette save",
                    font_size=13,
                    color=theme.text_secondary,
                )
            HotKey(
                filter=sequence("Mod+K", "Mod+S"),
                handler=_log_action(state, "command palette: save"),
            )

        ActionFeed(log=state.log)


@component
def KeyboardSection() -> None:
    """Keyboard handling examples."""
    with w.Column(gap=16):
        ExampleCard(example=FocusScopedDemo)
        ExampleCard(example=MountScopedDemo)
        ExampleCard(example=EnabledToggleDemo)
        ExampleCard(example=SequenceDemo)
