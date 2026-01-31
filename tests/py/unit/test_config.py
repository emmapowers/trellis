"""Tests for Config dataclass with ConfigVar resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from trellis.app.config import Config
from trellis.app.configvars import cli_context
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
        assert config.routing_mode == RoutingMode.STANDARD
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

    def test_server_platform_defaults_to_standard_routing(self) -> None:
        config = Config(name="myapp", module="main", platform=PlatformType.SERVER)
        assert config.routing_mode == RoutingMode.STANDARD

    def test_browser_platform_defaults_to_hash_url_routing(self) -> None:
        config = Config(name="myapp", module="main", platform=PlatformType.BROWSER)
        assert config.routing_mode == RoutingMode.HASH_URL

    def test_desktop_platform_defaults_to_embedded_routing(self) -> None:
        config = Config(name="myapp", module="main", platform=PlatformType.DESKTOP)
        assert config.routing_mode == RoutingMode.EMBEDDED

    def test_explicit_routing_mode_overrides_platform_default(self) -> None:
        config = Config(
            name="myapp",
            module="main",
            platform=PlatformType.SERVER,
            routing_mode=RoutingMode.HASH_URL,
        )
        assert config.routing_mode == RoutingMode.HASH_URL

    def test_routing_mode_from_env_overrides_platform_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TRELLIS_ROUTING_MODE", "embedded")
        config = Config(name="myapp", module="main", platform=PlatformType.SERVER)
        assert config.routing_mode == RoutingMode.EMBEDDED

    def test_routing_mode_from_cli_overrides_platform_default(self) -> None:
        with cli_context({"routing_mode": RoutingMode.HASH_URL}):
            config = Config(name="myapp", module="main", platform=PlatformType.DESKTOP)
            assert config.routing_mode == RoutingMode.HASH_URL


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
