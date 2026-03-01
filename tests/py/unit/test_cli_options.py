"""Tests for the configvar_options decorator."""

from __future__ import annotations

from pathlib import Path

import click
from click.testing import CliRunner

from trellis.app.configvars import ConfigVar
from trellis.cli.options import configvar_options, get_click_type
from trellis.platforms.common.base import PlatformType


class TestConfigvarOptionsDecorator:
    """Test basic decorator functionality."""

    def test_adds_click_option_for_configvar(self) -> None:
        """Decorator adds --port option for port ConfigVar."""
        port_var: ConfigVar[int | None] = ConfigVar(
            "port", default=None, type_hint=int, help="Server port"
        )

        @click.command()
        @configvar_options([port_var])
        def cmd(**kwargs: object) -> None:
            pass

        # Check that the option was added
        assert any(p.name == "port" for p in cmd.params)

    def test_adds_short_name_option(self) -> None:
        """Decorator adds -d for ConfigVar with short_name='d'."""
        debug_var: ConfigVar[str] = ConfigVar(
            "debug", default="", short_name="d", help="Debug mode"
        )

        @click.command()
        @configvar_options([debug_var])
        def cmd(**kwargs: object) -> None:
            pass

        # Find the debug param and check its opts
        debug_param = next(p for p in cmd.params if p.name == "debug")
        assert "-d" in debug_param.opts

    def test_preserves_function_signature(self) -> None:
        """Decorated function still callable."""
        port_var: ConfigVar[int | None] = ConfigVar("port", default=None, type_hint=int)

        @click.command()
        @configvar_options([port_var])
        def cmd(**kwargs: object) -> None:
            click.echo("executed")

        runner = CliRunner()
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "executed" in result.output


class TestTypeDerivation:
    """Test automatic Click type derivation from ConfigVar types."""

    def test_int_type_derived(self) -> None:
        """int ConfigVar -> Click int type."""
        var: ConfigVar[int] = ConfigVar("count", default=10)
        click_type = get_click_type(var)
        assert click_type is int

    def test_str_type_derived(self) -> None:
        """str ConfigVar -> Click str type."""
        var: ConfigVar[str] = ConfigVar("name", default="test")
        click_type = get_click_type(var)
        assert click_type is str

    def test_float_type_derived(self) -> None:
        """float ConfigVar -> Click float type."""
        var: ConfigVar[float] = ConfigVar("delay", default=1.0)
        click_type = get_click_type(var)
        assert click_type is float

    def test_path_type_derived(self) -> None:
        """Path ConfigVar -> click.Path type."""
        var: ConfigVar[Path | None] = ConfigVar("dir", default=None, type_hint=Path)
        click_type = get_click_type(var)
        assert isinstance(click_type, click.Path)
        converted = click_type.convert("/tmp/example", None, None)
        assert converted == Path("/tmp/example")
        assert isinstance(converted, Path)

    def test_strenum_becomes_choice(self) -> None:
        """StrEnum ConfigVar -> click.Choice with enum values."""
        var: ConfigVar[PlatformType] = ConfigVar("platform", default=PlatformType.SERVER)
        click_type = get_click_type(var)
        assert isinstance(click_type, click.Choice)
        assert set(click_type.choices) == {"server", "desktop", "browser"}

    def test_bool_flag_becomes_is_flag(self) -> None:
        """bool + is_flag=True -> is_flag=True."""
        var: ConfigVar[bool] = ConfigVar("watch", default=False, is_flag=True)
        # This is tested via the decorator behavior, not get_click_type
        # get_click_type returns None for flags (handled specially)
        click_type = get_click_type(var)
        assert click_type is None  # Flags don't have a type

    def test_bool_non_flag_becomes_option_pair(self) -> None:
        """bool + is_flag=False -> --option/--no-option."""
        var: ConfigVar[bool] = ConfigVar("hot_reload", default=True, is_flag=False)
        # This is tested via the decorator creating the right option format
        click_type = get_click_type(var)
        assert click_type is None  # Boolean options don't have a type


class TestHelpTextPropagation:
    """Test that help text propagates from ConfigVar to Click option."""

    def test_help_text_from_configvar(self) -> None:
        """ConfigVar help text appears in Click option."""
        var: ConfigVar[int | None] = ConfigVar(
            "port", default=None, type_hint=int, help="Server port to bind to"
        )

        @click.command()
        @configvar_options([var])
        def cmd(**kwargs: object) -> None:
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert "Server port to bind to" in result.output

    def test_empty_help_is_ok(self) -> None:
        """ConfigVar without help doesn't crash."""
        var: ConfigVar[int] = ConfigVar("port", default=8000)

        @click.command()
        @configvar_options([var])
        def cmd(**kwargs: object) -> None:
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert result.exit_code == 0


class TestNoneFiltering:
    """Test that None values are filtered from kwargs passed to the function."""

    def test_none_values_filtered_from_kwargs(self) -> None:
        """Unset options not passed to function."""
        var: ConfigVar[int | None] = ConfigVar("port", default=None, type_hint=int)
        received_kwargs: dict[str, object] = {}

        @click.command()
        @configvar_options([var])
        def cmd(**kwargs: object) -> None:
            received_kwargs.update(kwargs)

        runner = CliRunner()
        runner.invoke(cmd, [])
        assert "port" not in received_kwargs

    def test_explicit_values_passed(self) -> None:
        """Set options passed to function."""
        var: ConfigVar[int | None] = ConfigVar("port", default=None, type_hint=int)
        received_kwargs: dict[str, object] = {}

        @click.command()
        @configvar_options([var])
        def cmd(**kwargs: object) -> None:
            received_kwargs.update(kwargs)

        runner = CliRunner()
        runner.invoke(cmd, ["--port", "9000"])
        assert received_kwargs["port"] == 9000

    def test_false_not_filtered(self) -> None:
        """False values (not None) are passed through."""
        var: ConfigVar[bool] = ConfigVar(
            "hot_reload", default=True, is_flag=False, help="Enable hot reload"
        )
        received_kwargs: dict[str, object] = {}

        @click.command()
        @configvar_options([var])
        def cmd(**kwargs: object) -> None:
            received_kwargs.update(kwargs)

        runner = CliRunner()
        runner.invoke(cmd, ["--no-hot-reload"])
        assert received_kwargs["hot_reload"] is False

    def test_zero_not_filtered(self) -> None:
        """Zero values (not None) are passed through."""
        var: ConfigVar[int] = ConfigVar("count", default=10)
        received_kwargs: dict[str, object] = {}

        @click.command()
        @configvar_options([var])
        def cmd(**kwargs: object) -> None:
            received_kwargs.update(kwargs)

        runner = CliRunner()
        runner.invoke(cmd, ["--count", "0"])
        assert received_kwargs["count"] == 0


class TestDecoratorWithClickRunner:
    """Integration tests using Click's test runner."""

    def test_option_appears_in_help(self) -> None:
        """`--help` shows ConfigVar options."""
        var: ConfigVar[int | None] = ConfigVar(
            "port", default=None, type_hint=int, help="Server port"
        )

        @click.command()
        @configvar_options([var])
        def cmd(**kwargs: object) -> None:
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert "--port" in result.output
        assert "Server port" in result.output

    def test_option_value_received(self) -> None:
        """Running with --port 9000 passes port=9000."""
        var: ConfigVar[int | None] = ConfigVar("port", default=None, type_hint=int)
        received: dict[str, object] = {}

        @click.command()
        @configvar_options([var])
        def cmd(**kwargs: object) -> None:
            received.update(kwargs)

        runner = CliRunner()
        runner.invoke(cmd, ["--port", "9000"])
        assert received["port"] == 9000

    def test_path_option_value_received_as_path(self) -> None:
        """Path options should be passed as pathlib.Path values."""
        var: ConfigVar[Path | None] = ConfigVar("icon", default=None, type_hint=Path)
        received: dict[str, object] = {}

        @click.command()
        @configvar_options([var])
        def cmd(**kwargs: object) -> None:
            received.update(kwargs)

        runner = CliRunner()
        runner.invoke(cmd, ["--icon", "/tmp/icon.png"])
        assert received["icon"] == Path("/tmp/icon.png")
        assert isinstance(received["icon"], Path)

    def test_short_option_works(self) -> None:
        """Running with -d render passes debug='render'."""
        var: ConfigVar[str] = ConfigVar("debug", default="", short_name="d")
        received: dict[str, object] = {}

        @click.command()
        @configvar_options([var])
        def cmd(**kwargs: object) -> None:
            received.update(kwargs)

        runner = CliRunner()
        runner.invoke(cmd, ["-d", "render"])
        assert received["debug"] == "render"

    def test_choice_rejects_invalid(self) -> None:
        """Invalid enum value shows error."""
        var: ConfigVar[PlatformType] = ConfigVar("platform", default=PlatformType.SERVER)

        @click.command()
        @configvar_options([var])
        def cmd(**kwargs: object) -> None:
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--platform", "invalid"])
        assert result.exit_code != 0
        assert "invalid" in result.output.lower() or "choice" in result.output.lower()

    def test_flag_sets_true(self) -> None:
        """--watch sets watch=True."""
        var: ConfigVar[bool] = ConfigVar("watch", default=False, is_flag=True)
        received: dict[str, object] = {}

        @click.command()
        @configvar_options([var])
        def cmd(**kwargs: object) -> None:
            received.update(kwargs)

        runner = CliRunner()
        runner.invoke(cmd, ["--watch"])
        assert received["watch"] is True

    def test_boolean_option_negation(self) -> None:
        """--no-hot-reload sets hot_reload=False."""
        var: ConfigVar[bool] = ConfigVar("hot_reload", default=True, is_flag=False)
        received: dict[str, object] = {}

        @click.command()
        @configvar_options([var])
        def cmd(**kwargs: object) -> None:
            received.update(kwargs)

        runner = CliRunner()
        runner.invoke(cmd, ["--no-hot-reload"])
        assert received["hot_reload"] is False


class TestOptionGrouping:
    """Test option grouping by category."""

    def test_options_grouped_by_category(self) -> None:
        """Options appear under category headers in --help."""
        general_var: ConfigVar[str] = ConfigVar("name", default="app", help="App name")
        server_var: ConfigVar[int | None] = ConfigVar(
            "port", default=None, type_hint=int, category="server", help="Server port"
        )

        @click.command()
        @configvar_options([general_var, server_var])
        def cmd(**kwargs: object) -> None:
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        # Check that group headers appear
        assert "General Options" in result.output
        assert "Server Options" in result.output

    def test_general_category_for_no_category(self) -> None:
        """Vars without category go in General Options."""
        var: ConfigVar[str] = ConfigVar("name", default="app", help="App name")

        @click.command()
        @configvar_options([var])
        def cmd(**kwargs: object) -> None:
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert "General Options" in result.output

    def test_group_order_is_general_then_alphabetical(self) -> None:
        """General comes first, then server, desktop, etc. alphabetically."""
        general_var: ConfigVar[str] = ConfigVar("name", default="app")
        server_var: ConfigVar[str] = ConfigVar("host", default="localhost", category="server")
        desktop_var: ConfigVar[str] = ConfigVar("window_size", default="max", category="desktop")

        @click.command()
        @configvar_options([general_var, server_var, desktop_var])
        def cmd(**kwargs: object) -> None:
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])

        # Find positions
        general_pos = result.output.find("General Options")
        desktop_pos = result.output.find("Desktop Options")
        server_pos = result.output.find("Server Options")

        # General should be first, then alphabetically: desktop, server
        assert general_pos < desktop_pos < server_pos

    def test_hidden_vars_not_shown_in_help(self) -> None:
        """Hidden ConfigVars should not appear in --help output."""
        visible_var: ConfigVar[str] = ConfigVar("visible", default="yes", help="Visible option")
        hidden_var: ConfigVar[str] = ConfigVar(
            "hidden", default="no", help="Hidden option", hidden=True
        )

        # Filter out hidden vars as the run command would do
        cli_vars = [v for v in [visible_var, hidden_var] if not v.hidden]

        @click.command()
        @configvar_options(cli_vars)
        def cmd(**kwargs: object) -> None:
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert "--visible" in result.output
        assert "--hidden" not in result.output


class TestCornerCases:
    """Test edge cases and corner cases."""

    def test_empty_configvar_list(self) -> None:
        """Decorator handles no ConfigVars."""

        @click.command()
        @configvar_options([])
        def cmd() -> None:
            click.echo("works")

        runner = CliRunner()
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "works" in result.output

    def test_composable_with_click_argument(self) -> None:
        """Works with @click.argument."""
        var: ConfigVar[int | None] = ConfigVar("port", default=None, type_hint=int)

        @click.command()
        @click.argument("name")
        @configvar_options([var])
        def cmd(name: str, **kwargs: object) -> None:
            click.echo(f"name={name}")

        runner = CliRunner()
        result = runner.invoke(cmd, ["myapp"])
        assert result.exit_code == 0
        assert "name=myapp" in result.output

    def test_option_order_matches_configvar_order(self) -> None:
        """Help shows options in ConfigVar list order."""
        var1: ConfigVar[str] = ConfigVar("alpha", default="a")
        var2: ConfigVar[str] = ConfigVar("beta", default="b")
        var3: ConfigVar[str] = ConfigVar("gamma", default="c")

        @click.command()
        @configvar_options([var1, var2, var3])
        def cmd(**kwargs: object) -> None:
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        # Options should appear in the order they were passed to the decorator
        alpha_pos = result.output.find("--alpha")
        beta_pos = result.output.find("--beta")
        gamma_pos = result.output.find("--gamma")
        assert alpha_pos < beta_pos < gamma_pos

    def test_optional_type_hint_used(self) -> None:
        """ConfigVar(default=None, type_hint=int) works."""
        var: ConfigVar[int | None] = ConfigVar("port", default=None, type_hint=int)
        click_type = get_click_type(var)
        assert click_type is int

    def test_validator_not_called_at_cli_level(self) -> None:
        """Validators run at Config resolution, not CLI parsing."""

        def reject_all(value: int) -> int:
            raise ValueError("Should not be called")

        var: ConfigVar[int] = ConfigVar("port", default=8000, validator=reject_all)
        received: dict[str, object] = {}

        @click.command()
        @configvar_options([var])
        def cmd(**kwargs: object) -> None:
            received.update(kwargs)

        runner = CliRunner()
        # Should succeed - validator is not called at CLI level
        result = runner.invoke(cmd, ["--port", "9000"])
        assert result.exit_code == 0
        assert received["port"] == 9000
