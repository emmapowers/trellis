"""Build a portable single-exe bundle for Windows."""

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


def _collect_app_files(release_dir: Path) -> list[tuple[Path, str]]:
    """Gather exe + pyembed/ + DLLs from the Tauri release directory.

    Returns (absolute_path, archive_relative_path) pairs.
    """
    files: list[tuple[Path, str]] = []

    # Collect the main exe and DLLs from the release root
    for path in release_dir.iterdir():
        if not path.is_file():
            continue
        if path.suffix in _WINDOWS_SKIP_EXTENSIONS:
            continue
        if path.suffix in _WINDOWS_APP_EXTENSIONS:
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
        for abs_path, arc_name in files:
            zf.write(abs_path, arc_name)


def _generate_launcher_scaffold(
    launcher_dir: Path,
    product_name: str,
    exe_name: str,
    cargo_name: str,
    icon_path: Path | None,
) -> None:
    """Render Jinja2 templates for the launcher Rust crate."""
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
    }

    file_map = {
        "Cargo.toml.j2": "Cargo.toml",
        "main.rs.j2": "src/main.rs",
    }

    if icon_path and icon_path.exists():
        shutil.copy2(icon_path, launcher_dir / "icon.ico")
        file_map["build.rs.j2"] = "build.rs"

    for template_name, output_name in file_map.items():
        template = env.get_template(template_name)
        content = template.render(**template_vars)
        (launcher_dir / output_name).write_text(content)


def _build_launcher(rust: RustToolchain, launcher_dir: Path, cargo_name: str) -> Path:
    """Build the launcher crate and return the path to the release exe."""
    env = {**os.environ, **rust.env()}
    subprocess.run(
        [str(rust.cargo_bin), "build", "--release"],
        cwd=launcher_dir,
        env=env,
        check=True,
    )
    return launcher_dir / "target" / "release" / (cargo_name + "-launcher.exe")


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
    output_dir: Path,
) -> Path:
    """Build a portable single-exe bundle.

    Orchestrates: collect files -> create archive -> build launcher -> assemble.

    Args:
        rust: RustToolchain with environment configuration
        scaffold_dir: Path to the Tauri scaffold (contains target/release/)
        product_name: Display name of the application
        exe_name: Filename of the real executable (e.g. "myapp.exe")
        output_dir: Directory to write the portable exe

    Returns:
        Path to the assembled portable exe
    """
    release_dir = scaffold_dir / "target" / "release"

    # Collect app files from the release directory
    files = _collect_app_files(release_dir)
    if not files:
        raise RuntimeError(f"No app files found in {release_dir}")

    # Create the archive
    build_dir = scaffold_dir / "target" / "portable-build"
    build_dir.mkdir(parents=True, exist_ok=True)
    archive_path = build_dir / "app.zip"
    _create_archive(files, archive_path)

    # Build the launcher
    cargo_name = re.sub(r"[^a-z0-9_-]", "-", product_name.lower())
    cargo_name = re.sub(r"-+", "-", cargo_name).strip("-")
    launcher_dir = build_dir / "launcher"
    icon_path = scaffold_dir / "icons" / "icon.ico"
    _generate_launcher_scaffold(launcher_dir, product_name, exe_name, cargo_name, icon_path)
    launcher_exe = _build_launcher(rust, launcher_dir, cargo_name)

    # Assemble the portable exe
    output_path = output_dir / exe_name.replace(".exe", "-portable.exe")
    _assemble_portable_exe(launcher_exe, archive_path, output_path)

    return output_path
