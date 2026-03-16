"""Tests for KeySequence and sequence() helper."""

import pytest

from trellis.core.keys import KeyFilter, KeySequence, sequence


class TestSequence:
    def test_gg(self):
        ks = sequence("G", "G")
        assert ks == KeySequence(steps=(KeyFilter(key="G"), KeyFilter(key="G")))

    def test_chord(self):
        ks = sequence("Mod+K", "Mod+S")
        assert ks == KeySequence(
            steps=(
                KeyFilter(key="K", mod=True),
                KeyFilter(key="S", mod=True),
            )
        )

    def test_three_step(self):
        ks = sequence("D", "I", "W")
        assert len(ks.steps) == 3
        assert ks.steps[0] == KeyFilter(key="D")
        assert ks.steps[1] == KeyFilter(key="I")
        assert ks.steps[2] == KeyFilter(key="W")

    def test_custom_timeout(self):
        ks = KeySequence(steps=(KeyFilter(key="G"), KeyFilter(key="G")), timeout_ms=500)
        assert ks.timeout_ms == 500

    def test_default_timeout(self):
        ks = sequence("G", "G")
        assert ks.timeout_ms == 1000

    def test_invalid_spec_raises(self):
        with pytest.raises(ValueError, match=r"Shift.punctuation"):
            sequence("Shift+/")


class TestToDict:
    def test_gg_serialization(self):
        ks = sequence("G", "G")
        d = ks.to_dict()
        assert d["timeout_ms"] == 1000
        assert len(d["steps"]) == 2
        assert d["steps"][0]["key"] == "G"
        assert d["steps"][1]["key"] == "G"

    def test_chord_serialization(self):
        ks = sequence("Mod+K", "Mod+S")
        d = ks.to_dict()
        assert d["steps"][0]["key"] == "K"
        assert d["steps"][0]["mod"] is True
        assert d["steps"][1]["key"] == "S"
        assert d["steps"][1]["mod"] is True
