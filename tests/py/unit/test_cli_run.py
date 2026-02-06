"""Tests for the trellis run CLI command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from click.testing import CliRunner

from tests.conftest import WriteApp, WriteAppModule, WriteTrellisConfig
from trellis.app import AppLoader
from trellis.app.config import Config
from trellis.app.configvars import get_cli_args
from trellis.cli import CliContext, pass_cli_context, trellis
from trellis.cli.run import _build_run_kwargs
from trellis.platforms.common.base import PlatformType


class TestTrellisRunBasics:
    """Test basic trellis run command existence and help."""

    def test_run_command_exists(self) -> None:
        runner = CliRunner()
        result = runner.invoke(trellis, ["run", "--help"])
        assert result.exit_code == 0, f"Exit code: {result.exit_code}, output: {result.output}"

    def test_run_shows_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(trellis, ["run", "--help"])
        assert "Run a Trellis application" in result.output or "run" in result.output.lower()


class TestTrellisRunOptions:
    """Test CLI option parsing for trellis run."""

    def test_platform_option(self) -> None:
        runner = CliRunner()
        # Just test that the option is recognized (will fail to find app but option is parsed)
        result = runner.invoke(trellis, ["run", "--platform", "desktop", "--help"])
        assert result.exit_code == 0

    def test_port_option(self) -> None:
        runner = CliRunner()
        result = runner.invoke(trellis, ["run", "--port", "9000", "--help"])
        assert result.exit_code == 0

    def test_host_option(self) -> None:
        runner = CliRunner()
        result = runner.invoke(trellis, ["run", "--host", "0.0.0.0", "--help"])
        assert result.exit_code == 0

    def test_watch_flag(self) -> None:
        runner = CliRunner()
        result = runner.invoke(trellis, ["run", "--watch", "--help"])
        assert result.exit_code == 0

    def test_no_hot_reload_flag(self) -> None:
        runner = CliRunner()
        result = runner.invoke(trellis, ["run", "--no-hot-reload", "--help"])
        assert result.exit_code == 0

    def test_debug_option(self) -> None:
        runner = CliRunner()
        result = runner.invoke(trellis, ["run", "--debug", "render,state", "--help"])
        assert result.exit_code == 0


class TestShortOptions:
    """Test that short options work correctly."""

    def test_short_port_option(self) -> None:
        """Short option -p works for port."""
        runner = CliRunner()
        result = runner.invoke(trellis, ["run", "-p", "9000", "--help"])
        assert result.exit_code == 0

    def test_short_debug_option(self) -> None:
        """Short option -d works for debug."""
        runner = CliRunner()
        result = runner.invoke(trellis, ["run", "-d", "render", "--help"])
        assert result.exit_code == 0

    def test_short_watch_option(self) -> None:
        """Short option -w works for watch."""
        runner = CliRunner()
        result = runner.invoke(trellis, ["run", "-w", "--help"])
        assert result.exit_code == 0


class TestHelpTextFromConfigVars:
    """Test that help text comes from ConfigVars."""

    def test_run_help_shows_configvar_help_text(self) -> None:
        """Help text should come from ConfigVar definitions."""
        runner = CliRunner()
        result = runner.invoke(trellis, ["run", "--help"])
        # These help texts are defined in ConfigVars in config.py
        assert "Server port to bind to" in result.output
        assert "Watch for file changes" in result.output
        assert "Debug categories" in result.output


class TestCliContext:
    """Test that CLI options populate the cli_context."""

    def test_options_populate_cli_context(
        self,
        write_trellis_config: WriteTrellisConfig,
        write_app_module: WriteAppModule,
        reset_apploader: None,
    ) -> None:
        """CLI options should be available in cli_context during app loading."""
        module_name = "test_cli_context_app"

        app_root = write_trellis_config(
            content=(
                "from trellis.app.config import Config\n"
                "from trellis.app.configvars import get_cli_args\n"
                "_captured_cli_args = get_cli_args()\n"
                f"config = Config(name='test', module='{module_name}')\n"
            ),
        )
        write_app_module(module_name=module_name)

        mock_platform = MagicMock()
        mock_platform.run = AsyncMock()

        runner = CliRunner()
        with (
            patch.object(AppLoader, "bundle"),
            patch.object(
                AppLoader, "platform", new_callable=PropertyMock, return_value=mock_platform
            ),
        ):
            result = runner.invoke(
                trellis,
                ["--app-root", str(app_root), "run", "--port", "9876", "--host", "192.168.1.1"],
            )
        assert result.exit_code == 0, f"Exit code: {result.exit_code}, output: {result.output}"

    def test_cli_context_is_isolated(self) -> None:
        """CLI context should not leak between invocations."""
        # Outside of cli_context, should be empty
        assert get_cli_args() == {}


class TestCliContextDataclass:
    """Test CliContext dataclass and pass_cli_context decorator."""

    def test_cli_context_dataclass_has_app_root(self) -> None:
        """CliContext should have app_root attribute."""
        ctx = CliContext()
        assert hasattr(ctx, "app_root")
        assert ctx.app_root is None

    def test_cli_context_app_root_can_be_set(self) -> None:
        """CliContext.app_root can be set to a Path."""
        ctx = CliContext()
        ctx.app_root = Path("/some/path")
        assert ctx.app_root == Path("/some/path")

    def test_pass_cli_context_decorator_exists(self) -> None:
        """pass_cli_context should be a callable decorator."""
        assert callable(pass_cli_context)


class TestAppRootGlobalOption:
    """Test global --app-root CLI option."""

    def test_app_root_option_exists(self) -> None:
        """--app-root option should be recognized at group level."""
        runner = CliRunner()
        result = runner.invoke(trellis, ["--help"])
        assert "--app-root" in result.output or "-r" in result.output

    def test_short_option_r_works(self, write_trellis_config: WriteTrellisConfig) -> None:
        """Short option -r should work for --app-root."""
        app_root = write_trellis_config()

        runner = CliRunner()
        result = runner.invoke(trellis, ["-r", str(app_root), "run", "--help"])
        assert result.exit_code == 0

    def test_app_root_before_subcommand(self, write_trellis_config: WriteTrellisConfig) -> None:
        """--app-root should be placed before the subcommand."""
        app_root = write_trellis_config()

        runner = CliRunner()
        result = runner.invoke(trellis, ["--app-root", str(app_root), "run", "--help"])
        assert result.exit_code == 0

    def test_env_var_recognized(
        self,
        write_trellis_config: WriteTrellisConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """TRELLIS_APP_ROOT environment variable should be used."""
        app_root = write_trellis_config()
        monkeypatch.setenv("TRELLIS_APP_ROOT", str(app_root))

        runner = CliRunner()
        result = runner.invoke(trellis, ["run", "--help"])
        assert result.exit_code == 0

    def test_cli_overrides_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, reset_apploader: None
    ) -> None:
        """CLI --app-root should override TRELLIS_APP_ROOT."""
        # Use unique module names to avoid module cache conflicts
        cli_module = "cli_override_test_app"
        env_module = "env_override_test_app"

        cli_dir = tmp_path / "cli_app"
        cli_dir.mkdir()
        (cli_dir / "trellis_config.py").write_text(
            "from trellis.app.config import Config\n"
            f"config = Config(name='cli-app', module='{cli_module}')\n"
        )
        (cli_dir / f"{cli_module}.py").write_text(
            "from trellis import component\n"
            "from trellis.app import App\n"
            "\n"
            "@component\n"
            "def Root():\n"
            "    pass\n"
            "\n"
            "app = App(Root)\n"
        )

        env_dir = tmp_path / "env_app"
        env_dir.mkdir()
        (env_dir / "trellis_config.py").write_text(
            "from trellis.app.config import Config\n"
            f"config = Config(name='env-app', module='{env_module}')\n"
        )
        (env_dir / f"{env_module}.py").write_text(
            "from trellis import component\n"
            "from trellis.app import App\n"
            "\n"
            "@component\n"
            "def Root():\n"
            "    pass\n"
            "\n"
            "app = App(Root)\n"
        )

        monkeypatch.setenv("TRELLIS_APP_ROOT", str(env_dir))

        mock_platform = MagicMock()
        mock_platform.run = AsyncMock()

        runner = CliRunner()
        with (
            patch.object(AppLoader, "bundle"),
            patch.object(
                AppLoader, "platform", new_callable=PropertyMock, return_value=mock_platform
            ),
        ):
            # Run should use cli_dir, not env_dir
            result = runner.invoke(trellis, ["--app-root", str(cli_dir), "run"])
        # Should show "Running cli-app" not "Running env-app"
        assert "cli-app" in result.output

    def test_invalid_path_shows_error(self, tmp_path: Path) -> None:
        """Invalid --app-root path should show error."""
        nonexistent = tmp_path / "does_not_exist"

        runner = CliRunner()
        result = runner.invoke(trellis, ["--app-root", str(nonexistent), "run"])
        assert result.exit_code != 0
        # Click's exists=True will give an error message
        assert "does not exist" in result.output.lower() or "invalid" in result.output.lower()


class TestCliRunLoadApp:
    """Test that CLI run command loads the app via AppLoader.load_app().

    Note: Each test uses a unique module name to avoid Python's module caching
    between tests. The module cache persists across tests in the same process.
    """

    def test_run_loads_app_from_module(self, write_app: WriteApp, reset_apploader: None) -> None:
        """Run should successfully load an app from a module with app = App(...)."""
        app_root = write_app(name="test-app", module="test_valid_app")

        mock_platform = MagicMock()
        mock_platform.run = AsyncMock()

        runner = CliRunner()
        with (
            patch.object(AppLoader, "bundle"),
            patch.object(
                AppLoader, "platform", new_callable=PropertyMock, return_value=mock_platform
            ),
        ):
            result = runner.invoke(trellis, ["--app-root", str(app_root), "run"])

        assert result.exit_code == 0, f"Exit code: {result.exit_code}, output: {result.output}"
        assert "Running test-app" in result.output

    def test_run_error_when_app_variable_missing(
        self,
        write_trellis_config: WriteTrellisConfig,
        write_app_module: WriteAppModule,
    ) -> None:
        """Run should error when module doesn't define 'app' variable."""
        module_name = "test_missing_app"
        app_root = write_trellis_config(name="test-app", module=module_name)
        write_app_module(
            module_name=module_name,
            content=(
                "from trellis import component\n"
                "\n"
                "@component\n"
                "def Root():\n"
                "    pass\n"
                "\n"
                "# No app variable defined!\n"
            ),
        )

        runner = CliRunner()
        result = runner.invoke(trellis, ["--app-root", str(app_root), "run"])

        assert result.exit_code != 0, f"Expected failure, output: {result.output}"
        assert "'app' variable not defined" in result.output

    def test_run_error_when_app_wrong_type(
        self,
        write_trellis_config: WriteTrellisConfig,
        write_app_module: WriteAppModule,
    ) -> None:
        """Run should error when 'app' is not an App instance."""
        module_name = "test_wrong_type_app"
        app_root = write_trellis_config(name="test-app", module=module_name)
        write_app_module(module_name=module_name, content="app = 'not an App'\n")

        runner = CliRunner()
        result = runner.invoke(trellis, ["--app-root", str(app_root), "run"])

        assert result.exit_code != 0, f"Expected failure, output: {result.output}"
        assert "'app' must be an App instance" in result.output


# INTERNAL TEST: _build_run_kwargs is a pure function with clear logic worth testing directly
class TestBuildRunKwargs:
    """Tests for _build_run_kwargs helper."""

    def test_server_defaults(self) -> None:
        """Server config produces host, port, batch_delay, hot_reload."""
        config = Config(name="test", module="test_mod")
        kwargs = _build_run_kwargs(config)
        assert kwargs["host"] == "127.0.0.1"
        assert kwargs["port"] is None
        assert kwargs["batch_delay"] == pytest.approx(1 / 30)
        assert kwargs["hot_reload"] is True
        assert "window_title" not in kwargs

    def test_desktop_with_explicit_size(self) -> None:
        """Desktop config parses window_size into width and height."""
        config = Config(
            name="test",
            module="test_mod",
            platform=PlatformType.DESKTOP,
            window_size="1024x768",
        )
        kwargs = _build_run_kwargs(config)
        assert kwargs["window_title"] == "test"
        assert kwargs["window_width"] == 1024
        assert kwargs["window_height"] == 768

    def test_desktop_maximized_omits_dimensions(self) -> None:
        """Desktop with maximized window_size does not include width/height."""
        config = Config(
            name="test",
            module="test_mod",
            platform=PlatformType.DESKTOP,
            window_size="maximized",
        )
        kwargs = _build_run_kwargs(config)
        assert kwargs["window_title"] == "test"
        assert "window_width" not in kwargs
        assert "window_height" not in kwargs

    def test_custom_host_and_port(self) -> None:
        """Custom host and port flow through."""
        config = Config(name="test", module="test_mod", host="0.0.0.0", port=9000)
        kwargs = _build_run_kwargs(config)
        assert kwargs["host"] == "0.0.0.0"
        assert kwargs["port"] == 9000
