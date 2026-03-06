"""Contract tests for codegen-aligned HTML API conventions."""

from __future__ import annotations

import inspect

from trellis import html as h


def test_media_functions_use_snake_case_autoplay() -> None:
    """Video/Audio APIs expose snake_case auto_play kwargs."""
    video_parameters = inspect.signature(h.Video).parameters
    audio_parameters = inspect.signature(h.Audio).parameters

    assert "auto_play" in video_parameters
    assert "auto_play" in audio_parameters
    assert "autoPlay" not in video_parameters
    assert "autoPlay" not in audio_parameters
