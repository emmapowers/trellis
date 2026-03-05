"""Type-checking tests for Hotkey literal types.

Run with: pixi run -- basedpyright tests/py/typecheck/test_hotkey_types.py

Lines in the VALID sections must pass with zero errors.
Lines in the INVALID sections must each produce exactly one type error,
suppressed with `pyright: ignore` so the overall file is clean.
"""

from trellis.core.hotkey_types import Hotkey
from trellis.core.keys import KeyFilter, sequence

# ============================================================
# VALID hotkey strings — must produce zero type errors
# ============================================================

# Bare keys
bare_escape: Hotkey = "Escape"
bare_enter: Hotkey = "Enter"
bare_a: Hotkey = "A"
bare_z: Hotkey = "Z"
bare_0: Hotkey = "0"
bare_9: Hotkey = "9"
bare_f1: Hotkey = "F1"
bare_f12: Hotkey = "F12"
bare_space: Hotkey = "Space"
bare_arrow: Hotkey = "ArrowUp"
bare_slash: Hotkey = "/"
bare_backtick: Hotkey = "`"

# Single modifier
ctrl_s: Hotkey = "Control+S"
alt_f4: Hotkey = "Alt+F4"
shift_a: Hotkey = "Shift+A"
meta_s: Hotkey = "Meta+S"
mod_s: Hotkey = "Mod+S"
ctrl_slash: Hotkey = "Control+/"
mod_slash: Hotkey = "Mod+/"

# Two modifiers
ctrl_shift_a: Hotkey = "Control+Shift+A"
mod_shift_s: Hotkey = "Mod+Shift+S"
ctrl_alt_del: Hotkey = "Control+Alt+Delete"
alt_meta_k: Hotkey = "Alt+Meta+K"

# Three modifiers
ctrl_alt_shift_a: Hotkey = "Control+Alt+Shift+A"
mod_alt_shift_enter: Hotkey = "Mod+Alt+Shift+Enter"

# Four modifiers
all_mods_a: Hotkey = "Control+Alt+Shift+Meta+A"

# ============================================================
# INVALID hotkey strings — each line MUST produce a type error
# (suppressed so the file type-checks clean overall)
# ============================================================

wrong_case_ctrl: Hotkey = "ctrl+s"  # pyright: ignore[reportAssignmentType]  # lowercase modifier
wrong_case_escape: Hotkey = "escape"  # pyright: ignore[reportAssignmentType]  # lowercase key
lowercase_a: Hotkey = "a"  # pyright: ignore[reportAssignmentType]  # lowercase letter
wrong_case_mod: Hotkey = "mod+s"  # pyright: ignore[reportAssignmentType]  # lowercase modifier
alias_ctrl: Hotkey = "Ctrl+S"  # pyright: ignore[reportAssignmentType]  # alias not canonical
shift_punct: Hotkey = "Shift+/"  # pyright: ignore[reportAssignmentType]  # shift+punctuation
mod_ctrl: Hotkey = "Mod+Control+S"  # pyright: ignore[reportAssignmentType]  # mod+control conflict
mod_meta: Hotkey = "Mod+Meta+S"  # pyright: ignore[reportAssignmentType]  # mod+meta conflict
wrong_order: Hotkey = (
    "Alt+Control+S"  # pyright: ignore[reportAssignmentType]  # wrong modifier order
)
upper_enter: Hotkey = "ENTER"  # pyright: ignore[reportAssignmentType]  # wrong case
lower_f1: Hotkey = "f1"  # pyright: ignore[reportAssignmentType]  # wrong case
ctrl_shift_punct: Hotkey = (
    "Control+Shift+/"  # pyright: ignore[reportAssignmentType]  # shift+punctuation
)
gibberish: Hotkey = "gibberish"  # pyright: ignore[reportAssignmentType]  # not a real key

# ============================================================
# VALID KeyFilter construction
# ============================================================

_ = KeyFilter(key="S")
_ = KeyFilter(key="S", mod=True)
_ = KeyFilter(key="Escape")
_ = KeyFilter(key="ArrowUp", ctrl=True)
_ = KeyFilter(key="F1", alt=True, shift=True)
_ = KeyFilter(key="/", ctrl=True)

# ============================================================
# INVALID KeyFilter construction — each MUST error
# ============================================================

_ = KeyFilter(key="s")  # pyright: ignore[reportArgumentType]  # lowercase
_ = KeyFilter(key="escape")  # pyright: ignore[reportArgumentType]  # wrong case
_ = KeyFilter(key="ENTER")  # pyright: ignore[reportArgumentType]  # wrong case
_ = KeyFilter(key="nope")  # pyright: ignore[reportArgumentType]  # not a key

# ============================================================
# VALID sequence() calls
# ============================================================

sequence("G", "G")
sequence("Mod+K", "Mod+S")
sequence("D", "I", "W")
sequence("Escape")
sequence("Control+Shift+A", "B")

# ============================================================
# INVALID sequence() calls — each MUST error
# ============================================================

sequence("ctrl+s")  # pyright: ignore[reportArgumentType]  # wrong case
sequence("Shift+/")  # pyright: ignore[reportArgumentType]  # shift+punctuation
sequence("nope")  # pyright: ignore[reportArgumentType]  # invalid key
sequence("G", "nope")  # pyright: ignore[reportArgumentType]  # second arg invalid
