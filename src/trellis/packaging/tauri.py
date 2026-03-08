"""Build a desktop app bundle with Tauri."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from sysconfig import get_config_var
from typing import TYPE_CHECKING

import jinja2

from trellis.packaging.portable import build_installer_exe, build_portable_exe
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
        "is_windows": sys.platform == "win32",
    }

    # Link dist directory so Tauri can find frontend assets.
    # On Windows, symlinks require admin privileges, so use a junction instead.
    dist_link = scaffold_dir / "dist"
    if dist_link.exists() or dist_link.is_symlink():
        if dist_link.is_dir() and not dist_link.is_symlink():
            os.rmdir(dist_link)
        else:
            dist_link.unlink()
    if sys.platform == "win32":
        import _winapi  # noqa: PLC0415 - Windows-only

        _winapi.CreateJunction(str(dist_path.resolve()), str(dist_link))
    else:
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

    # Only list icons that actually exist in the tauri config
    template_vars["icon_paths"] = [
        f"icons/{f.name}" for f in sorted(icons_dir.iterdir()) if f.is_file()
    ]

    # Render templates (after icons so icon_paths is populated)
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

    # Copy the entire Python installation into pyembed for bundling.
    # Unix layout: install/bin/python3 → parent.parent = install/
    # Windows layout: python/python.exe → parent = python/
    if sys.platform == "win32":
        src_dir = python_bin.parent
    else:
        src_dir = python_bin.parent.parent

    if pyembed_dir.exists():
        shutil.rmtree(pyembed_dir)
    shutil.copytree(src_dir, pyembed_dir)


def _patch_libpython_install_name(pyembed_dir: Path) -> None:
    """Patch libpython's install_name on macOS to use @rpath.

    python-build-standalone ships libpython with an absolute install_name.
    Without @rpath in the dylib's install_name, the RPATH set on the
    executable is ignored by dyld.
    """
    _platform = sys.platform
    if _platform != "darwin":
        return

    lib_dir = pyembed_dir / "lib"
    for dylib in lib_dir.glob("libpython*.dylib"):
        if dylib.is_symlink():
            continue
        subprocess.run(
            ["install_name_tool", "-id", f"@rpath/{dylib.name}", str(dylib)],
            check=True,
        )


def _get_rustflags(pyembed_dir: Path) -> str | None:
    """Get RUSTFLAGS for linking against the embedded Python.

    Returns None on Linux where flags are set via .cargo/config.toml instead,
    to support spaces in product_name within rpath values.
    """
    _platform = sys.platform
    if _platform == "linux":
        # All flags handled by .cargo/config.toml on Linux
        return None

    if _platform == "win32":
        lib_dir = pyembed_dir / "libs"
    else:
        lib_dir = pyembed_dir / "lib"
    flags = f"-L {lib_dir}"

    if _platform == "darwin":
        flags += " -C link-arg=-Wl,-rpath,@executable_path/../Resources/pyembed/lib"

    return flags


def _get_linux_system_lib_flags() -> list[str]:
    """Get -L flags for system library paths on Linux."""
    flags: list[str] = []
    result = subprocess.run(
        ["pkg-config", "--libs-only-L", "gtk+-3.0", "webkit2gtk-4.1"],
        check=False,
        capture_output=True,
        text=True,
    )
    pkg_config_dirs = result.stdout.strip()
    if not pkg_config_dirs:
        # pkg-config returns no -L flags when libs are in standard paths
        multiarch = get_config_var("MULTIARCH") or ""
        for lib_path in [f"/usr/lib/{multiarch}", "/usr/lib"]:
            if Path(lib_path).is_dir():
                flags.extend(["-L", lib_path])
    else:
        # pkg-config returns e.g. "-L/usr/lib/x86_64-linux-gnu"
        for part in pkg_config_dirs.split():
            flags.extend(["-L", part.removeprefix("-L")])

    return flags


def _generate_cargo_config(*, scaffold_dir: Path, pyembed_dir: Path, product_name: str) -> None:
    """Generate .cargo/config.toml with linker flags for Linux.

    Uses config.toml instead of RUSTFLAGS to handle spaces in product_name
    (rpath values containing spaces can't be passed via RUSTFLAGS).
    """
    if sys.platform != "linux":
        return

    cargo_dir = scaffold_dir / ".cargo"
    cargo_dir.mkdir(parents=True, exist_ok=True)

    lib_dir = pyembed_dir / "lib"
    rpath = f"$ORIGIN/../lib/{product_name}/pyembed/lib"

    rustflags = [
        "-L",
        str(lib_dir),
        "-C",
        f"link-arg=-Wl,-rpath,{rpath}",
    ]
    rustflags.extend(_get_linux_system_lib_flags())

    # Format as TOML array
    flags_toml = ", ".join(f'"{f}"' for f in rustflags)

    lines: list[str] = []
    for target in ("x86_64-unknown-linux-gnu", "aarch64-unknown-linux-gnu"):
        lines.append(f"[target.{target}]")
        lines.append(f"rustflags = [{flags_toml}]")
        lines.append("")

    (cargo_dir / "config.toml").write_text("\n".join(lines) + "\n")


_WINDOWS_PYTHON_DLLS = ["python3*.dll", "vcruntime*.dll"]


def _stage_windows_python_dlls(*, pyembed_dir: Path, scaffold_dir: Path) -> None:
    """Copy Python DLLs to the scaffold root so NSIS installs them next to the exe.

    The exe has a load-time dependency on python313.dll, which must be in the
    same directory as the exe (not in a subdirectory like pyembed/).
    """
    for pattern in _WINDOWS_PYTHON_DLLS:
        for dll in pyembed_dir.glob(pattern):
            shutil.copy2(dll, scaffold_dir / dll.name)


def _get_pyo3_python(pyembed_dir: Path) -> Path:
    """Get the path to the Python binary in pyembed."""
    if sys.platform == "win32":
        return pyembed_dir / "python.exe"
    return pyembed_dir / "bin" / "python3"


_LINUX_REQUIRED_LIBS = [
    ("gtk+-3.0", "libgtk-3-dev"),
    ("webkit2gtk-4.1", "libwebkit2gtk-4.1-dev"),
    ("javascriptcoregtk-4.1", "libjavascriptcoregtk-4.1-dev"),
    ("libsoup-3.0", "libsoup-3.0-dev"),
    ("librsvg-2.0", "librsvg2-dev"),
]


def _check_linux_system_deps() -> None:
    """Check that required system libraries are available on Linux.

    Raises RuntimeError with install instructions if any are missing.
    """
    if sys.platform != "linux":
        return

    missing: list[tuple[str, str]] = []
    for pkg_config_name, apt_package in _LINUX_REQUIRED_LIBS:
        result = subprocess.run(
            ["pkg-config", "--exists", pkg_config_name],
            check=False,
            capture_output=True,
        )
        if result.returncode != 0:
            missing.append((pkg_config_name, apt_package))

    if not missing:
        return

    apt_packages = " ".join(pkg for _, pkg in missing)
    lib_list = "\n".join(f"  - {name} ({pkg})" for name, pkg in missing)
    raise RuntimeError(
        f"Missing system libraries required to build a Tauri desktop app:\n"
        f"{lib_list}\n\n"
        f"Install them with:\n"
        f"  sudo apt-get install {apt_packages}\n\n"
        f"For other distros, see: https://v2.tauri.app/start/prerequisites/#linux"
    )


def run_tauri_build(
    *,
    tauri_cli: Path,
    rust: RustToolchain,
    scaffold_dir: Path,
    pyembed_dir: Path,
    product_name: str,
    bundles: list[str] | None = None,
) -> tuple[Path, bool, bool]:
    """Run the Tauri build process.

    Args:
        tauri_cli: Path to the cargo-tauri binary
        rust: RustToolchain with environment configuration
        scaffold_dir: Path to the generated Tauri scaffold
        pyembed_dir: Path to the embedded Python directory
        product_name: Display name of the application (used for resource paths)
        bundles: Bundle types to build (default: ["app"])

    Returns:
        Tuple of (bundle_dir, wants_portable, wants_installer).
    """
    if bundles is None:
        if sys.platform == "darwin":
            bundles = ["app"]
        elif sys.platform == "win32":
            bundles = ["portable"]
        else:
            bundles = ["deb"]

    # Separate self-extracting bundle types from tauri-native ones
    _SELF_EXTRACTING = {"portable", "installer"}
    wants_portable = "portable" in bundles
    wants_installer = "installer" in bundles
    tauri_bundles = [b for b in bundles if b not in _SELF_EXTRACTING]

    _patch_libpython_install_name(pyembed_dir)
    _generate_cargo_config(
        scaffold_dir=scaffold_dir, pyembed_dir=pyembed_dir, product_name=product_name
    )

    # LD_LIBRARY_PATH lets linuxdeploy find libpython and vendored libs
    # during AppImage bundling (Linux only)
    if sys.platform == "win32":
        site_packages = pyembed_dir / "Lib" / "site-packages"
        ld_library_path = ""
    else:
        lib_paths = [str(pyembed_dir / "lib")]
        site_packages = pyembed_dir / "lib" / "python3.13" / "site-packages"
        if site_packages.is_dir():
            lib_paths.extend(str(d) for d in site_packages.glob("*.libs"))
        if existing := os.environ.get("LD_LIBRARY_PATH"):
            lib_paths.append(existing)
        ld_library_path = ":".join(lib_paths)

    env = {
        **os.environ,
        **rust.env(),
        "PYTAURI_STANDALONE": "1",
        "PYO3_PYTHON": str(_get_pyo3_python(pyembed_dir)),
        "LD_LIBRARY_PATH": ld_library_path,
        "APPIMAGE_EXTRACT_AND_RUN": "1",
        "NO_STRIP": "true",
        "DEPLOY_GTK_VERSION": "3",
    }
    rustflags = _get_rustflags(pyembed_dir)
    if rustflags is not None:
        env["RUSTFLAGS"] = rustflags

    tauri_cmd = [str(tauri_cli), "build"]
    if tauri_bundles:
        tauri_cmd.extend(["--bundles", *tauri_bundles])
    else:
        tauri_cmd.append("--no-bundle")

    subprocess.run(
        tauri_cmd,
        cwd=scaffold_dir,
        env=env,
        check=True,
    )

    # Tauri outputs bundles to target/release/bundle/
    return scaffold_dir / "target" / "release" / "bundle", wants_portable, wants_installer


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
        for subdir, glob_pattern in [
            ("appimage", "*.AppImage"),
            ("deb", "*.deb"),
            ("rpm", "*.rpm"),
        ]:
            pkg_dir = bundle_dir / subdir
            if pkg_dir.exists():
                for pkg in pkg_dir.glob(glob_pattern):
                    shutil.copy2(pkg, output_dir / pkg.name)


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
    _check_linux_system_deps()

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

    # 3b. Copy Python DLLs next to the exe (Windows load-time dependency)
    if sys.platform == "win32":
        _stage_windows_python_dlls(pyembed_dir=pyembed_dir, scaffold_dir=scaffold_dir)

    # 4. Run Tauri build
    product_name = config.title or config.name
    bundle_dir, wants_portable, wants_installer = run_tauri_build(
        tauri_cli=tauri_cli,
        rust=rust,
        scaffold_dir=scaffold_dir,
        pyembed_dir=pyembed_dir,
        product_name=product_name,
        bundles=bundles,
    )

    # 5. Copy output to destination
    dest = output_dir or (app_root / "dist")
    _copy_build_output(bundle_dir=bundle_dir, output_dir=dest, platform=sys.platform)

    # 6. Build self-extracting exe(s) if requested (post-processing after Tauri compile)
    cargo_name = re.sub(r"[^a-z0-9_-]", "-", product_name.lower())
    cargo_name = re.sub(r"-+", "-", cargo_name).strip("-")
    exe_name = cargo_name + ".exe"

    if wants_portable:
        build_portable_exe(
            rust=rust,
            scaffold_dir=scaffold_dir,
            product_name=product_name,
            exe_name=exe_name,
            output_dir=dest,
        )

    if wants_installer:
        version = config.version or "0.1.0"
        build_installer_exe(
            rust=rust,
            scaffold_dir=scaffold_dir,
            product_name=product_name,
            exe_name=exe_name,
            version=version,
            output_dir=dest,
        )

    return dest


__all__ = [
    "build_desktop_app_bundle",
    "generate_tauri_scaffold",
    "install_app_into_portable_python",
    "run_tauri_build",
]
