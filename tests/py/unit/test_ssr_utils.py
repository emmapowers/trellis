"""Tests for shared SSR dehydration utilities."""

from __future__ import annotations

import json

from trellis.platforms.common.ssr_utils import build_dehydration_data


class TestBuildDehydrationData:
    """Tests for build_dehydration_data."""

    def test_with_session_id(self) -> None:
        """JSON contains sessionId when provided."""
        result = build_dehydration_data("sess-123", [])
        data = json.loads(result)
        assert data["sessionId"] == "sess-123"

    def test_without_session_id(self) -> None:
        """JSON omits sessionId when None."""
        result = build_dehydration_data(None, [])
        data = json.loads(result)
        assert "sessionId" not in data

    def test_contains_patches(self) -> None:
        """JSON contains the patches array."""
        patches = [{"type": "add", "id": "1"}]
        result = build_dehydration_data(None, patches)
        data = json.loads(result)
        assert data["patches"] == patches

    def test_contains_server_version(self) -> None:
        """JSON contains serverVersion."""
        result = build_dehydration_data(None, [])
        data = json.loads(result)
        assert "serverVersion" in data
        assert isinstance(data["serverVersion"], str)
