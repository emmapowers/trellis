"""Tests for KeyFilter parsing and serialization."""

import pytest

from trellis.core.keys import KeyFilter, parse_key_filter


class TestSingleKey:
    def test_enter(self):
        kf = parse_key_filter("Enter")
        assert kf == KeyFilter(key="Enter")

    def test_escape(self):
        kf = parse_key_filter("Escape")
        assert kf == KeyFilter(key="Escape")

    def test_letter(self):
        kf = parse_key_filter("S")
        assert kf == KeyFilter(key="S")

    def test_digit(self):
        kf = parse_key_filter("5")
        assert kf == KeyFilter(key="5")

    def test_function_key(self):
        kf = parse_key_filter("F1")
        assert kf == KeyFilter(key="F1")

    def test_punctuation(self):
        kf = parse_key_filter("/")
        assert kf == KeyFilter(key="/")

    def test_space(self):
        kf = parse_key_filter("Space")
        assert kf == KeyFilter(key="Space")


class TestCaseNormalization:
    def test_lowercase_letter(self):
        kf = parse_key_filter("s")
        assert kf == KeyFilter(key="S")

    def test_ctrl_lowercase(self):
        kf = parse_key_filter("ctrl+s")
        assert kf == KeyFilter(key="S", ctrl=True)

    def test_mixed_case_modifier(self):
        kf = parse_key_filter("CONTROL+a")
        assert kf == KeyFilter(key="A", ctrl=True)

    def test_enter_lowercase(self):
        kf = parse_key_filter("enter")
        assert kf == KeyFilter(key="Enter")


class TestModifiers:
    def test_mod(self):
        kf = parse_key_filter("Mod+S")
        assert kf == KeyFilter(key="S", mod=True)

    def test_control(self):
        kf = parse_key_filter("Control+S")
        assert kf == KeyFilter(key="S", ctrl=True)

    def test_shift(self):
        kf = parse_key_filter("Shift+A")
        assert kf == KeyFilter(key="A", shift=True)

    def test_alt(self):
        kf = parse_key_filter("Alt+S")
        assert kf == KeyFilter(key="S", alt=True)

    def test_meta(self):
        kf = parse_key_filter("Meta+S")
        assert kf == KeyFilter(key="S", meta=True)

    def test_control_shift(self):
        kf = parse_key_filter("Control+Shift+Delete")
        assert kf == KeyFilter(key="Delete", ctrl=True, shift=True)

    def test_control_alt_shift(self):
        kf = parse_key_filter("Control+Alt+Shift+A")
        assert kf == KeyFilter(key="A", ctrl=True, shift=True, alt=True)

    def test_modifier_aliases(self):
        assert parse_key_filter("Cmd+S") == KeyFilter(key="S", meta=True)
        assert parse_key_filter("Command+S") == KeyFilter(key="S", meta=True)
        assert parse_key_filter("Option+S") == KeyFilter(key="S", alt=True)


class TestValidation:
    def test_shift_punctuation_rejected(self):
        with pytest.raises(ValueError, match=r"Shift.punctuation"):
            parse_key_filter("Shift+/")

    def test_mod_control_rejected(self):
        with pytest.raises(ValueError, match=r"Mod.Control"):
            parse_key_filter("Mod+Control+S")

    def test_mod_meta_rejected(self):
        with pytest.raises(ValueError, match=r"Mod.Meta"):
            parse_key_filter("Mod+Meta+S")

    def test_empty_string(self):
        with pytest.raises(ValueError, match="Empty"):
            parse_key_filter("")

    def test_whitespace_only(self):
        with pytest.raises(ValueError, match="Empty"):
            parse_key_filter("   ")

    def test_trailing_plus(self):
        with pytest.raises(ValueError, match="Trailing"):
            parse_key_filter("Control+")

    def test_unknown_modifier(self):
        with pytest.raises(ValueError, match="Unknown modifier"):
            parse_key_filter("Super+S")

    def test_duplicate_modifier(self):
        with pytest.raises(ValueError, match="Duplicate"):
            parse_key_filter("Control+Ctrl+S")

    def test_unknown_key(self):
        with pytest.raises(ValueError, match="Unknown key"):
            parse_key_filter("FooBar")


class TestToDict:
    def test_simple_key(self):
        kf = KeyFilter(key="Enter")
        assert kf.to_dict() == {
            "key": "Enter",
            "ctrl": False,
            "shift": False,
            "alt": False,
            "meta": False,
            "mod": False,
        }

    def test_mod_key(self):
        kf = KeyFilter(key="S", mod=True)
        d = kf.to_dict()
        assert d["key"] == "S"
        assert d["mod"] is True
        assert d["ctrl"] is False

    def test_multiple_modifiers(self):
        kf = KeyFilter(key="A", ctrl=True, shift=True, alt=True)
        d = kf.to_dict()
        assert d["ctrl"] is True
        assert d["shift"] is True
        assert d["alt"] is True
        assert d["meta"] is False
