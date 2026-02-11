"""Tests for ConfigVar configuration system."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

from trellis.app.configvars import (
    ConfigVar,
    _configvar_registry,
    cli_context,
    get_config_vars,
    validate_batch_delay,
    validate_debug_categories,
    validate_port_or_none,
    validate_positive_float,
    validate_positive_int,
    validate_window_size,
)
from trellis.platforms.common.base import PlatformType


class TestConfigVarBasics:
    """Test basic ConfigVar creation and default resolution."""

    def test_creates_with_name_and_default(self) -> None:
        var: ConfigVar[int] = ConfigVar("port", default=8000)
        assert var.name == "port"
        assert var.default == 8000

    def test_resolve_returns_default_when_no_sources(self) -> None:
        var: ConfigVar[str] = ConfigVar("host", default="localhost")
        assert var.resolve() == "localhost"

    def test_resolve_returns_none_for_optional_without_default(self) -> None:
        var: ConfigVar[int | None] = ConfigVar("port", default=None)
        assert var.resolve() is None


class TestConfigVarEnvResolution:
    """Test ConfigVar resolution from environment variables."""

    def test_reads_from_env_variable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRELLIS_HOST", "0.0.0.0")
        var: ConfigVar[str] = ConfigVar("host", default="localhost")
        assert var.resolve() == "0.0.0.0"

    def test_uses_custom_env_name(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MY_CUSTOM_VAR", "custom_value")
        var: ConfigVar[str] = ConfigVar("host", default="localhost", env_name="MY_CUSTOM_VAR")
        assert var.resolve() == "custom_value"

    def test_category_affects_env_name(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRELLIS_SERVER_HOST", "192.168.1.1")
        var: ConfigVar[str] = ConfigVar("host", default="localhost", category="server")
        assert var.resolve() == "192.168.1.1"

    def test_env_takes_precedence_over_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRELLIS_PORT", "9000")
        var: ConfigVar[int] = ConfigVar("port", default=8000)
        assert var.resolve() == 9000


class TestConfigVarCliResolution:
    """Test ConfigVar resolution from CLI context."""

    def test_reads_from_cli_context(self) -> None:
        var: ConfigVar[int] = ConfigVar("port", default=8000)
        with cli_context({"port": 9999}):
            assert var.resolve() == 9999

    def test_cli_takes_precedence_over_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRELLIS_PORT", "9000")
        var: ConfigVar[int] = ConfigVar("port", default=8000)
        with cli_context({"port": 7777}):
            assert var.resolve() == 7777

    def test_cli_takes_precedence_over_constructor_value(self) -> None:
        var: ConfigVar[int] = ConfigVar("port", default=8000)
        with cli_context({"port": 7777}):
            # Constructor value passed as argument, but CLI wins
            assert var.resolve(constructor_value=5555) == 7777

    def test_cli_none_falls_through_to_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRELLIS_PORT", "9000")
        var: ConfigVar[int] = ConfigVar("port", default=8000)
        # CLI context exists but port is None -> falls through to ENV
        with cli_context({"host": "0.0.0.0"}):
            assert var.resolve() == 9000

    def test_env_takes_precedence_over_constructor_value(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TRELLIS_PORT", "9000")
        var: ConfigVar[int] = ConfigVar("port", default=8000)
        # ENV wins over constructor value
        assert var.resolve(constructor_value=5555) == 9000


class TestConfigVarTypeCoercion:
    """Test automatic type coercion from ENV string values."""

    def test_coerces_int_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRELLIS_PORT", "8080")
        var: ConfigVar[int] = ConfigVar("port", default=8000)
        result = var.resolve()
        assert result == 8080
        assert isinstance(result, int)

    def test_coerces_float_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRELLIS_DELAY", "0.5")
        var: ConfigVar[float] = ConfigVar("delay", default=1.0)
        result = var.resolve()
        assert result == 0.5
        assert isinstance(result, float)

    @pytest.mark.parametrize("env_value", ["true", "True", "TRUE", "1", "yes", "Yes", "YES"])
    def test_coerces_bool_true_values(
        self, monkeypatch: pytest.MonkeyPatch, env_value: str
    ) -> None:
        monkeypatch.setenv("TRELLIS_WATCH", env_value)
        var: ConfigVar[bool] = ConfigVar("watch", default=False)
        assert var.resolve() is True

    @pytest.mark.parametrize("env_value", ["false", "False", "FALSE", "0", "no", "No", "NO"])
    def test_coerces_bool_false_values(
        self, monkeypatch: pytest.MonkeyPatch, env_value: str
    ) -> None:
        monkeypatch.setenv("TRELLIS_WATCH", env_value)
        var: ConfigVar[bool] = ConfigVar("watch", default=True)
        assert var.resolve() is False

    def test_coerces_path_from_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRELLIS_STATIC_DIR", "~/static")
        # Must provide type_hint when default is None and we need coercion
        var: ConfigVar[Path | None] = ConfigVar("static_dir", default=None, type_hint=Path)
        result = var.resolve()
        assert isinstance(result, Path)
        assert str(result) == str(Path.home() / "static")

    def test_coerces_strenum_from_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRELLIS_PLATFORM", "desktop")
        var: ConfigVar[PlatformType] = ConfigVar("platform", default=PlatformType.SERVER)
        result = var.resolve()
        assert result == PlatformType.DESKTOP
        assert isinstance(result, PlatformType)

    def test_invalid_int_raises_valueerror(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRELLIS_PORT", "not_a_number")
        var: ConfigVar[int] = ConfigVar("port", default=8000)
        with pytest.raises(ValueError, match="invalid literal"):
            var.resolve()

    def test_invalid_enum_raises_valueerror(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRELLIS_PLATFORM", "invalid_platform")
        var: ConfigVar[PlatformType] = ConfigVar("platform", default=PlatformType.SERVER)
        with pytest.raises(ValueError, match="is not a valid"):
            var.resolve()


class TestConfigVarValidation:
    """Test ConfigVar validation functions."""

    def test_validator_called_on_resolve(self) -> None:
        def double_it(value: int) -> int:
            return value * 2

        var: ConfigVar[int] = ConfigVar("value", default=10, validator=double_it)
        assert var.resolve() == 20

    def test_validator_can_transform_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def clamp_max(value: int) -> int:
            return min(value, 100)

        monkeypatch.setenv("TRELLIS_VALUE", "999")
        var: ConfigVar[int] = ConfigVar("value", default=50, validator=clamp_max)
        assert var.resolve() == 100

    def test_validator_error_propagates(self) -> None:
        def reject_all(value: int) -> int:
            raise ValueError("Always fails")

        var: ConfigVar[int] = ConfigVar("value", default=10, validator=reject_all)
        with pytest.raises(ValueError, match="Always fails"):
            var.resolve()


class TestPortValidation:
    """Test port number validation."""

    def test_valid_port_passes(self) -> None:
        assert validate_port_or_none(8080) == 8080
        assert validate_port_or_none(1) == 1
        assert validate_port_or_none(65535) == 65535

    def test_port_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="Port must be 1-65535"):
            validate_port_or_none(0)

    def test_port_over_65535_raises(self) -> None:
        with pytest.raises(ValueError, match="Port must be 1-65535"):
            validate_port_or_none(65536)

    def test_none_port_passes(self) -> None:
        assert validate_port_or_none(None) is None


class TestPositiveIntValidation:
    """Test positive integer validation."""

    def test_valid_positive_passes(self) -> None:
        assert validate_positive_int(1) == 1
        assert validate_positive_int(100) == 100

    def test_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            validate_positive_int(0)

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            validate_positive_int(-5)


class TestPositiveFloatValidation:
    """Test positive float validation."""

    def test_valid_positive_passes(self) -> None:
        assert validate_positive_float(0.001) == 0.001
        assert validate_positive_float(1.5) == 1.5

    def test_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            validate_positive_float(0.0)

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            validate_positive_float(-0.5)


class TestDebugCategoriesValidation:
    """Test debug categories validation."""

    @pytest.mark.parametrize(
        "value",
        ["render", "render,state", "all", ""],
    )
    def test_valid_categories_pass(self, value: str) -> None:
        # Should not raise
        result = validate_debug_categories(value)
        assert isinstance(result, str)

    def test_invalid_category_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown debug categor"):
            validate_debug_categories("invalid_category")


class TestConfigVarEdgeCases:
    """Test edge cases and string handling."""

    def test_empty_env_treated_as_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRELLIS_HOST", "")
        var: ConfigVar[str] = ConfigVar("host", default="localhost")
        # Empty string should fall through to default
        assert var.resolve() == "localhost"

    def test_whitespace_stripped_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRELLIS_PORT", "  8080  ")
        var: ConfigVar[int] = ConfigVar("port", default=8000)
        assert var.resolve() == 8080

    def test_enum_case_insensitive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRELLIS_PLATFORM", "DESKTOP")
        var: ConfigVar[PlatformType] = ConfigVar("platform", default=PlatformType.SERVER)
        assert var.resolve() == PlatformType.DESKTOP

    def test_nested_cli_context_inner_wins(self) -> None:
        var: ConfigVar[int] = ConfigVar("port", default=8000)
        with cli_context({"port": 9000}):
            assert var.resolve() == 9000
            with cli_context({"port": 7000}):
                assert var.resolve() == 7000
            # Back to outer context
            assert var.resolve() == 9000


class TestDebugCategoriesEdgeCases:
    """Test debug category edge cases."""

    def test_strips_whitespace_from_categories(self) -> None:
        result = validate_debug_categories(" render , state ")
        # Should strip whitespace and still validate
        assert "render" in result
        assert "state" in result

    def test_deduplicates_categories(self) -> None:
        result = validate_debug_categories("render,render,state")
        # Count occurrences of render - should be deduplicated
        assert result.count("render") == 1

    def test_empty_string_returns_empty(self) -> None:
        assert validate_debug_categories("") == ""


class TestBatchDelayValidation:
    """Test batch delay validation bounds."""

    def test_valid_batch_delay_passes(self) -> None:
        assert validate_batch_delay(0.001) == 0.001
        assert validate_batch_delay(1 / 30) == pytest.approx(1 / 30)
        assert validate_batch_delay(10.0) == 10.0

    def test_batch_delay_below_min_raises(self) -> None:
        with pytest.raises(ValueError, match="batch_delay must be"):
            validate_batch_delay(0.0001)

    def test_batch_delay_above_max_raises(self) -> None:
        with pytest.raises(ValueError, match="batch_delay must be"):
            validate_batch_delay(11.0)


class TestValidateWindowSize:
    """Test window size validation."""

    def test_maximized_valid(self) -> None:
        assert validate_window_size("maximized") == "maximized"

    def test_maximized_case_insensitive(self) -> None:
        assert validate_window_size("MAXIMIZED") == "maximized"
        assert validate_window_size("Maximized") == "maximized"

    def test_dimension_format_valid(self) -> None:
        assert validate_window_size("1024x768") == "1024x768"
        assert validate_window_size("1920x1080") == "1920x1080"

    def test_dimension_format_normalized(self) -> None:
        assert validate_window_size(" 1024 x 768 ") == "1024x768"
        assert validate_window_size("1024X768") == "1024x768"

    def test_invalid_format_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid window size"):
            validate_window_size("invalid")
        with pytest.raises(ValueError, match="Invalid window size"):
            validate_window_size("1024")
        with pytest.raises(ValueError, match="Invalid window size"):
            validate_window_size("1024x")

    def test_negative_dimensions_rejected(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            validate_window_size("-100x768")
        with pytest.raises(ValueError, match="must be positive"):
            validate_window_size("1024x-768")

    def test_zero_dimensions_rejected(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            validate_window_size("0x768")
        with pytest.raises(ValueError, match="must be positive"):
            validate_window_size("1024x0")


class TestConfigVarRegistry:
    """Test ConfigVar auto-registration."""

    @pytest.fixture(autouse=True)
    def _restore_registry(self) -> Generator[None]:
        """Snapshot and restore _configvar_registry so tests don't leak state."""
        registry_backup = list(_configvar_registry)
        yield
        _configvar_registry.clear()
        _configvar_registry.extend(registry_backup)

    def test_configvar_auto_registers(self) -> None:
        """ConfigVar constructor adds to registry."""
        # Get current count
        initial_count = len(_configvar_registry)

        # Create a new ConfigVar
        var: ConfigVar[str] = ConfigVar("test_auto_reg", default="value")

        # Should be in registry
        assert var in _configvar_registry
        assert len(_configvar_registry) == initial_count + 1

        # get_config_vars should return it
        all_vars = get_config_vars()
        assert var in all_vars

    def test_get_config_vars_returns_all(self) -> None:
        """get_config_vars() returns all registered vars."""
        # Get all vars
        all_vars = get_config_vars()

        # Should match registry
        assert len(all_vars) == len(_configvar_registry)
        for var in _configvar_registry:
            assert var in all_vars

    def test_get_config_vars_returns_copy(self) -> None:
        """get_config_vars() returns a copy, not the actual registry."""
        all_vars = get_config_vars()
        initial_registry_len = len(_configvar_registry)

        # Modifying returned list should not affect registry
        all_vars.clear()
        assert len(_configvar_registry) == initial_registry_len

    def test_hidden_default_is_false(self) -> None:
        """ConfigVar hidden defaults to False."""
        var: ConfigVar[int] = ConfigVar("test_hidden_default", default=42)
        assert var.hidden is False

    def test_hidden_can_be_set_true(self) -> None:
        """ConfigVar hidden can be set to True."""
        var: ConfigVar[int] = ConfigVar("test_hidden_true", default=42, hidden=True)
        assert var.hidden is True


class TestConfigVarListCoercion:
    """Test ConfigVar coercion of list types from ENV string values."""

    def test_coerces_list_of_paths_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """list[Path] ConfigVar splits comma-separated string and coerces each element."""
        monkeypatch.setenv("TRELLIS_PATHS", "src,lib")
        var: ConfigVar[list[Path]] = ConfigVar("paths", default=[Path(".")], type_hint=list[Path])
        result = var.resolve()
        assert result == [Path("src"), Path("lib")]

    def test_coerces_list_of_strings_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """list[str] ConfigVar splits comma-separated string."""
        monkeypatch.setenv("TRELLIS_TAGS", "alpha,beta,gamma")
        var: ConfigVar[list[str]] = ConfigVar("tags", default=["default"], type_hint=list[str])
        result = var.resolve()
        assert result == ["alpha", "beta", "gamma"]

    def test_list_strips_whitespace_from_elements(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """list coercion strips whitespace from each element."""
        monkeypatch.setenv("TRELLIS_PATHS", " src , lib ")
        var: ConfigVar[list[Path]] = ConfigVar("paths", default=[Path(".")], type_hint=list[Path])
        result = var.resolve()
        assert result == [Path("src"), Path("lib")]

    def test_list_returns_default_when_env_not_set(self) -> None:
        """list ConfigVar returns default when no ENV set."""
        var: ConfigVar[list[Path]] = ConfigVar("paths", default=[Path(".")], type_hint=list[Path])
        result = var.resolve()
        assert result == [Path(".")]

    def test_list_expands_user_in_paths(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """list[Path] expands ~ in path elements."""
        monkeypatch.setenv("TRELLIS_PATHS", "~/src,lib")
        var: ConfigVar[list[Path]] = ConfigVar("paths", default=[Path(".")], type_hint=list[Path])
        result = var.resolve()
        assert result[0] == Path.home() / "src"
        assert result[1] == Path("lib")


class TestConfigVarCliMetadata:
    """Test CLI-specific metadata fields on ConfigVar."""

    def test_default_cli_metadata(self) -> None:
        """Default values: short_name=None, is_flag=False."""
        var: ConfigVar[int] = ConfigVar("port", default=8000)
        assert var.short_name is None
        assert var.is_flag is False

    def test_short_name_stored(self) -> None:
        """ConfigVar stores short_name."""
        var: ConfigVar[str] = ConfigVar("debug", default="", short_name="d")
        assert var.short_name == "d"

    def test_is_flag_stored(self) -> None:
        """ConfigVar stores is_flag=True."""
        var: ConfigVar[bool] = ConfigVar("watch", default=False, is_flag=True)
        assert var.is_flag is True

    def test_get_cli_short_name_returns_formatted(self) -> None:
        """get_cli_short_name() returns '-d' for short_name='d'."""
        var: ConfigVar[str] = ConfigVar("debug", default="", short_name="d")
        assert var.get_cli_short_name() == "-d"

    def test_get_cli_short_name_returns_none_when_not_set(self) -> None:
        """get_cli_short_name() returns None when short_name=None."""
        var: ConfigVar[int] = ConfigVar("port", default=8000)
        assert var.get_cli_short_name() is None
