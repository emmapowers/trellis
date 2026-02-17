"""Desktop E2E harness configuration and scripted probes."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum

_DEFAULT_TIMEOUT_SECONDS = 8.0
_DEFAULT_INITIAL_DELAY_SECONDS = 0.8
_MARKDOWN_EXTERNAL_LINK_EXPECTED_URLS = (
    "https://github.com/emmapowers/trellis",
    "https://github.com/emmapowers/trellis/",
)


class DesktopE2EScenario(StrEnum):
    """Supported desktop E2E scenarios."""

    MARKDOWN_EXTERNAL_LINK = "markdown_external_link"


@dataclass(frozen=True, slots=True)
class DesktopE2EConfig:
    """Desktop E2E harness configuration loaded from environment."""

    scenario: DesktopE2EScenario
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS
    initial_delay_seconds: float = _DEFAULT_INITIAL_DELAY_SECONDS
    expected_external_urls: tuple[str, ...] = ()


def load_desktop_e2e_config_from_env() -> DesktopE2EConfig | None:
    """Load desktop E2E configuration from process environment.

    Returns None when no scenario is configured.
    """
    scenario_value = os.environ.get("TRELLIS_DESKTOP_E2E_SCENARIO")
    if not scenario_value:
        return None

    scenario = DesktopE2EScenario(scenario_value)
    timeout_seconds = _read_float_env(
        "TRELLIS_DESKTOP_E2E_TIMEOUT_SECONDS", _DEFAULT_TIMEOUT_SECONDS
    )
    initial_delay_seconds = _read_float_env(
        "TRELLIS_DESKTOP_E2E_INITIAL_DELAY_SECONDS", _DEFAULT_INITIAL_DELAY_SECONDS
    )
    return DesktopE2EConfig(
        scenario=scenario,
        timeout_seconds=timeout_seconds,
        initial_delay_seconds=initial_delay_seconds,
        expected_external_urls=_MARKDOWN_EXTERNAL_LINK_EXPECTED_URLS,
    )


def build_probe_script(config: DesktopE2EConfig) -> str:
    """Build JavaScript probe for the configured scenario."""
    if config.scenario == DesktopE2EScenario.MARKDOWN_EXTERNAL_LINK:
        return _MARKDOWN_EXTERNAL_LINK_PROBE
    raise ValueError(f"Unsupported desktop E2E scenario: {config.scenario}")


def _read_float_env(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None:
        return default
    return float(value)


_MARKDOWN_EXTERNAL_LINK_PROBE = """\
(() => {
  const clickMarkdownLink = () => {
    const typographyButton = Array.from(document.querySelectorAll("button")).find(
      (button) => button.textContent?.trim() === "Typography"
    );
    if (!(typographyButton instanceof HTMLButtonElement)) {
      return false;
    }
    typographyButton.click();

    const markdownHost = document.querySelector("[data-testid='markdown-host']");
    const markdownRoot = markdownHost && markdownHost.shadowRoot;
    if (!markdownRoot) {
      return false;
    }

    const anchor = markdownRoot.querySelector("a[href]");
    if (!(anchor instanceof HTMLAnchorElement)) {
      return false;
    }

    anchor.dispatchEvent(
      new MouseEvent("click", {
        bubbles: true,
        cancelable: true,
        composed: true,
        button: 0,
      })
    );
    return true;
  };

  let attempts = 0;
  const interval = window.setInterval(() => {
    attempts += 1;
    if (clickMarkdownLink() || attempts > 120) {
      window.clearInterval(interval);
    }
  }, 50);
})();
"""
