"""Build a desktop app bundle with PyInstaller."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from trellis.platforms.common.base import PlatformType

if TYPE_CHECKING:
    from trellis.app.config import Config


class PackagePlatformError(RuntimeError):
    """Raised when packaging is requested on an unsupported platform."""


def _resolve_pyinstaller_icon(config: Config, app_root: Path) -> Path | None:
    """Pick the best icon for PyInstaller, preferring derived bundle icons."""
    if config.icon is None:
        return None

    derived_candidates = [
        app_root / ".dist" / "favicon.icns",
        app_root / ".dist" / "favicon.ico",
        app_root / ".dist" / "favicon.png",
    ]
    for candidate in derived_candidates:
        if candidate.exists():
            return candidate

    if config.icon.exists():
        return config.icon

    return None


def _write_bootstrap(config: Config, bootstrap_path: Path) -> None:
    """Write a small launcher script that runs the desktop app."""
    config_json = json.dumps(config.to_json())
    bootstrap_source = f"""from __future__ import annotations

import asyncio
from typing import Any

from trellis.app import AppLoader, set_apploader
from trellis.app.config import Config
from trellis.cli.run import _build_run_kwargs

APP_CONFIG_JSON = {config_json}


def main() -> None:
    config = Config.from_json(APP_CONFIG_JSON)
    apploader = AppLoader.from_config(config)
    apploader.load_app()
    set_apploader(apploader)
    app = apploader.app
    assert app is not None

    run_kwargs = _build_run_kwargs(config)

    def app_wrapper(_component: Any, system_theme: str, theme_mode: str | None) -> Any:
        return app.get_wrapped_top(system_theme, theme_mode)

    asyncio.run(apploader.platform.run(app.top, app_wrapper, **run_kwargs))


if __name__ == "__main__":
    main()
"""
    bootstrap_path.write_text(bootstrap_source)


def build_desktop_app_bundle(config: Config, app_root: Path, output_dir: Path | None) -> Path:
    """Build a desktop app bundle with PyInstaller.

    This is intentionally macOS-first and produces a ``.app`` bundle.
    """
    if config.platform != PlatformType.DESKTOP:
        raise ValueError("PyInstaller packaging is only supported for desktop platform")
    if sys.platform != "darwin":
        raise PackagePlatformError("PyInstaller packaging is currently supported on macOS only")

    pyinstaller_bin = shutil.which("pyinstaller")
    if pyinstaller_bin is None:
        raise RuntimeError("PyInstaller not found in PATH")

    package_workspace = app_root / ".workspace" / "package"
    package_workspace.mkdir(parents=True, exist_ok=True)
    bootstrap_path = package_workspace / "bootstrap.py"
    _write_bootstrap(config, bootstrap_path)

    resolved_output_dir = (output_dir or (app_root / "package")).resolve()
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    work_path = package_workspace / "build"
    spec_path = package_workspace / "spec"
    work_path.mkdir(parents=True, exist_ok=True)
    spec_path.mkdir(parents=True, exist_ok=True)

    command = [
        pyinstaller_bin,
        "--noconfirm",
        "--clean",
        "--windowed",
        "--onedir",
        "--paths",
        str(app_root),
        "--hidden-import",
        config.module,
        "--name",
        config.name,
        "--distpath",
        str(resolved_output_dir),
        "--workpath",
        str(work_path),
        "--specpath",
        str(spec_path),
        str(bootstrap_path),
    ]

    icon_path = _resolve_pyinstaller_icon(config, app_root)
    if icon_path is not None:
        command.extend(["--icon", str(icon_path)])

    subprocess.run(command, check=True, cwd=app_root)
    return resolved_output_dir / f"{config.name}.app"


__all__ = ["PackagePlatformError", "build_desktop_app_bundle"]
