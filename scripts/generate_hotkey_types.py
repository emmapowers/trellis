#!/usr/bin/env python3
"""Generate the Hotkey literal type — a union of every valid hotkey string.

Follows TanStack Hotkeys conventions:
- Uppercase letters (A-Z)
- PascalCase modifiers and special keys
- Fixed modifier order: Control+Alt+Shift+Meta
- Shift excludes punctuation keys (layout-dependent)
- Mod excludes Control and Meta (platform conflict)

Run: python scripts/generate_hotkey_types.py
"""

from __future__ import annotations

import textwrap
from pathlib import Path

# --- Key sets (matching KeyboardEvent.key values) ---

LETTER_KEYS = [chr(c) for c in range(ord("A"), ord("Z") + 1)]

NUMBER_KEYS = [str(d) for d in range(10)]

FUNCTION_KEYS = [f"F{n}" for n in range(1, 13)]

NAVIGATION_KEYS = [
    "ArrowUp",
    "ArrowDown",
    "ArrowLeft",
    "ArrowRight",
    "Home",
    "End",
    "PageUp",
    "PageDown",
]

EDITING_KEYS = ["Enter", "Escape", "Space", "Tab", "Backspace", "Delete"]

PUNCTUATION_KEYS = ["/", "[", "]", "\\", "=", "-", ",", ".", "`"]

NON_PUNCTUATION_KEYS = (
    LETTER_KEYS + NUMBER_KEYS + EDITING_KEYS + NAVIGATION_KEYS + FUNCTION_KEYS
)

ALL_KEYS = NON_PUNCTUATION_KEYS + PUNCTUATION_KEYS

# --- Modifier tiers ---
# Each tier is (name, modifier_prefix_parts, allowed_keys)
# Modifier order: Control, Alt, Shift, Meta, Mod
# Rules:
#   - Shift present → no punctuation keys
#   - Mod cannot combine with Control or Meta

TIERS: list[tuple[str, list[str], list[str]]] = [
    # Single modifier
    ("Control", ["Control"], ALL_KEYS),
    ("Alt", ["Alt"], ALL_KEYS),
    ("Shift", ["Shift"], NON_PUNCTUATION_KEYS),
    ("Meta", ["Meta"], ALL_KEYS),
    ("Mod", ["Mod"], ALL_KEYS),
    # Two modifiers
    ("ControlAlt", ["Control", "Alt"], ALL_KEYS),
    ("ControlShift", ["Control", "Shift"], NON_PUNCTUATION_KEYS),
    ("ControlMeta", ["Control", "Meta"], ALL_KEYS),
    ("AltShift", ["Alt", "Shift"], NON_PUNCTUATION_KEYS),
    ("AltMeta", ["Alt", "Meta"], ALL_KEYS),
    ("ShiftMeta", ["Shift", "Meta"], NON_PUNCTUATION_KEYS),
    ("ModAlt", ["Mod", "Alt"], ALL_KEYS),
    ("ModShift", ["Mod", "Shift"], NON_PUNCTUATION_KEYS),
    # Three modifiers
    ("ControlAltShift", ["Control", "Alt", "Shift"], NON_PUNCTUATION_KEYS),
    ("ControlAltMeta", ["Control", "Alt", "Meta"], ALL_KEYS),
    ("ControlShiftMeta", ["Control", "Shift", "Meta"], NON_PUNCTUATION_KEYS),
    ("AltShiftMeta", ["Alt", "Shift", "Meta"], NON_PUNCTUATION_KEYS),
    ("ModAltShift", ["Mod", "Alt", "Shift"], NON_PUNCTUATION_KEYS),
    # Four modifiers (no Mod variants possible)
    ("ControlAltShiftMeta", ["Control", "Alt", "Shift", "Meta"], NON_PUNCTUATION_KEYS),
]


def quote_key(s: str) -> str:
    """Quote a key string, escaping backslashes."""
    escaped = s.replace("\\", "\\\\")
    return f'"{escaped}"'


def format_literal_block(name: str, strings: list[str], indent: str = "    ") -> str:
    """Format a Literal type alias with wrapped string members."""
    if not strings:
        return f"{name} = Never\n"

    quoted = [quote_key(s) for s in strings]
    joined = f",\n{indent}".join(quoted)
    return f"{name} = Literal[\n{indent}{joined},\n]\n"


def generate() -> str:
    parts: list[str] = []

    parts.append('"""Generated hotkey literal types — do not edit manually.')
    parts.append("")
    parts.append("Regenerate with: python scripts/generate_hotkey_types.py")
    parts.append('"""')
    parts.append("")
    parts.append("from __future__ import annotations")
    parts.append("")
    parts.append("from typing import Literal")
    parts.append("")

    # Key category types
    parts.append("# --- Key categories ---")
    parts.append("")
    parts.append(format_literal_block("LetterKey", LETTER_KEYS))
    parts.append(format_literal_block("NumberKey", NUMBER_KEYS))
    parts.append(format_literal_block("FunctionKey", FUNCTION_KEYS))
    parts.append(format_literal_block("NavigationKey", NAVIGATION_KEYS))
    parts.append(format_literal_block("EditingKey", EDITING_KEYS))
    parts.append(format_literal_block("PunctuationKey", PUNCTUATION_KEYS))
    parts.append("")
    parts.append("NonPunctuationKey = LetterKey | NumberKey | EditingKey | NavigationKey | FunctionKey")
    parts.append("Key = NonPunctuationKey | PunctuationKey")
    parts.append("")

    # Bare key hotkeys
    parts.append("# --- Bare keys (no modifier) ---")
    parts.append("")
    parts.append("BareHotkey = Key")
    parts.append("")

    # Modifier tiers
    parts.append("# --- Modifier combinations ---")
    parts.append("")

    tier_names = []
    total = len(ALL_KEYS)  # bare keys

    for tier_name, mods, keys in TIERS:
        prefix = "+".join(mods) + "+"
        hotkey_strings = [f"{prefix}{k}" for k in keys]
        type_name = f"{tier_name}Hotkey"
        parts.append(format_literal_block(type_name, hotkey_strings))
        tier_names.append(type_name)
        total += len(hotkey_strings)

    # Final union
    parts.append("# --- Full union ---")
    parts.append("")
    all_types = ["BareHotkey"] + tier_names
    union = " | ".join(all_types)
    parts.append(f"Hotkey = {union}")
    parts.append("")
    parts.append(f"# Total: {total} valid hotkey strings")
    parts.append("")

    return "\n".join(parts)


def main() -> None:
    output = generate()
    target = Path(__file__).resolve().parent.parent / "src" / "trellis" / "core" / "hotkey_types.py"
    target.write_text(output)

    # Count for summary
    lines = output.count("\n")
    strings = output.count('"') // 2
    print(f"Generated {target.relative_to(target.parent.parent.parent.parent)} ({lines} lines, ~{strings} literal strings)")


if __name__ == "__main__":
    main()
