"""Build a desktop app bundle with Tauri."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import jinja2

from trellis.toolchain import ensure_python_standalone, ensure_rustup, ensure_tauri_cli
from trellis.toolchain.rustup import RustToolchain

if TYPE_CHECKING:
    from trellis.app.config import Config

from PIL import Image

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _generate_default_icon(path: Path) -> None:
    """Generate a simple default 512x512 icon PNG."""
    img = Image.new("RGBA", (512, 512), (46, 125, 50, 255))
    img.save(path, "PNG")


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

    raw_slug = re.sub(r"[^a-z0-9-]", "-", config.name.lower()).strip("-")
    identifier = config.identifier or f"com.trellis.{raw_slug}"
    version = config.version or "0.1.0"
    window_width, window_height = _parse_window_size(config.window_size)

    # Cargo package names: lowercase, alphanumeric/hyphens/underscores only
    cargo_name = re.sub(r"[^a-z0-9_-]", "-", config.name.lower())
    cargo_name = re.sub(r"-+", "-", cargo_name).strip("-")

    template_vars = {
        "name": cargo_name,
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

    # Populate icons directory from bundler output or config source icon
    icons_dir = scaffold_dir / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)

    _ICON_MAP = {
        "favicon.icns": "icon.icns",
        "favicon.ico": "icon.ico",
        "favicon.png": "icon.png",
    }
    has_bundler_icons = False
    for src_name, dest_name in _ICON_MAP.items():
        src = dist_path / src_name
        if src.exists():
            shutil.copy2(src, icons_dir / dest_name)
            has_bundler_icons = True

    # Generate a full-size icon.png from the source icon (bundler's favicon.png is 32x32)
    if config.icon and config.icon.exists():
        img = Image.open(config.icon).convert("RGBA")
        img = img.resize((512, 512), Image.Resampling.LANCZOS)
        img.save(str(icons_dir / "icon.png"), "PNG")
    elif not has_bundler_icons:
        _generate_default_icon(icons_dir / "icon.png")


def install_app_into_portable_python(
    *, python_bin: Path, app_root: Path, pyembed_dir: Path
) -> None:
    """Install the Trellis app into the portable Python environment.

    Uses pip to install the app and its dependencies into the standalone
    Python, then copies the installation into pyembed_dir for bundling.
    """
    pyembed_dir.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            str(python_bin),
            "-m",
            "pip",
            "install",
            "--no-warn-script-location",
            "--no-cache-dir",
            str(app_root),
            "pytauri-wheel>=0.8.0",
        ],
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


def _patch_libpython_install_name(pyembed_dir: Path) -> None:
    """Patch libpython's install_name on macOS to use @rpath.

    python-build-standalone ships libpython with an absolute install_name.
    Without @rpath in the dylib's install_name, the RPATH set on the
    executable is ignored by dyld.
    """
    if sys.platform != "darwin":
        return

    lib_dir = pyembed_dir / "lib"
    for dylib in lib_dir.glob("libpython*.dylib"):
        if dylib.is_symlink():
            continue
        subprocess.run(
            ["install_name_tool", "-id", f"@rpath/{dylib.name}", str(dylib)],
            check=True,
        )


def _get_rustflags(pyembed_dir: Path) -> str:
    """Get RUSTFLAGS for linking against the embedded Python."""
    lib_dir = pyembed_dir / "lib"
    flags = f"-L {lib_dir}"

    if sys.platform == "darwin":
        flags += " -C link-arg=-Wl,-rpath,@executable_path/../Resources/pyembed/lib"
    elif sys.platform == "linux":
        flags += " -C link-arg=-Wl,-rpath,$ORIGIN/pyembed/lib"

    return flags


def _get_pyo3_python(pyembed_dir: Path) -> Path:
    """Get the path to the Python binary in pyembed."""
    if sys.platform == "win32":
        return pyembed_dir / "python.exe"
    return pyembed_dir / "bin" / "python3"


def run_tauri_build(
    *,
    tauri_cli: Path,
    rust: RustToolchain,
    scaffold_dir: Path,
    pyembed_dir: Path,
    bundles: list[str] | None = None,
) -> Path:
    """Run the Tauri build process.

    Args:
        tauri_cli: Path to the cargo-tauri binary
        rust: RustToolchain with environment configuration
        scaffold_dir: Path to the generated Tauri scaffold
        pyembed_dir: Path to the embedded Python directory
        bundles: Bundle types to build (default: ["app"])

    Returns:
        Path to the build output directory
    """
    if bundles is None:
        bundles = ["app"]

    _patch_libpython_install_name(pyembed_dir)

    env = {
        **os.environ,
        **rust.env(),
        "PYTAURI_STANDALONE": "1",
        "PYO3_PYTHON": str(_get_pyo3_python(pyembed_dir)),
        "RUSTFLAGS": _get_rustflags(pyembed_dir),
    }

    subprocess.run(
        [str(tauri_cli), "build", "--bundles", *bundles],
        check=True,
        cwd=scaffold_dir,
        env=env,
    )

    # Tauri outputs bundles to target/release/bundle/
    return scaffold_dir / "target" / "release" / "bundle"


def _copy_build_output(*, bundle_dir: Path, output_dir: Path, platform: str) -> None:
    """Copy build artifacts from Tauri's bundle directory to output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)

    if platform == "darwin":
        macos_dir = bundle_dir / "macos"
        if macos_dir.exists():
            for app in macos_dir.glob("*.app"):
                dest = output_dir / app.name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(app, dest)
        dmg_dir = bundle_dir / "dmg"
        if dmg_dir.exists():
            for dmg in dmg_dir.glob("*.dmg"):
                shutil.copy2(dmg, output_dir / dmg.name)
    elif platform == "win32":
        nsis_dir = bundle_dir / "nsis"
        if nsis_dir.exists():
            for exe in nsis_dir.glob("*.exe"):
                shutil.copy2(exe, output_dir / exe.name)
    elif platform == "linux":
        deb_dir = bundle_dir / "deb"
        if deb_dir.exists():
            for deb in deb_dir.glob("*.deb"):
                shutil.copy2(deb, output_dir / deb.name)


def build_desktop_app_bundle(
    config: Config,
    app_root: Path,
    output_dir: Path | None,
    bundles: list[str] | None = None,
) -> Path:
    """Build a desktop app bundle with Tauri.

    Orchestrates the full packaging pipeline:
    1. Ensure Rust toolchain is available
    2. Ensure Tauri CLI is available
    3. Ensure portable Python is available
    4. Generate Tauri project scaffold
    5. Install app into portable Python
    6. Run Tauri build
    7. Copy output to destination directory

    Args:
        config: Application configuration
        app_root: Path to the application root directory
        output_dir: Custom output directory (default: app_root / "dist")
        bundles: Bundle types to build (default: ["app"])

    Returns:
        Path to the output directory containing the built artifacts
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
    bundle_dir = run_tauri_build(
        tauri_cli=tauri_cli,
        rust=rust,
        scaffold_dir=scaffold_dir,
        pyembed_dir=pyembed_dir,
        bundles=bundles,
    )

    # 5. Copy output to destination
    dest = output_dir or (app_root / "dist")
    _copy_build_output(bundle_dir=bundle_dir, output_dir=dest, platform=sys.platform)
    return dest


__all__ = [
    "build_desktop_app_bundle",
    "generate_tauri_scaffold",
    "install_app_into_portable_python",
    "run_tauri_build",
]
