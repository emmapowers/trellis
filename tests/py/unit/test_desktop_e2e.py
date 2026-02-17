"""Unit tests for desktop E2E harness configuration."""

from __future__ import annotations

import pytest

from trellis.platforms.desktop.e2e import (
    DesktopE2EConfig,
    DesktopE2EScenario,
    build_probe_script,
    load_desktop_e2e_config_from_env,
)

_EXPECTED_MARKDOWN_EXTERNAL_URLS = (
    "https://github.com/emmapowers/trellis",
    "https://github.com/emmapowers/trellis/",
)


def test_returns_none_when_no_scenario_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TRELLIS_DESKTOP_E2E_SCENARIO", raising=False)
    result = load_desktop_e2e_config_from_env()
    assert result is None


def test_loads_markdown_external_link_scenario(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRELLIS_DESKTOP_E2E_SCENARIO", "markdown_external_link")
    config = load_desktop_e2e_config_from_env()
    assert config == DesktopE2EConfig(
        scenario=DesktopE2EScenario.MARKDOWN_EXTERNAL_LINK,
        expected_external_urls=_EXPECTED_MARKDOWN_EXTERNAL_URLS,
    )


def test_loads_custom_timing_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRELLIS_DESKTOP_E2E_SCENARIO", "markdown_external_link")
    monkeypatch.setenv("TRELLIS_DESKTOP_E2E_TIMEOUT_SECONDS", "12.5")
    monkeypatch.setenv("TRELLIS_DESKTOP_E2E_INITIAL_DELAY_SECONDS", "1.75")

    config = load_desktop_e2e_config_from_env()

    assert config == DesktopE2EConfig(
        scenario=DesktopE2EScenario.MARKDOWN_EXTERNAL_LINK,
        timeout_seconds=12.5,
        initial_delay_seconds=1.75,
        expected_external_urls=_EXPECTED_MARKDOWN_EXTERNAL_URLS,
    )


def test_invalid_scenario_raises_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRELLIS_DESKTOP_E2E_SCENARIO", "not_a_real_scenario")
    with pytest.raises(ValueError, match="not_a_real_scenario"):
        load_desktop_e2e_config_from_env()


def test_markdown_probe_clicks_shadow_dom_anchor() -> None:
    config = DesktopE2EConfig(
        scenario=DesktopE2EScenario.MARKDOWN_EXTERNAL_LINK,
        expected_external_urls=_EXPECTED_MARKDOWN_EXTERNAL_URLS,
    )
    script = build_probe_script(config)
    assert "shadowRoot" in script
    assert "dispatchEvent" in script
    assert "Typography" in script


def test_markdown_scenario_includes_expected_external_urls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRELLIS_DESKTOP_E2E_SCENARIO", "markdown_external_link")

    config = load_desktop_e2e_config_from_env()

    assert config is not None
    assert config.expected_external_urls == _EXPECTED_MARKDOWN_EXTERNAL_URLS
