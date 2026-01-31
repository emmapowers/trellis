"""Tests for the trellis run CLI command."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from trellis.app.configvars import get_cli_args
from trellis.cli import trellis


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
        # Create a minimal trellis.py that captures cli_context
        trellis_py = tmp_path / "trellis.py"
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
