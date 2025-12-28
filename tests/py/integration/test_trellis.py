"""Tests for Trellis unified entry point."""

import sys
from importlib.util import find_spec
from unittest.mock import patch

import pytest

from trellis.platforms.common.base import PlatformArgumentError, PlatformType

# Skip marker for tests that require pytauri (desktop platform)
requires_pytauri = pytest.mark.skipif(
    find_spec("pytauri") is None,
    reason="pytauri not installed",
)
from trellis.app.entry import (
    Trellis,
    _TrellisArgs,
    _detect_platform,
    _parse_cli_args,
)


class TestTrellisArgs:
    """Tests for _TrellisArgs helper class."""

    def test_set_default_stores_value(self) -> None:
        """set_default() stores value if key not present."""
        args = _TrellisArgs()
        args.set_default("host", "localhost")
        assert args.get("host") == "localhost"

    def test_set_default_does_not_override(self) -> None:
        """set_default() does not override existing value."""
        args = _TrellisArgs()
        args.set("host", "0.0.0.0")
        args.set_default("host", "localhost")
        assert args.get("host") == "0.0.0.0"

    def test_set_marks_explicit(self) -> None:
        """set() marks value as explicit."""
        args = _TrellisArgs()
        args.set("port", 8080)
        assert args.is_explicit("port")

    def test_set_default_not_explicit(self) -> None:
        """set_default() does not mark value as explicit."""
        args = _TrellisArgs()
        args.set_default("port", 8080)
        assert not args.is_explicit("port")

    def test_to_dict_returns_all_values(self) -> None:
        """to_dict() returns all stored values."""
        args = _TrellisArgs()
        args.set_default("host", "localhost")
        args.set("port", 8080)
        assert args.to_dict() == {"host": "localhost", "port": 8080}

    def test_explicit_args_for_platform_server(self) -> None:
        """explicit_args_for_platform() returns server args."""
        args = _TrellisArgs()
        args.set("host", "0.0.0.0")
        args.set("port", 8080)
        args.set_default("window_title", "Test")
        result = args.explicit_args_for_platform(PlatformType.SERVER)
        assert set(result) == {"host", "port"}

    def test_explicit_args_for_platform_desktop(self) -> None:
        """explicit_args_for_platform() returns desktop args."""
        args = _TrellisArgs()
        args.set("window_title", "My App")
        args.set("window_width", 800)
        args.set_default("host", "localhost")
        result = args.explicit_args_for_platform(PlatformType.DESKTOP)
        assert set(result) == {"window_title", "window_width"}


class TestDetectPlatform:
    """Tests for platform auto-detection."""

    def test_default_is_server(self) -> None:
        """Default platform is SERVER when not in Pyodide."""
        assert _detect_platform() == PlatformType.SERVER

    def test_pyodide_detected_as_browser(self) -> None:
        """Platform is BROWSER when pyodide module present."""
        with patch.dict(sys.modules, {"pyodide": object()}):
            assert _detect_platform() == PlatformType.BROWSER


class TestParseCLIArgs:
    """Tests for CLI argument parsing."""

    def test_no_args_returns_none_platform(self) -> None:
        """No CLI args returns None platform."""
        with patch("sys.argv", ["app"]):
            platform, args = _parse_cli_args()
            assert platform is None
            assert args == {}

    def test_platform_server(self) -> None:
        """--platform=server sets SERVER."""
        with patch("sys.argv", ["app", "--platform=server"]):
            platform, _ = _parse_cli_args()
            assert platform == PlatformType.SERVER

    def test_platform_desktop(self) -> None:
        """--platform=desktop sets DESKTOP."""
        with patch("sys.argv", ["app", "--platform=desktop"]):
            platform, _ = _parse_cli_args()
            assert platform == PlatformType.DESKTOP

    def test_platform_browser(self) -> None:
        """--platform=browser sets BROWSER."""
        with patch("sys.argv", ["app", "--platform=browser"]):
            platform, _ = _parse_cli_args()
            assert platform == PlatformType.BROWSER

    def test_desktop_shortcut(self) -> None:
        """--desktop is shortcut for --platform=desktop."""
        with patch("sys.argv", ["app", "--desktop"]):
            platform, _ = _parse_cli_args()
            assert platform == PlatformType.DESKTOP

    def test_desktop_and_platform_conflict(self) -> None:
        """--desktop and --platform together raises error."""
        with patch("sys.argv", ["app", "--desktop", "--platform=server"]):
            with pytest.raises(PlatformArgumentError) as exc:
                _parse_cli_args()
            assert "--desktop" in str(exc.value)
            assert "--platform" in str(exc.value)

    def test_host_arg(self) -> None:
        """--host is parsed."""
        with patch("sys.argv", ["app", "--host=0.0.0.0"]):
            _, args = _parse_cli_args()
            assert args == {"host": "0.0.0.0"}

    def test_port_arg(self) -> None:
        """--port is parsed as int."""
        with patch("sys.argv", ["app", "--port=9000"]):
            _, args = _parse_cli_args()
            assert args == {"port": 9000}

    def test_unknown_args_ignored(self) -> None:
        """Unknown args are ignored (for app-specific args)."""
        with patch("sys.argv", ["app", "--my-custom-arg", "--another=value"]):
            platform, args = _parse_cli_args()
            assert platform is None
            assert args == {}


class TestTrellisInit:
    """Tests for Trellis initialization."""

    def test_default_platform_is_server(self) -> None:
        """Default platform is SERVER."""
        with patch("sys.argv", ["app"]):
            app = Trellis()
            assert app.platform_type == PlatformType.SERVER

    @requires_pytauri
    def test_platform_from_constructor_string(self) -> None:
        """Platform can be set as string in constructor."""
        with patch("sys.argv", ["app"]):
            app = Trellis(platform="desktop")
            assert app.platform_type == PlatformType.DESKTOP

    def test_platform_from_constructor_enum(self) -> None:
        """Platform can be set as enum in constructor."""
        with patch("sys.argv", ["app"]):
            app = Trellis(platform=PlatformType.BROWSER)
            assert app.platform_type == PlatformType.BROWSER

    @requires_pytauri
    def test_constructor_overrides_cli(self) -> None:
        """Constructor platform takes precedence over CLI."""
        with patch("sys.argv", ["app", "--platform=server"]):
            app = Trellis(platform="desktop")
            assert app.platform_type == PlatformType.DESKTOP

    @requires_pytauri
    def test_cli_overrides_detection(self) -> None:
        """CLI platform takes precedence over auto-detection."""
        with patch("sys.argv", ["app", "--platform=desktop"]):
            app = Trellis()
            assert app.platform_type == PlatformType.DESKTOP

    def test_ignore_cli_flag(self) -> None:
        """ignore_cli=True ignores CLI arguments."""
        with patch("sys.argv", ["app", "--platform=desktop", "--port=9000"]):
            app = Trellis(ignore_cli=True)
            assert app.platform_type == PlatformType.SERVER

    def test_server_args_with_server_platform(self) -> None:
        """Server args are accepted with server platform."""
        with patch("sys.argv", ["app"]):
            app = Trellis(platform="server", host="0.0.0.0", port=8080)
            assert app.platform_type == PlatformType.SERVER

    @requires_pytauri
    def test_server_args_with_desktop_platform_raises(self) -> None:
        """Server args with desktop platform raises error."""
        with patch("sys.argv", ["app"]):
            with pytest.raises(PlatformArgumentError) as exc:
                Trellis(platform="desktop", host="0.0.0.0")
            assert "host" in str(exc.value)
            assert "desktop" in str(exc.value).lower()

    def test_desktop_args_with_server_platform_raises(self) -> None:
        """Desktop args with server platform raises error."""
        with patch("sys.argv", ["app"]):
            with pytest.raises(PlatformArgumentError) as exc:
                Trellis(platform="server", window_title="My App")
            assert "window_title" in str(exc.value)
            assert "server" in str(exc.value).lower()

    def test_cli_args_override_defaults(self) -> None:
        """CLI args override defaults but not constructor args."""
        with patch("sys.argv", ["app", "--port=9000"]):
            app = Trellis()
            assert app._args.get("port") == 9000

    def test_constructor_args_override_cli(self) -> None:
        """Constructor args take precedence over CLI args."""
        with patch("sys.argv", ["app", "--port=9000"]):
            app = Trellis(port=8080)
            assert app._args.get("port") == 8080
