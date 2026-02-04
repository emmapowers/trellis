"""Tests for Config dataclass with ConfigVar resolution."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from trellis.app.config import Config
from trellis.app.configvars import cli_context, coerce_value
from trellis.platforms.common.base import PlatformType
from trellis.routing.enums import RoutingMode


class TestConfigCreation:
    """Test Config creation with required fields."""

    def test_creates_with_required_fields(self) -> None:
        config = Config(name="myapp", module="main")
        assert config.name == "myapp"
        assert config.module == "main"

    def test_missing_name_raises(self) -> None:
        with pytest.raises(TypeError, match=r"missing required argument.*name"):
            Config(name="", module="main")  # type: ignore

    def test_missing_module_raises(self) -> None:
        with pytest.raises(TypeError, match=r"missing required argument.*module"):
            Config(name="myapp", module="")  # type: ignore

    def test_has_sensible_defaults(self) -> None:
        config = Config(name="myapp", module="main")

        # General defaults
        assert config.platform == PlatformType.SERVER
        assert config.force_build is False
        assert config.watch is False
        assert config.hot_reload is True
        assert config.routing_mode == RoutingMode.URL
        assert config.debug == ""
        assert config.assets_dir == Path("./assets/")
        assert config.title == "myapp"  # defaults to name

        # Server defaults
        assert config.host == "127.0.0.1"
        assert config.port is None

        # Desktop defaults
        assert config.window_size == "maximized"


class TestConfigFromEnv:
    """Test Config resolution from environment variables."""

    def test_reads_platform_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRELLIS_PLATFORM", "desktop")
        config = Config(name="myapp", module="main")
        assert config.platform == PlatformType.DESKTOP

    def test_reads_server_host_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRELLIS_SERVER_HOST", "0.0.0.0")
        config = Config(name="myapp", module="main")
        assert config.host == "0.0.0.0"

    def test_reads_server_port_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRELLIS_SERVER_PORT", "9000")
        config = Config(name="myapp", module="main")
        assert config.port == 9000

    def test_reads_window_size_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRELLIS_DESKTOP_WINDOW_SIZE", "1920x1080")
        config = Config(name="myapp", module="main")
        assert config.window_size == "1920x1080"


class TestConfigFromCli:
    """Test Config resolution with CLI context."""

    def test_cli_overrides_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRELLIS_SERVER_PORT", "9000")
        with cli_context({"port": 7777}):
            config = Config(name="myapp", module="main")
            assert config.port == 7777

    def test_cli_overrides_constructor_value(self) -> None:
        with cli_context({"port": 7777}):
            config = Config(name="myapp", module="main", port=5555)
            assert config.port == 7777

    def test_env_overrides_constructor_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRELLIS_SERVER_PORT", "9000")
        config = Config(name="myapp", module="main", port=5555)
        assert config.port == 9000

    def test_constructor_value_overrides_default(self) -> None:
        config = Config(name="myapp", module="main", port=5555)
        assert config.port == 5555


class TestConfigValidation:
    """Test Config field validation."""

    def test_invalid_port_raises(self) -> None:
        with pytest.raises(ValueError, match="Port must be 1-65535"):
            Config(name="myapp", module="main", port=0)

    def test_invalid_window_size_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid window size"):
            Config(name="myapp", module="main", window_size="invalid")

    def test_invalid_batch_delay_raises(self) -> None:
        with pytest.raises(ValueError, match="batch_delay must be"):
            Config(name="myapp", module="main", batch_delay=0.0001)

    def test_invalid_debug_category_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown debug categor"):
            Config(name="myapp", module="main", debug="invalid_category")


class TestConfigBatchDelay:
    """Test batch_delay field specifically."""

    def test_default_batch_delay(self) -> None:
        config = Config(name="myapp", module="main")
        assert config.batch_delay == pytest.approx(1 / 30)

    def test_custom_batch_delay(self) -> None:
        config = Config(name="myapp", module="main", batch_delay=0.1)
        assert config.batch_delay == 0.1

    def test_batch_delay_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRELLIS_BATCH_DELAY", "0.05")
        config = Config(name="myapp", module="main")
        assert config.batch_delay == 0.05


class TestConfigAssetsDir:
    """Test assets_dir field with Path coercion."""

    def test_assets_dir_from_constructor(self) -> None:
        config = Config(name="myapp", module="main", assets_dir=Path("/var/www"))
        assert config.assets_dir == Path("/var/www")

    def test_assets_dir_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRELLIS_ASSETS_DIR", "~/assets")
        config = Config(name="myapp", module="main")
        assert config.assets_dir == Path.home() / "assets"

    def test_assets_dir_default(self) -> None:
        config = Config(name="myapp", module="main")
        assert config.assets_dir == Path("./assets/")


class TestConfigRoutingMode:
    """Test routing_mode platform-dependent defaults."""

    def test_server_platform_defaults_to_url_routing(self) -> None:
        config = Config(name="myapp", module="main", platform=PlatformType.SERVER)
        assert config.routing_mode == RoutingMode.URL

    def test_browser_platform_defaults_to_hash_routing(self) -> None:
        config = Config(name="myapp", module="main", platform=PlatformType.BROWSER)
        assert config.routing_mode == RoutingMode.HASH

    def test_desktop_platform_defaults_to_hidden_routing(self) -> None:
        config = Config(name="myapp", module="main", platform=PlatformType.DESKTOP)
        assert config.routing_mode == RoutingMode.HIDDEN

    def test_explicit_routing_mode_overrides_platform_default(self) -> None:
        config = Config(
            name="myapp",
            module="main",
            platform=PlatformType.SERVER,
            routing_mode=RoutingMode.HASH,
        )
        assert config.routing_mode == RoutingMode.HASH

    def test_routing_mode_from_env_overrides_platform_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TRELLIS_ROUTING_MODE", "hidden")
        config = Config(name="myapp", module="main", platform=PlatformType.SERVER)
        assert config.routing_mode == RoutingMode.HIDDEN

    def test_routing_mode_from_cli_overrides_platform_default(self) -> None:
        with cli_context({"routing_mode": RoutingMode.HASH}):
            config = Config(name="myapp", module="main", platform=PlatformType.DESKTOP)
            assert config.routing_mode == RoutingMode.HASH


class TestConfigTitle:
    """Test title field defaults and overrides."""

    def test_title_defaults_to_name(self) -> None:
        config = Config(name="myapp", module="main")
        assert config.title == "myapp"

    def test_title_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRELLIS_TITLE", "My Custom Title")
        config = Config(name="myapp", module="main")
        assert config.title == "My Custom Title"

    def test_explicit_title_overrides_name(self) -> None:
        config = Config(name="myapp", module="main", title="Custom Title")
        assert config.title == "Custom Title"


class TestCoerceValue:
    """Test coerce_value() helper function."""

    def test_coerces_platform_enum(self) -> None:
        result = coerce_value("platform", "desktop")
        assert result == PlatformType.DESKTOP

    def test_coerces_port_to_int(self) -> None:
        result = coerce_value("port", "8080")
        assert result == 8080
        assert isinstance(result, int)

    def test_coerces_path(self) -> None:
        result = coerce_value("assets_dir", "/var/www/assets")
        assert result == Path("/var/www/assets")

    def test_unknown_field_raises_key_error(self) -> None:
        with pytest.raises(KeyError, match="No ConfigVar registered for field"):
            coerce_value("nonexistent_field", "value")


class TestConfigToJson:
    """Test Config.to_json() serialization."""

    def test_serializes_required_fields(self) -> None:
        config = Config(name="myapp", module="main")
        result = json.loads(config.to_json())
        assert result["name"] == "myapp"
        assert result["module"] == "main"

    def test_serializes_enum_as_string_value(self) -> None:
        config = Config(name="myapp", module="main", platform=PlatformType.DESKTOP)
        result = json.loads(config.to_json())
        assert result["platform"] == "desktop"

    def test_serializes_path_as_string(self) -> None:
        config = Config(name="myapp", module="main", assets_dir=Path("/var/www"))
        result = json.loads(config.to_json())
        assert result["assets_dir"] == "/var/www"

    def test_serializes_none_as_null(self) -> None:
        config = Config(name="myapp", module="main", port=None)
        result = json.loads(config.to_json())
        assert result["port"] is None

    def test_serializes_all_fields(self) -> None:
        config = Config(name="myapp", module="main")
        result = json.loads(config.to_json())
        # Check that all Config fields are present
        expected_fields = {
            "name",
            "module",
            "python_path",
            "platform",
            "force_build",
            "watch",
            "batch_delay",
            "hot_reload",
            "routing_mode",
            "debug",
            "assets_dir",
            "title",
            "host",
            "port",
            "window_size",
        }
        assert set(result.keys()) == expected_fields


class TestConfigFromJson:
    """Test Config.from_json() deserialization."""

    def test_deserializes_required_fields(self) -> None:
        json_str = json.dumps({"name": "myapp", "module": "main"})
        config = Config.from_json(json_str)
        assert config.name == "myapp"
        assert config.module == "main"

    def test_deserializes_enum_from_string(self) -> None:
        json_str = json.dumps({"name": "myapp", "module": "main", "platform": "desktop"})
        config = Config.from_json(json_str)
        assert config.platform == PlatformType.DESKTOP

    def test_deserializes_path_from_string(self) -> None:
        json_str = json.dumps({"name": "myapp", "module": "main", "assets_dir": "/var/www"})
        config = Config.from_json(json_str)
        assert config.assets_dir == Path("/var/www")

    def test_deserializes_null_as_none(self) -> None:
        json_str = json.dumps({"name": "myapp", "module": "main", "port": None})
        config = Config.from_json(json_str)
        assert config.port is None

    def test_missing_fields_use_defaults(self) -> None:
        json_str = json.dumps({"name": "myapp", "module": "main"})
        config = Config.from_json(json_str)
        # Check defaults are applied
        assert config.platform == PlatformType.SERVER
        assert config.host == "127.0.0.1"
        assert config.watch is False


class TestConfigJsonRoundTrip:
    """Test round-trip JSON serialization/deserialization."""

    def test_roundtrip_preserves_values(self) -> None:
        original = Config(
            name="myapp",
            module="main",
            platform=PlatformType.DESKTOP,
            port=9000,
            host="0.0.0.0",
            assets_dir=Path("/var/www"),
            watch=True,
            debug="render,state",
        )
        json_str = original.to_json()
        restored = Config.from_json(json_str)

        assert restored.name == original.name
        assert restored.module == original.module
        assert restored.platform == original.platform
        assert restored.port == original.port
        assert restored.host == original.host
        assert restored.assets_dir == original.assets_dir
        assert restored.watch == original.watch
        assert restored.debug == original.debug


class TestConfigJsonErrors:
    """Test error handling in JSON serialization/deserialization."""

    def test_missing_name_raises_type_error(self) -> None:
        json_str = json.dumps({"module": "main"})
        with pytest.raises(TypeError, match=r"missing required argument.*name"):
            Config.from_json(json_str)

    def test_invalid_json_raises_decode_error(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            Config.from_json("not valid json {")

    def test_invalid_enum_raises_value_error(self) -> None:
        json_str = json.dumps({"name": "myapp", "module": "main", "platform": "invalid"})
        with pytest.raises(ValueError, match="not a valid PlatformType"):
            Config.from_json(json_str)

    def test_invalid_port_runs_validation(self) -> None:
        json_str = json.dumps({"name": "myapp", "module": "main", "port": 99999})
        with pytest.raises(ValueError, match="Port must be 1-65535"):
            Config.from_json(json_str)
