"""Contract tests for codegen-aligned HTML API conventions."""

from __future__ import annotations

import inspect

from trellis import html as h
from trellis.html._generated_runtime import _A
from trellis.html._generated_runtime import Audio as RawAudio
from trellis.html._generated_runtime import Nav as RawNav


def test_media_functions_use_snake_case_autoplay() -> None:
    """Video/Audio APIs expose snake_case auto_play kwargs."""
    video_parameters = inspect.signature(h.Video).parameters
    audio_parameters = inspect.signature(h.Audio).parameters

    assert "auto_play" in video_parameters
    assert "auto_play" in audio_parameters
    assert "autoPlay" not in video_parameters
    assert "autoPlay" not in audio_parameters


def test_text_helper_signatures_use_inner_text_name() -> None:
    """Hybrid helper signatures should expose inner_text in inspection."""
    p_parameters = inspect.signature(h.P).parameters
    anchor_parameters = inspect.signature(h.A).parameters
    raw_anchor_parameters = inspect.signature(_A).parameters

    assert "inner_text" in p_parameters
    assert "inner_text" in anchor_parameters
    assert "inner_text" in raw_anchor_parameters
    assert "text" not in p_parameters
    assert "text" not in anchor_parameters
    assert "text" not in raw_anchor_parameters


def test_generated_runtime_exposes_audio_and_aria_signatures() -> None:
    """Generated runtime should expose audio media props and aria_* attrs."""
    audio_parameters = inspect.signature(RawAudio).parameters
    nav_parameters = inspect.signature(RawNav).parameters

    assert "auto_play" in audio_parameters
    assert "controls" in audio_parameters
    assert "src" in audio_parameters
    assert "aria_label" in nav_parameters
