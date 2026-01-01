"""Unit tests for ClientState and theme functionality."""

import dataclasses

import pytest

from trellis.app import Browser, ClientState, DeviceType, OperatingSystem, ThemeMode, ThemeTokens


class TestClientStateTheme:
    """Tests for theme-related ClientState functionality."""

    def test_system_mode_follows_os_dark(self) -> None:
        """When mode is SYSTEM, resolved_theme should follow system_theme."""
        state = ClientState(theme_setting=ThemeMode.SYSTEM, system_theme=ThemeMode.DARK)
        assert state.theme == ThemeMode.DARK
        assert state.is_dark is True
        assert state.is_light is False

    def test_system_mode_follows_os_light(self) -> None:
        """When mode is SYSTEM and OS is light, resolved_theme is LIGHT."""
        state = ClientState(theme_setting=ThemeMode.SYSTEM, system_theme=ThemeMode.LIGHT)
        assert state.theme == ThemeMode.LIGHT
        assert state.is_dark is False
        assert state.is_light is True

    def test_explicit_dark_mode_ignores_system(self) -> None:
        """When mode is DARK, system_theme should be ignored."""
        state = ClientState(theme_setting=ThemeMode.DARK, system_theme=ThemeMode.LIGHT)
        assert state.theme == ThemeMode.DARK
        assert state.is_dark is True

    def test_explicit_light_mode_ignores_system(self) -> None:
        """When mode is LIGHT, system_theme should be ignored."""
        state = ClientState(theme_setting=ThemeMode.LIGHT, system_theme=ThemeMode.DARK)
        assert state.theme == ThemeMode.LIGHT
        assert state.is_light is True

    def test_handle_system_theme_change_to_dark(self) -> None:
        """handle_system_theme_change should update system_theme to dark."""
        state = ClientState(theme_setting=ThemeMode.SYSTEM, system_theme=ThemeMode.LIGHT)
        state.handle_system_theme_change("dark")
        assert state.system_theme == ThemeMode.DARK
        assert state.theme == ThemeMode.DARK

    def test_handle_system_theme_change_to_light(self) -> None:
        """handle_system_theme_change should update system_theme to light."""
        state = ClientState(theme_setting=ThemeMode.SYSTEM, system_theme=ThemeMode.DARK)
        state.handle_system_theme_change("light")
        assert state.system_theme == ThemeMode.LIGHT
        assert state.theme == ThemeMode.LIGHT

    def test_toggle_cycles_system_to_light(self) -> None:
        """toggle() should cycle SYSTEM -> LIGHT."""
        state = ClientState(theme_setting=ThemeMode.SYSTEM)
        state.toggle()
        assert state.theme_setting == ThemeMode.LIGHT

    def test_toggle_cycles_light_to_dark(self) -> None:
        """toggle() should cycle LIGHT -> DARK."""
        state = ClientState(theme_setting=ThemeMode.LIGHT)
        state.toggle()
        assert state.theme_setting == ThemeMode.DARK

    def test_toggle_cycles_dark_to_system(self) -> None:
        """toggle() should cycle DARK -> SYSTEM."""
        state = ClientState(theme_setting=ThemeMode.DARK)
        state.toggle()
        assert state.theme_setting == ThemeMode.SYSTEM

    def test_toggle_full_cycle(self) -> None:
        """toggle() should complete full cycle: SYSTEM -> LIGHT -> DARK -> SYSTEM."""
        state = ClientState(theme_setting=ThemeMode.SYSTEM)
        state.toggle()
        assert state.theme_setting == ThemeMode.LIGHT
        state.toggle()
        assert state.theme_setting == ThemeMode.DARK
        state.toggle()
        assert state.theme_setting == ThemeMode.SYSTEM

    def test_set_mode_with_string(self) -> None:
        """set_mode should accept string values."""
        state = ClientState()
        state.set_mode("dark")
        assert state.theme_setting == ThemeMode.DARK
        state.set_mode("light")
        assert state.theme_setting == ThemeMode.LIGHT
        state.set_mode("system")
        assert state.theme_setting == ThemeMode.SYSTEM

    def test_set_mode_with_enum(self) -> None:
        """set_mode should accept ThemeMode enum values."""
        state = ClientState()
        state.set_mode(ThemeMode.DARK)
        assert state.theme_setting == ThemeMode.DARK

    def test_set_mode_rejects_invalid_string(self) -> None:
        """set_mode should raise ValueError for invalid string values."""
        state = ClientState()
        with pytest.raises(ValueError, match=r"Invalid theme mode.*invalid"):
            state.set_mode("invalid")  # type: ignore

    def test_set_mode_rejects_case_sensitive_typo(self) -> None:
        """set_mode should raise ValueError for typos in mode names."""
        state = ClientState()
        with pytest.raises(ValueError, match=r"Invalid theme mode.*Dark"):
            state.set_mode("Dark")  # type: ignore  # Should be lowercase


class TestThemeTokens:
    """Tests for ThemeTokens dataclass."""

    def test_tokens_are_css_variables(self) -> None:
        """Theme tokens should be CSS variable references."""
        from trellis.app import theme

        assert theme.bg_page == "var(--trellis-bg-page)"
        assert theme.text_primary == "var(--trellis-text-primary)"
        assert theme.accent_primary == "var(--trellis-accent-primary)"

    def test_tokens_are_frozen(self) -> None:
        """Theme tokens should be immutable."""
        from trellis.app import theme

        with pytest.raises(dataclasses.FrozenInstanceError):
            theme.bg_page = "something else"  # type: ignore

    def test_all_tokens_have_css_variable_values(self) -> None:
        """All theme tokens should have CSS variable values."""
        tokens = ThemeTokens()
        for field in dataclasses.fields(tokens):
            value = getattr(tokens, field.name)
            assert value.startswith("var(--trellis-"), f"{field.name} should be a CSS var"


class TestClientStateDeviceInfo:
    """Tests for device info fields on ClientState."""

    def test_default_values(self) -> None:
        """ClientState should have sensible defaults."""
        state = ClientState()
        assert state.theme_setting == ThemeMode.SYSTEM
        assert state.system_theme == ThemeMode.LIGHT
        assert state.device_type.value == "unknown"
        assert state.os.value == "unknown"
        assert state.browser.value == "unknown"
        assert state.root_element_id == ""

    def test_device_info_preserved(self) -> None:
        """Device info fields should be preserved."""
        state = ClientState(
            device_type=DeviceType.WEB,
            os=OperatingSystem.MACOS,
            browser=Browser.CHROME,
            root_element_id="my-app",
        )
        assert state.device_type == DeviceType.WEB
        assert state.os == OperatingSystem.MACOS
        assert state.browser == Browser.CHROME
        assert state.root_element_id == "my-app"


class TestClientStateOutsideRenderContext:
    """Tests for ClientState behavior outside render context."""

    def test_from_context_outside_render_raises_runtime_error(self) -> None:
        """from_context() outside render context raises RuntimeError."""
        with pytest.raises(RuntimeError, match="outside of render context"):
            ClientState.from_context()
