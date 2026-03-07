"""Keyboard handling section of the widget showcase."""

import typing as tp
from dataclasses import dataclass
from threading import Timer

from trellis import HotKey, Stateful, component, mutable, sequence
from trellis import html as h
from trellis import widgets as w
from trellis.app import theme

from ..components import ExampleCard
from ..example import example

# How long the action indicator stays visible (seconds)
_INDICATOR_DURATION = 2.0


@dataclass
class ActionState(Stateful):
    """State for a single action indicator that auto-clears."""

    label: str = ""


def _flash(state: ActionState, label: str) -> tp.Callable[[], bool]:
    """Create a handler that briefly shows a label, then clears it."""

    def handler() -> bool:
        state.label = label
        Timer(_INDICATOR_DURATION, _clear, args=(state,)).start()
        return True

    return handler


def _clear(state: ActionState) -> None:
    state.label = ""


@component
def ActionIndicator(*, state: ActionState) -> None:
    """Inline indicator that appears below a widget when an action fires."""
    if not state.label:
        return

    with h.Div(
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "gap": "6px",
            "padding": "3px 10px",
            "borderRadius": "4px",
            "background": theme.accent_subtle,
            "marginTop": "4px",
        },
    ):
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
            text=state.label,
            font_size=12,
            color=theme.accent_primary,
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
                w.Label(text="+", font_size=11, color=theme.text_muted)
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
                            "fontFamily": "ui-monospace, SFMono-Regular, Menlo, monospace",
                            "lineHeight": "1",
                        },
                    )


@component
def SequenceHint(*, keys: list[str], label: str) -> None:
    """Key sequence hint: [key1] then [key2] description."""
    with h.Div(
        style={
            "display": "flex",
            "alignItems": "center",
            "gap": "8px",
        },
    ):
        for i, key in enumerate(keys):
            if i > 0:
                w.Label(text="then", font_size=11, color=theme.text_muted)
            Kbd(keys=key)
        w.Label(text=label, font_size=13, color=theme.text_secondary)


@example(
    "Focus-scoped (.on_key)",
    includes=[ActionState, ActionIndicator, KeyHint, Kbd],
)
def FocusScopedDemo() -> None:
    """Key handlers that fire only when the element has focus."""
    submit = ActionState()
    cancel = ActionState()

    with w.Column(gap=12):
        with w.Column(gap=4):
            KeyHint(keys="Enter", label="Submit (Shift+Enter does not trigger)")
            w.TextInput(placeholder="Focus and press Enter").on_key(
                "Enter", _flash(submit, "submitted")
            )
            ActionIndicator(state=submit)

        with w.Column(gap=4):
            KeyHint(keys="Escape", label="Cancel")
            w.TextInput(placeholder="Focus and press Escape").on_key(
                "Escape", _flash(cancel, "cancelled")
            )
            ActionIndicator(state=cancel)


@example(
    "Mount-scoped (HotKey)",
    includes=[ActionState, ActionIndicator, KeyHint, Kbd],
)
def MountScopedDemo() -> None:
    """Global shortcuts that fire regardless of focus."""
    save = ActionState()
    search = ActionState()

    with w.Column(gap=12):
        with w.Column(gap=4):
            KeyHint(keys="Mod+S", label="Save (global — works anywhere on page)")
            HotKey(filter="Mod+S", handler=_flash(save, "saved"))
            ActionIndicator(state=save)

        with w.Column(gap=4):
            KeyHint(keys="K", label="Search (ignored when typing in inputs)")
            HotKey(filter="K", handler=_flash(search, "search opened"))
            w.TextInput(placeholder="Type here — K won't trigger")
            ActionIndicator(state=search)


@example(
    "Enabled Toggle",
    includes=[ActionState, ActionIndicator, KeyHint, Kbd],
)
def EnabledToggleDemo() -> None:
    """Hotkey that can be toggled on/off at runtime."""

    @dataclass
    class ToggleState(Stateful):
        active: bool = False

    toggle = ToggleState()
    action = ActionState()

    with w.Column(gap=12):
        with w.Row(gap=12, align="center"):
            KeyHint(keys="Mod+D", label="")
            w.Checkbox(label="Enable shortcut", checked=mutable(toggle.active))
        HotKey(filter="Mod+D", handler=_flash(action, "Mod+D fired"), enabled=toggle.active)
        ActionIndicator(state=action)


@example(
    "Sequences",
    includes=[ActionState, ActionIndicator, SequenceHint, Kbd],
)
def SequenceDemo() -> None:
    """Multi-key sequences and chords."""
    goto = ActionState()
    chord = ActionState()

    with w.Column(gap=12):
        with w.Column(gap=4):
            SequenceHint(keys=["G", "G"], label="Go to top")
            HotKey(filter=sequence("G", "G"), handler=_flash(goto, "go to top"))
            ActionIndicator(state=goto)

        with w.Column(gap=4):
            SequenceHint(keys=["Mod+K", "Mod+S"], label="Command palette save")
            HotKey(
                filter=sequence("Mod+K", "Mod+S"),
                handler=_flash(chord, "command palette: save"),
            )
            ActionIndicator(state=chord)


@component
def KeyboardSection() -> None:
    """Keyboard handling examples."""
    with w.Column(gap=16):
        ExampleCard(example=FocusScopedDemo)
        ExampleCard(example=MountScopedDemo)
        ExampleCard(example=EnabledToggleDemo)
        ExampleCard(example=SequenceDemo)
