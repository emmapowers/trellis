"""Build a desktop app bundle with PyInstaller."""

from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
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

    resolved = app_root / config.icon if not config.icon.is_absolute() else config.icon
    if resolved.exists():
        return resolved

    return None


def _discover_collect_all_packages() -> list[str]:
    """Return top-level package names for every installed distribution.

    Uses ``--collect-all`` instead of ``--hidden-import`` so that PyInstaller
    collects submodules, data files, *and* native extensions — not just the
    packages it can trace via static imports.  This eliminates whack-a-mole
    for packages that use dynamic loading (importlib.import_module,
    entry-points, native extensions loaded at runtime, etc.).

    Relies on the caller running inside the project's pixi env so only
    project dependencies (not dev tools) are visible.
    """
    seen: set[str] = set()
    for dist in importlib.metadata.distributions():
        top_level = dist.read_text("top_level.txt")
        if top_level:
            for line in top_level.strip().splitlines():
                pkg = line.strip()
                if pkg and pkg not in seen and "/" not in pkg:
                    seen.add(pkg)
        else:
            # Editable installs often lack top_level.txt.  Fall back to the
            # distribution name (normalised to a valid Python identifier).
            name = dist.metadata["Name"]
            if name:
                pkg = name.replace("-", "_").lower()
                if pkg not in seen:
                    seen.add(pkg)
    return sorted(seen)


def _write_bootstrap(config: Config, bootstrap_path: Path) -> None:
    """Write a small launcher script that runs the desktop app."""
    config_json = json.dumps(config.to_json())
    bootstrap_source = f"""from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

from trellis.app import AppLoader, set_apploader
from trellis.app.config import Config
from trellis.cli.run import _build_run_kwargs

APP_CONFIG_JSON = {config_json}


def _runtime_app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")).resolve()
    return Path(__file__).resolve().parent


def main() -> None:
    config = Config.from_json(APP_CONFIG_JSON)
    app_root = _runtime_app_root()
    apploader = AppLoader(app_root)
    apploader.config = config
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
    if platform.system() != "Darwin":
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
        "--add-data",
        f"{app_root / '.dist'}{os.pathsep}.dist",
        "--copy-metadata",
        "pytauri-wheel",
        "--name",
        config.name,
        "--distpath",
        str(resolved_output_dir),
        "--workpath",
        str(work_path),
        "--specpath",
        str(spec_path),
    ]

    # The app's own module is loaded via importlib.import_module() at
    # runtime, so PyInstaller can't trace it statically.
    command.extend(["--hidden-import", config.module])

    # Collect every installed Python package so PyInstaller picks up
    # submodules, data files, and native extensions.
    for pkg in _discover_collect_all_packages():
        command.extend(["--collect-all", pkg])

    # Ship trellis's own PyInstaller hooks (e.g. hook-rich.py).
    builtin_hooks = Path(__file__).parent / "hooks"
    if builtin_hooks.is_dir():
        command.extend(["--additional-hooks-dir", str(builtin_hooks)])

    # Projects can supply their own hooks/ directory too.
    project_hooks = app_root / "hooks"
    if project_hooks.is_dir():
        command.extend(["--additional-hooks-dir", str(project_hooks)])

    if config.collect_bundle_extras is not None:
        config.collect_bundle_extras(app_root, command)

    icon_path = _resolve_pyinstaller_icon(config, app_root)
    if icon_path is not None:
        command.extend(["--icon", str(icon_path)])

    command.append(str(bootstrap_path))
    subprocess.run(command, check=True, cwd=app_root)
    return resolved_output_dir / f"{config.name}.app"


__all__ = ["PackagePlatformError", "build_desktop_app_bundle"]
