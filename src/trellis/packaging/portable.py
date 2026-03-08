"""Build portable and installer single-exe bundles for Windows."""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

import jinja2

from trellis.toolchain.rustup import RustToolchain

_TEMPLATES_DIR = Path(__file__).parent / "templates"

PORTABLE_MAGIC = b"TRLSPACK"
FOOTER_SIZE = 48  # 32 hex hash + 8 archive size + 8 magic

_WINDOWS_APP_EXTENSIONS = {".exe", ".dll"}
_WINDOWS_SKIP_EXTENSIONS = {".pdb", ".d", ".lib", ".exp"}


def _make_cargo_name(name: str) -> str:
    """Normalize a name into a valid Cargo package name (lowercase, alphanumeric/hyphens)."""
    result = re.sub(r"[^a-z0-9_-]", "-", name.lower())
    cargo_name = re.sub(r"-+", "-", result).strip("-")
    if not cargo_name:
        raise ValueError("name must contain at least one ASCII letter, digit, '_' or '-'")
    return cargo_name


def _output_filename(product_name: str, version: str, ext: str, *, installer: bool = False) -> str:
    """Build a consistent output filename.

    Examples:
        _output_filename("Widget Showcase", "0.1.0", "exe") -> "Widget-Showcase-0.1.0.exe"
        _output_filename("My App", "1.0.0", "exe", installer=True) -> "My-App-1.0.0-installer.exe"
    """
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", product_name)
    name = re.sub(r"\s+", "-", name).strip(" .-")
    name = re.sub(r"-+", "-", name)
    if not name:
        raise ValueError("product_name must contain at least one valid filename character")
    safe_version = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", version)
    safe_version = re.sub(r"\s+", "-", safe_version).strip(" .-")
    safe_version = re.sub(r"-+", "-", safe_version)
    if not safe_version:
        raise ValueError("version must contain at least one valid filename character")
    suffix = "-installer" if installer else ""
    return f"{name}-{safe_version}{suffix}.{ext}"


def _collect_app_files(release_dir: Path, exe_name: str = "") -> list[tuple[Path, str]]:
    """Gather exe + pyembed/ + DLLs from the Tauri release directory.

    Args:
        release_dir: Path to the Tauri release directory
        exe_name: Expected main executable name. When set, only this exe and
            DLLs are collected (prevents rebundling previous package outputs).

    Returns (absolute_path, archive_relative_path) pairs.
    """
    files: list[tuple[Path, str]] = []

    # Collect the main exe and DLLs from the release root
    for path in release_dir.iterdir():
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix in _WINDOWS_SKIP_EXTENSIONS:
            continue
        if exe_name and path.name == exe_name:
            files.append((path, path.name))
        elif not exe_name and suffix in _WINDOWS_APP_EXTENSIONS:
            files.append((path, path.name))
        elif suffix == ".dll":
            files.append((path, path.name))

    # Collect pyembed directory recursively
    pyembed_dir = release_dir / "pyembed"
    if pyembed_dir.is_dir():
        for path in pyembed_dir.rglob("*"):
            if path.is_file():
                rel = path.relative_to(release_dir)
                files.append((path, str(rel).replace("\\", "/")))

    return files


def _create_archive(files: list[tuple[Path, str]], archive_path: Path) -> None:
    """Create a zip archive from the collected files."""
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for abs_path, arc_name in sorted(files, key=lambda item: item[1]):
            zf.write(abs_path, arc_name)


def _generate_launcher_scaffold(
    launcher_dir: Path,
    product_name: str,
    exe_name: str,
    cargo_name: str,
    icon_path: Path | None,
    *,
    mode: str = "portable",
    version: str = "",
) -> None:
    """Render Jinja2 templates for the launcher Rust crate.

    Args:
        mode: "portable" for hash-based caching, "installer" for hash-based
              install with Start Menu shortcut and uninstaller registration.
        version: App version string, used for display in Add/Remove Programs.
    """
    launcher_dir.mkdir(parents=True, exist_ok=True)
    (launcher_dir / "src").mkdir(parents=True, exist_ok=True)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(_TEMPLATES_DIR / "launcher")),
        keep_trailing_newline=True,
    )

    template_vars = {
        "name": cargo_name,
        "product_name": product_name,
        "exe_name": exe_name,
        "version": version,
    }

    main_template = "main_installer.rs.j2" if mode == "installer" else "main.rs.j2"
    file_map = {
        "Cargo.toml.j2": "Cargo.toml",
        main_template: "src/main.rs",
    }

    if icon_path and icon_path.exists():
        shutil.copy2(icon_path, launcher_dir / "icon.ico")
        file_map["build.rs.j2"] = "build.rs"
    else:
        (launcher_dir / "build.rs").unlink(missing_ok=True)
        (launcher_dir / "icon.ico").unlink(missing_ok=True)

    for template_name, output_name in file_map.items():
        template = env.get_template(template_name)
        content = template.render(**template_vars)
        (launcher_dir / output_name).write_text(content, encoding="utf-8")


def _build_launcher(rust: RustToolchain, launcher_dir: Path, cargo_name: str) -> Path:
    """Build the launcher crate and return the path to the release exe."""
    target_dir = launcher_dir / "target"
    env = {**os.environ, **rust.env(), "CARGO_TARGET_DIR": str(target_dir)}
    subprocess.run(
        [str(rust.cargo_bin), "build", "--release"],
        cwd=launcher_dir,
        env=env,
        check=True,
    )
    binary_name = (cargo_name + "-launcher").replace("-", "_") + ".exe"
    return launcher_dir / "target" / "release" / binary_name


def _assemble_portable_exe(launcher_exe: Path, archive_path: Path, output_path: Path) -> None:
    """Concatenate launcher + archive + footer into a single portable exe.

    Footer format: [32-byte hex SHA-256][8-byte archive size LE][8-byte magic]
    """
    archive_bytes = archive_path.read_bytes()
    content_hash = hashlib.sha256(archive_bytes).hexdigest()[:32]
    archive_size = len(archive_bytes)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(launcher_exe.read_bytes())
        f.write(archive_bytes)
        f.write(content_hash.encode("ascii"))
        f.write(archive_size.to_bytes(8, "little"))
        f.write(PORTABLE_MAGIC)


def build_portable_exe(
    *,
    rust: RustToolchain,
    scaffold_dir: Path,
    product_name: str,
    exe_name: str,
    version: str,
    output_dir: Path,
) -> Path:
    """Build a portable single-exe bundle.

    Orchestrates: collect files -> create archive -> build launcher -> assemble.

    Returns:
        Path to the assembled portable exe
    """
    release_dir = scaffold_dir / "target" / "release"

    files = _collect_app_files(release_dir, exe_name)
    if not files:
        raise RuntimeError(f"No app files found in {release_dir}")

    build_dir = scaffold_dir / "target" / "portable-build"
    build_dir.mkdir(parents=True, exist_ok=True)
    archive_path = build_dir / "app.zip"
    _create_archive(files, archive_path)

    cargo_name = _make_cargo_name(product_name)
    launcher_dir = build_dir / "launcher"
    icon_path = scaffold_dir / "icons" / "icon.ico"
    _generate_launcher_scaffold(launcher_dir, product_name, exe_name, cargo_name, icon_path)
    launcher_exe = _build_launcher(rust, launcher_dir, cargo_name)

    output_path = output_dir / _output_filename(product_name, version, "exe")
    _assemble_portable_exe(launcher_exe, archive_path, output_path)

    return output_path


def build_installer_exe(
    *,
    rust: RustToolchain,
    scaffold_dir: Path,
    product_name: str,
    exe_name: str,
    version: str,
    output_dir: Path,
) -> Path:
    """Build an installer single-exe bundle.

    Like build_portable_exe but installs to %LOCALAPPDATA% with a Start Menu
    shortcut and Add/Remove Programs uninstaller. Uses the content hash to
    detect changes and re-extract when the bundle contents differ.

    Returns:
        Path to the assembled installer exe
    """
    release_dir = scaffold_dir / "target" / "release"

    files = _collect_app_files(release_dir, exe_name)
    if not files:
        raise RuntimeError(f"No app files found in {release_dir}")

    build_dir = scaffold_dir / "target" / "installer-build"
    build_dir.mkdir(parents=True, exist_ok=True)
    archive_path = build_dir / "app.zip"
    _create_archive(files, archive_path)

    cargo_name = _make_cargo_name(product_name)
    launcher_dir = build_dir / "launcher"
    icon_path = scaffold_dir / "icons" / "icon.ico"
    _generate_launcher_scaffold(
        launcher_dir,
        product_name,
        exe_name,
        cargo_name,
        icon_path,
        mode="installer",
        version=version,
    )
    launcher_exe = _build_launcher(rust, launcher_dir, cargo_name)

    output_path = output_dir / _output_filename(product_name, version, "exe", installer=True)
    _assemble_portable_exe(launcher_exe, archive_path, output_path)

    return output_path
