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

from trellis.packaging.portable import _make_cargo_name, build_windows_exe
from trellis.packaging.toolchain import (
    PYTHON_STANDALONE_VERSION,
    ensure_python_standalone,
    ensure_rustup,
    ensure_tauri_cli,
)
from trellis.packaging.toolchain.rustup import RustToolchain

if TYPE_CHECKING:
    from trellis.app.config import Config

from PIL import Image

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _generate_default_icon(path: Path) -> None:
    """Generate a simple default 512x512 icon PNG."""
    img = Image.new("RGBA", (512, 512), (46, 125, 50, 255))
    img.save(path, "PNG")


def _parse_window_size(window_size: str) -> tuple[int, int, bool]:
    """Parse window size string into (width, height, maximized)."""
    if window_size == "maximized":
        return 1024, 768, True
    parts = window_size.split("x")
    return int(parts[0]), int(parts[1]), False


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
    window_width, window_height, window_maximized = _parse_window_size(config.window_size)

    # Cargo package names: lowercase, alphanumeric/hyphens/underscores only
    cargo_name = _make_cargo_name(config.name)

    template_vars = {
        "name": cargo_name,
        "product_name": config.title or config.name,
        "version": version,
        "identifier": identifier,
        "window_title": config.title or config.name,
        "window_width": window_width,
        "window_height": window_height,
        "window_maximized": window_maximized,
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
    *, standalone_base: Path, app_root: Path, pyembed_dir: Path
) -> None:
    """Install the Trellis app into the portable Python environment.

    Copies the standalone Python to pyembed_dir first, then uses pip to
    install the app and its dependencies into the copy. This avoids
    polluting the cached standalone Python with app-specific packages.
    The packaged runtime uses the standalone-built PyTauri extension and
    does not depend on pytauri-wheel being installed into pyembed.
    """
    if pyembed_dir.exists():
        shutil.rmtree(pyembed_dir)
    shutil.copytree(standalone_base, pyembed_dir)

    # Find python binary in the copy
    if sys.platform == "win32":
        python_bin = pyembed_dir / "python.exe"
    else:
        python_bin = pyembed_dir / "bin" / "python3"

    subprocess.run(
        [
            str(python_bin),
            "-m",
            "pip",
            "install",
            "--no-warn-script-location",
            "--no-cache-dir",
            str(app_root),
        ],
        check=True,
    )

    # Copy trellis_config.py so AppLoader can discover it at runtime
    config_src = app_root / "trellis_config.py"
    if config_src.exists():
        shutil.copy2(config_src, pyembed_dir / "trellis_config.py")


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
    """Generate .cargo/config.toml with rustflags for linking against embedded Python.

    Uses config.toml array-of-strings format instead of the RUSTFLAGS env var
    to correctly handle paths containing spaces.
    """
    cargo_dir = scaffold_dir / ".cargo"
    cargo_dir.mkdir(parents=True, exist_ok=True)

    _platform = sys.platform
    lines: list[str] = []

    if _platform == "darwin":
        lib_dir = pyembed_dir / "lib"
        rustflags = [
            "-L",
            str(lib_dir),
            "-C",
            "link-arg=-Wl,-rpath,@executable_path/../Resources/pyembed/lib",
        ]
        flags_toml = ", ".join(f'"{f}"' for f in rustflags)
        for target in ("aarch64-apple-darwin", "x86_64-apple-darwin"):
            lines.append(f"[target.{target}]")
            lines.append(f"rustflags = [{flags_toml}]")
            lines.append("")

    elif _platform == "win32":
        lib_dir = pyembed_dir / "libs"
        rustflags = ["-L", str(lib_dir)]
        flags_toml = ", ".join(f'"{f}"' for f in rustflags)
        for target in ("x86_64-pc-windows-msvc", "aarch64-pc-windows-msvc"):
            lines.append(f"[target.{target}]")
            lines.append(f"rustflags = [{flags_toml}]")
            lines.append("")

    else:  # linux
        lib_dir = pyembed_dir / "lib"
        rpath = f"$ORIGIN/../lib/{product_name}/pyembed/lib"
        rustflags = [
            "-L",
            str(lib_dir),
            "-C",
            f"link-arg=-Wl,-rpath,{rpath}",
        ]
        rustflags.extend(_get_linux_system_lib_flags())
        flags_toml = ", ".join(f'"{f}"' for f in rustflags)
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


def _check_macos_dev_tools() -> None:
    """Check that Xcode Command Line Tools are installed on macOS.

    Raises RuntimeError with install instructions if missing.
    """
    if sys.platform != "darwin":
        return

    result = subprocess.run(
        ["xcode-select", "-p"],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Xcode Command Line Tools are required to build a Tauri desktop app on macOS.\n\n"
            "Install them with:\n"
            "  xcode-select --install\n\n"
            "For more information, see:\n"
            "  https://developer.apple.com/xcode/resources/"
        )


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


def _tauri_bundles(
    *, installer: bool, platform: str, bundles: list[str] | None = None
) -> list[str]:
    """Return the Tauri bundle types for a given mode and platform.

    When *bundles* is provided, it is used directly. Otherwise, default
    bundle types are chosen based on *installer* and *platform*.
    Windows uses self-extracting exe (post-processed), so Tauri gets --no-bundle.
    """
    if bundles:
        return bundles
    if platform == "win32":
        return []
    if platform == "darwin":
        return ["dmg"] if installer else ["app"]
    # Linux
    return ["deb"] if installer else ["appimage"]


def run_tauri_build(
    *,
    tauri_cli: Path,
    rust: RustToolchain,
    scaffold_dir: Path,
    pyembed_dir: Path,
    product_name: str,
    installer: bool = False,
    bundles: list[str] | None = None,
) -> Path:
    """Run the Tauri build process.

    Args:
        tauri_cli: Path to the cargo-tauri binary
        rust: RustToolchain with environment configuration
        scaffold_dir: Path to the generated Tauri scaffold
        pyembed_dir: Path to the embedded Python directory
        product_name: Display name of the application (used for resource paths)
        installer: If True, build installer bundles instead of portable ones

    Returns:
        Path to the Tauri bundle output directory.
    """
    tauri_bundles = _tauri_bundles(installer=installer, platform=sys.platform, bundles=bundles)

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
        python_dir = "python" + ".".join(PYTHON_STANDALONE_VERSION.split(".")[:2])
        site_packages = pyembed_dir / "lib" / python_dir / "site-packages"
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

    return scaffold_dir / "target" / "release" / "bundle"


def _copy_build_output(
    *,
    bundle_dir: Path,
    output_dir: Path,
    product_name: str,
    version: str,
    tauri_bundles: list[str],
) -> list[str]:
    """Copy build artifacts from Tauri's bundle directory to output_dir.

    Only copies artifact types listed in *tauri_bundles* so stale outputs
    from previous builds are not included.

    Returns:
        List of artifact filenames written to output_dir.
    """
    from trellis.packaging.portable import _output_filename  # noqa: PLC0415

    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts: list[str] = []

    for bundle_type in tauri_bundles:
        if bundle_type == "app":
            macos_dir = bundle_dir / "macos"
            if macos_dir.exists():
                for app in macos_dir.glob("*.app"):
                    dest_name = _output_filename(product_name, version, "app")
                    dest = output_dir / dest_name
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(app, dest)
                    artifacts.append(dest_name)
        elif bundle_type == "dmg":
            dmg_dir = bundle_dir / "dmg"
            if dmg_dir.exists():
                for dmg in dmg_dir.glob("*.dmg"):
                    dest_name = _output_filename(product_name, version, "dmg")
                    shutil.copy2(dmg, output_dir / dest_name)
                    artifacts.append(dest_name)
        elif bundle_type == "appimage":
            appimage_dir = bundle_dir / "appimage"
            if appimage_dir.exists():
                for pkg in appimage_dir.glob("*.AppImage"):
                    dest_name = _output_filename(product_name, version, "AppImage")
                    shutil.copy2(pkg, output_dir / dest_name)
                    artifacts.append(dest_name)
        elif bundle_type == "deb":
            deb_dir = bundle_dir / "deb"
            if deb_dir.exists():
                for pkg in deb_dir.glob("*.deb"):
                    deb_name = pkg.name.lower().replace(" ", "-")
                    shutil.copy2(pkg, output_dir / deb_name)
                    artifacts.append(deb_name)

    return artifacts


def build_desktop_app_bundle(
    config: Config,
    app_root: Path,
    output_dir: Path | None,
    installer: bool = False,
    bundles: list[str] | None = None,
) -> tuple[Path, list[str]]:
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
        installer: If True, build installer bundle instead of portable

    Returns:
        (output_dir, artifacts) tuple where artifacts is a list of filenames.
    """
    _check_macos_dev_tools()
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
        standalone_base=python_standalone.base_dir,
        app_root=app_root,
        pyembed_dir=pyembed_dir,
    )

    # 3b. Copy Python DLLs next to the exe (Windows load-time dependency)
    if sys.platform == "win32":
        _stage_windows_python_dlls(pyembed_dir=pyembed_dir, scaffold_dir=scaffold_dir)

    # 4. Run Tauri build
    product_name = config.title or config.name
    version = config.version or "0.1.0"
    resolved_bundles = _tauri_bundles(installer=installer, platform=sys.platform, bundles=bundles)
    bundle_dir = run_tauri_build(
        tauri_cli=tauri_cli,
        rust=rust,
        scaffold_dir=scaffold_dir,
        pyembed_dir=pyembed_dir,
        product_name=product_name,
        installer=installer,
        bundles=bundles,
    )

    # 5. Copy output to destination
    dest = output_dir or (app_root / "dist")
    artifacts = _copy_build_output(
        bundle_dir=bundle_dir,
        output_dir=dest,
        product_name=product_name,
        version=version,
        tauri_bundles=resolved_bundles,
    )

    # 6. On Windows, build self-extracting exe (post-processing after Tauri compile)
    if sys.platform == "win32":
        cargo_name = _make_cargo_name(product_name)
        exe_name = cargo_name + ".exe"

        exe_path = build_windows_exe(
            rust=rust,
            scaffold_dir=scaffold_dir,
            product_name=product_name,
            exe_name=exe_name,
            version=version,
            output_dir=dest,
            installer=installer,
        )
        artifacts.append(exe_path.name)

    return dest, artifacts


__all__ = [
    "build_desktop_app_bundle",
    "generate_tauri_scaffold",
    "install_app_into_portable_python",
    "run_tauri_build",
]
