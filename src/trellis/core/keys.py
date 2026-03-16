"""Keyboard filter types for Trellis key handling."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from trellis.core.hotkey_types import Hotkey, Key

_MAX_FUNCTION_KEY = 12


@dataclass(frozen=True)
class KeyFilter:
    """A parsed keyboard filter — matches a specific key + modifier combination."""

    key: Key
    ctrl: bool = False
    shift: bool = False
    alt: bool = False
    meta: bool = False
    mod: bool = False  # Cmd on Mac, Ctrl on Win/Linux — resolved client-side

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class KeySequence:
    """An ordered sequence of key filters (e.g. vim's "gg", "diw")."""

    steps: tuple[KeyFilter, ...]
    timeout_ms: int = 1000

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def sequence(*specs: Hotkey) -> KeySequence:
    """Create a type-safe key sequence from hotkey specs.

    Each argument is type-checked as a valid Hotkey literal:
        sequence("G", "G")           # vim go-to-top
        sequence("Mod+K", "Mod+S")   # chord: Cmd+K then Cmd+S
        sequence("D", "I", "W")      # vim delete-inner-word
    """
    return KeySequence(steps=tuple(parse_key_filter(s) for s in specs))


# Canonical modifier names, in the fixed order used for hotkey strings
_MODIFIER_ALIASES: dict[str, str] = {
    "control": "ctrl",
    "ctrl": "ctrl",
    "shift": "shift",
    "alt": "alt",
    "option": "alt",
    "meta": "meta",
    "command": "meta",
    "cmd": "meta",
    "mod": "mod",
}

# Maps from KeyboardEvent.key values (lowercased) to canonical Key form
_KEY_ALIASES: dict[str, str] = {
    "esc": "Escape",
    "return": "Enter",
    "up": "ArrowUp",
    "down": "ArrowDown",
    "left": "ArrowLeft",
    "right": "ArrowRight",
    " ": "Space",
}

_PUNCTUATION_KEYS = frozenset("/[]\\=-.`,")


def parse_key_filter(spec: str) -> KeyFilter:
    """Parse a hotkey spec string into a KeyFilter.

    Accepts case-insensitive input and normalizes to canonical form.
    Validates modifier conflicts (Mod+Control, Mod+Meta) and
    Shift+punctuation (layout-dependent).

    Examples:
        parse_key_filter("Mod+S")       → KeyFilter(key="S", mod=True)
        parse_key_filter("Escape")      → KeyFilter(key="Escape")
        parse_key_filter("ctrl+shift+A") → KeyFilter(key="A", ctrl=True, shift=True)
    """
    if not spec or not spec.strip():
        raise ValueError("Empty hotkey spec")

    tokens = spec.split("+")
    if tokens[-1] == "":
        raise ValueError(f"Trailing '+' in hotkey spec: {spec!r}")

    modifiers: dict[str, bool] = {}
    raw_key = tokens[-1]

    for token in tokens[:-1]:
        lower = token.lower()
        canonical = _MODIFIER_ALIASES.get(lower)
        if canonical is None:
            raise ValueError(
                f"Unknown modifier {token!r} in hotkey spec: {spec!r}. "
                f"Valid modifiers: Control, Shift, Alt, Meta, Mod"
            )
        if canonical in modifiers:
            raise ValueError(f"Duplicate modifier {token!r} in hotkey spec: {spec!r}")
        modifiers[canonical] = True

    # Resolve the key to canonical form
    key = _resolve_key(raw_key)

    # Validate: Mod cannot combine with Control or Meta
    if modifiers.get("mod"):
        if modifiers.get("ctrl"):
            raise ValueError(
                f"Mod+Control conflict in {spec!r}: Mod resolves to Control on Windows/Linux"
            )
        if modifiers.get("meta"):
            raise ValueError(f"Mod+Meta conflict in {spec!r}: Mod resolves to Meta on macOS")

    # Validate: Shift + punctuation is layout-dependent
    if modifiers.get("shift") and key in _PUNCTUATION_KEYS:
        raise ValueError(
            f"Shift+punctuation in {spec!r}: Shift changes punctuation keys across keyboard layouts"
        )

    return KeyFilter(
        key=key,  # type: ignore[arg-type]  # runtime-validated Key
        ctrl=modifiers.get("ctrl", False),
        shift=modifiers.get("shift", False),
        alt=modifiers.get("alt", False),
        meta=modifiers.get("meta", False),
        mod=modifiers.get("mod", False),
    )


def _resolve_key(raw: str) -> str:
    """Resolve a raw key token to its canonical Key form."""
    # Check aliases first (case-insensitive)
    alias = _KEY_ALIASES.get(raw.lower())
    if alias is not None:
        return alias

    # Single character: uppercase letters, keep digits and punctuation as-is
    if len(raw) == 1:
        if raw.isalpha():
            return raw.upper()
        return raw

    # Multi-character: try case-insensitive match against known keys
    lower = raw.lower()

    # PascalCase special keys
    _KNOWN_KEYS = {
        "enter": "Enter",
        "escape": "Escape",
        "space": "Space",
        "tab": "Tab",
        "backspace": "Backspace",
        "delete": "Delete",
        "arrowup": "ArrowUp",
        "arrowdown": "ArrowDown",
        "arrowleft": "ArrowLeft",
        "arrowright": "ArrowRight",
        "home": "Home",
        "end": "End",
        "pageup": "PageUp",
        "pagedown": "PageDown",
    }

    known = _KNOWN_KEYS.get(lower)
    if known is not None:
        return known

    # Function keys
    if lower.startswith("f") and lower[1:].isdigit():
        n = int(lower[1:])
        if 1 <= n <= _MAX_FUNCTION_KEY:
            return f"F{n}"

    raise ValueError(f"Unknown key: {raw!r}")


EventType = Literal["keydown", "keyup"]
