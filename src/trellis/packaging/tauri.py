"""Build a desktop app bundle with Tauri."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import jinja2

from trellis.toolchain import ensure_python_standalone, ensure_rustup, ensure_tauri_cli
from trellis.toolchain.rustup import RustToolchain

if TYPE_CHECKING:
    from trellis.app.config import Config

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _parse_window_size(window_size: str) -> tuple[int, int]:
    """Parse window size string into (width, height). Defaults to 1024x768 for 'maximized'."""
    if window_size == "maximized":
        return 1024, 768
    parts = window_size.split("x")
    return int(parts[0]), int(parts[1])


def generate_tauri_scaffold(*, scaffold_dir: Path, config: Config, dist_path: Path) -> None:
    """Generate the Tauri project scaffold from templates.

    Creates Cargo.toml, tauri.conf.json, Rust source files, and capabilities
    configuration in scaffold_dir.
    """
    scaffold_dir.mkdir(parents=True, exist_ok=True)
    (scaffold_dir / "src").mkdir(parents=True, exist_ok=True)
    (scaffold_dir / "capabilities").mkdir(parents=True, exist_ok=True)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(_TEMPLATES_DIR)),
        keep_trailing_newline=True,
    )

    identifier = config.identifier or f"com.trellis.{config.name}"
    version = config.version or "0.1.0"
    window_width, window_height = _parse_window_size(config.window_size)

    template_vars = {
        "name": config.name,
        "product_name": config.title or config.name,
        "version": version,
        "identifier": identifier,
        "module": config.module,
        "window_title": config.title or config.name,
        "window_width": window_width,
        "window_height": window_height,
        "update_url": config.update_url,
        "update_pubkey": config.update_pubkey or "",
    }

    file_map = {
        "Cargo.toml.j2": "Cargo.toml",
        "tauri.conf.json.j2": "tauri.conf.json",
        "lib.rs.j2": "src/lib.rs",
        "main.rs.j2": "src/main.rs",
        "build.rs.j2": "build.rs",
        "capabilities_default.json.j2": "capabilities/default.json",
    }

    for template_name, output_name in file_map.items():
        template = env.get_template(template_name)
        content = template.render(**template_vars)
        (scaffold_dir / output_name).write_text(content)

    # Symlink dist directory so Tauri can find frontend assets
    dist_link = scaffold_dir / "dist"
    if dist_link.exists() or dist_link.is_symlink():
        dist_link.unlink()
    dist_link.symlink_to(dist_path.resolve())


def install_app_into_portable_python(
    *, python_bin: Path, app_root: Path, pyembed_dir: Path
) -> None:
    """Install the Trellis app into the portable Python environment.

    Uses pip to install the app and its dependencies into the standalone
    Python, then copies the installation into pyembed_dir for bundling.
    """
    pyembed_dir.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [str(python_bin), "-m", "pip", "install", "--no-warn-script-location", str(app_root)],
        check=True,
    )

    # Copy the entire Python installation into pyembed for bundling
    python_base = python_bin.parent.parent  # bin/python3 -> install dir
    if python_base.name == "install":
        src_dir = python_base
    else:
        src_dir = python_base

    if pyembed_dir.exists():
        shutil.rmtree(pyembed_dir)
    shutil.copytree(src_dir, pyembed_dir)


def run_tauri_build(*, tauri_cli: Path, rust: RustToolchain, scaffold_dir: Path) -> Path:
    """Run the Tauri build process.

    Args:
        tauri_cli: Path to the cargo-tauri binary
        rust: RustToolchain with environment configuration
        scaffold_dir: Path to the generated Tauri scaffold

    Returns:
        Path to the build output directory
    """
    env = {
        **os.environ,
        **rust.env(),
        "PYTAURI_STANDALONE": "1",
    }

    subprocess.run(
        [str(tauri_cli), "build"],
        check=True,
        cwd=scaffold_dir,
        env=env,
    )

    # Tauri outputs bundles to target/release/bundle/
    return scaffold_dir / "target" / "release" / "bundle"


def build_desktop_app_bundle(config: Config, app_root: Path, output_dir: Path | None) -> Path:
    """Build a desktop app bundle with Tauri.

    Orchestrates the full packaging pipeline:
    1. Ensure Rust toolchain is available
    2. Ensure Tauri CLI is available
    3. Ensure portable Python is available
    4. Generate Tauri project scaffold
    5. Install app into portable Python
    6. Run Tauri build

    Args:
        config: Application configuration
        app_root: Path to the application root directory
        output_dir: Custom output directory (unused — Tauri controls output location)

    Returns:
        Path to the build output directory
    """
    # 1. Ensure toolchains
    rust = ensure_rustup()
    tauri_cli = ensure_tauri_cli(rust)
    python_standalone = ensure_python_standalone()

    # 2. Generate scaffold
    build_dir = app_root / ".trellis-build"
    scaffold_dir = build_dir / "src-tauri"
    dist_path = app_root / ".dist"

    generate_tauri_scaffold(
        scaffold_dir=scaffold_dir,
        config=config,
        dist_path=dist_path,
    )

    # 3. Install app into portable Python
    pyembed_dir = scaffold_dir / "pyembed"
    install_app_into_portable_python(
        python_bin=python_standalone.python_bin,
        app_root=app_root,
        pyembed_dir=pyembed_dir,
    )

    # 4. Run Tauri build
    return run_tauri_build(
        tauri_cli=tauri_cli,
        rust=rust,
        scaffold_dir=scaffold_dir,
    )


__all__ = [
    "build_desktop_app_bundle",
    "generate_tauri_scaffold",
    "install_app_into_portable_python",
    "run_tauri_build",
]
