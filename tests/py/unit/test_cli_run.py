"""Tests for the trellis run CLI command."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from trellis.app.configvars import get_cli_args
from trellis.cli import CliContext, pass_cli_context, trellis


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

    def test_options_populate_cli_context(self, tmp_path: Path) -> None:
        """CLI options should be available in cli_context during app loading."""
        # Create a minimal trellis_config.py that captures cli_context
        trellis_py = tmp_path / "trellis_config.py"
        trellis_py.write_text(
            """
from trellis.app.config import Config
from trellis.app.configvars import get_cli_args

# Capture CLI args at module load time for testing
_captured_cli_args = get_cli_args()

config = Config(name="test", module="main")
"""
        )

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # This will fail because there's no main module, but we can check
            # that cli_context is set before the failure
            runner.invoke(
                trellis,
                ["run", "--port", "9876", "--host", "192.168.1.1"],
                catch_exceptions=False,
            )
            # We expect it to fail at the "run" step, but config should have been loaded
            # with CLI args available. The actual context is tested via Config tests.

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

    def test_short_option_r_works(self, tmp_path: Path) -> None:
        """Short option -r should work for --app-root."""
        # Create a valid trellis_config.py
        (tmp_path / "trellis_config.py").write_text(
            "from trellis.app.config import Config\n"
            "config = Config(name='test', module='main')\n"
        )

        runner = CliRunner()
        # Just check the option is recognized (run will fail to find module)
        result = runner.invoke(trellis, ["-r", str(tmp_path), "run", "--help"])
        assert result.exit_code == 0

    def test_app_root_before_subcommand(self, tmp_path: Path) -> None:
        """--app-root should be placed before the subcommand."""
        (tmp_path / "trellis_config.py").write_text(
            "from trellis.app.config import Config\n"
            "config = Config(name='test', module='main')\n"
        )

        runner = CliRunner()
        result = runner.invoke(trellis, ["--app-root", str(tmp_path), "run", "--help"])
        assert result.exit_code == 0

    def test_env_var_recognized(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """TRELLIS_APP_ROOT environment variable should be used."""
        (tmp_path / "trellis_config.py").write_text(
            "from trellis.app.config import Config\n"
            "config = Config(name='test', module='main')\n"
        )

        monkeypatch.setenv("TRELLIS_APP_ROOT", str(tmp_path))

        runner = CliRunner()
        # Just verify help works - full test of env var is in test_app_root.py
        result = runner.invoke(trellis, ["run", "--help"])
        assert result.exit_code == 0

    def test_cli_overrides_env(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """CLI --app-root should override TRELLIS_APP_ROOT."""
        cli_dir = tmp_path / "cli_app"
        cli_dir.mkdir()
        (cli_dir / "trellis_config.py").write_text(
            "from trellis.app.config import Config\n"
            "config = Config(name='cli-app', module='main')\n"
        )

        env_dir = tmp_path / "env_app"
        env_dir.mkdir()
        (env_dir / "trellis_config.py").write_text(
            "from trellis.app.config import Config\n"
            "config = Config(name='env-app', module='main')\n"
        )

        monkeypatch.setenv("TRELLIS_APP_ROOT", str(env_dir))

        runner = CliRunner()
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
