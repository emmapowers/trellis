"""Tests for packaging config fields."""

from __future__ import annotations

import json

import pytest

from trellis.app.config import Config
from trellis.platforms.common.base import PlatformType


class TestPackagingConfigFields:
    """Tests for new packaging-related config fields."""

    def test_defaults_to_none(self) -> None:
        config = Config(name="myapp", module="main")
        assert config.identifier is None
        assert config.version is None
        assert config.update_url is None
        assert config.update_pubkey is None

    def test_accepts_values(self) -> None:
        config = Config(
            name="myapp",
            module="main",
            identifier="com.example.myapp",
            version="1.0.0",
            update_url="https://updates.example.com",
            update_pubkey="dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXk=",
        )
        assert config.identifier == "com.example.myapp"
        assert config.version == "1.0.0"
        assert config.update_url == "https://updates.example.com"
        assert config.update_pubkey == "dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXk="

    def test_survives_json_roundtrip(self) -> None:
        original = Config(
            name="myapp",
            module="main",
            platform=PlatformType.DESKTOP,
            identifier="com.example.myapp",
            version="2.0.0",
            update_url="https://updates.example.com/v2",
            update_pubkey="pubkey123",
        )
        json_str = original.to_json()
        restored = Config.from_json(json_str)

        assert restored.identifier == original.identifier
        assert restored.version == original.version
        assert restored.update_url == original.update_url
        assert restored.update_pubkey == original.update_pubkey

    def test_none_values_survive_roundtrip(self) -> None:
        original = Config(name="myapp", module="main")
        json_str = original.to_json()
        restored = Config.from_json(json_str)

        assert restored.identifier is None
        assert restored.version is None
        assert restored.update_url is None
        assert restored.update_pubkey is None

    def test_to_json_includes_packaging_fields(self) -> None:
        config = Config(name="myapp", module="main", identifier="com.example.myapp")
        result = json.loads(config.to_json())
        assert "identifier" in result
        assert result["identifier"] == "com.example.myapp"
        assert "version" in result
        assert "update_url" in result
        assert "update_pubkey" in result

    def test_collect_bundle_extras_no_longer_accepted(self) -> None:
        """collect_bundle_extras was removed — passing it should raise TypeError."""
        with pytest.raises(TypeError):
            Config(
                name="myapp",
                module="main",
                collect_bundle_extras=lambda p, c: None,  # type: ignore[call-arg]
            )
