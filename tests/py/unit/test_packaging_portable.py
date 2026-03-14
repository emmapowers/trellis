"""Tests for portable single-exe packaging."""

from __future__ import annotations

import hashlib
import io
import struct
import time
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
import zstandard

from trellis.packaging.portable import (
    FOOTER_SIZE,
    PORTABLE_MAGIC,
    _assemble_portable_exe,
    _collect_app_files,
    _create_archive,
    _output_filename,
    build_windows_exe,
)
from trellis.packaging.toolchain.rustup import RustToolchain


def _make_rust_toolchain(tmp_path: Path) -> RustToolchain:
    cargo_home = tmp_path / "cargo"
    rustup_home = tmp_path / "rustup"
    cargo_bin = cargo_home / "bin"
    cargo_bin.mkdir(parents=True)
    rustc = cargo_bin / "rustc"
    rustc.write_text("fake")
    cargo = cargo_bin / "cargo"
    cargo.write_text("fake")
    return RustToolchain(
        cargo_home=cargo_home,
        rustup_home=rustup_home,
        cargo_bin=cargo,
        rustc_bin=rustc,
    )


def _make_release_dir(tmp_path: Path) -> Path:
    """Create a fake Tauri release directory with typical files."""
    release_dir = tmp_path / "target" / "release"
    release_dir.mkdir(parents=True)

    # App exe
    (release_dir / "myapp.exe").write_bytes(b"MZ" + b"\x00" * 100)
    # DLLs
    (release_dir / "python313.dll").write_bytes(b"dll-content")
    (release_dir / "vcruntime140.dll").write_bytes(b"vcrt-content")
    # Files to skip
    (release_dir / "myapp.pdb").write_bytes(b"debug-symbols")
    (release_dir / "myapp.d").write_text("dep-info")
    (release_dir / "myapp.lib").write_bytes(b"lib-content")
    (release_dir / "myapp.exp").write_bytes(b"exp-content")
    # A random non-matching file (no relevant extension)
    (release_dir / "build-script").write_text("script")

    # pyembed directory
    pyembed = release_dir / "pyembed"
    pyembed.mkdir()
    (pyembed / "python.exe").write_bytes(b"python-exe")
    lib_dir = pyembed / "Lib" / "site-packages" / "trellis"
    lib_dir.mkdir(parents=True)
    (lib_dir / "__init__.py").write_text("# trellis")

    return release_dir


class TestCollectAppFiles:
    def test_gathers_exe_and_dlls(self, tmp_path: Path) -> None:
        release_dir = _make_release_dir(tmp_path)
        files = _collect_app_files(release_dir)
        arc_names = {name for _, name in files}

        assert "myapp.exe" in arc_names
        assert "python313.dll" in arc_names
        assert "vcruntime140.dll" in arc_names

    def test_excludes_pdb_and_dep_files(self, tmp_path: Path) -> None:
        release_dir = _make_release_dir(tmp_path)
        files = _collect_app_files(release_dir)
        arc_names = {name for _, name in files}

        assert "myapp.pdb" not in arc_names
        assert "myapp.d" not in arc_names
        assert "myapp.lib" not in arc_names
        assert "myapp.exp" not in arc_names

    def test_includes_pyembed_recursively(self, tmp_path: Path) -> None:
        release_dir = _make_release_dir(tmp_path)
        files = _collect_app_files(release_dir)
        arc_names = {name for _, name in files}

        assert "pyembed/python.exe" in arc_names
        assert "pyembed/Lib/site-packages/trellis/__init__.py" in arc_names

    def test_empty_release_dir(self, tmp_path: Path) -> None:
        release_dir = tmp_path / "target" / "release"
        release_dir.mkdir(parents=True)
        files = _collect_app_files(release_dir)
        assert files == []

    def test_raises_when_exe_name_missing(self, tmp_path: Path) -> None:
        release_dir = tmp_path / "target" / "release"
        release_dir.mkdir(parents=True)
        (release_dir / "python313.dll").write_bytes(b"dll-content")

        with pytest.raises(RuntimeError, match=r"Expected app executable 'myapp\.exe' not found"):
            _collect_app_files(release_dir, exe_name="myapp.exe")


class TestCreateArchive:
    def test_round_trip(self, tmp_path: Path) -> None:
        release_dir = _make_release_dir(tmp_path)
        files = _collect_app_files(release_dir)
        archive_path = tmp_path / "test.zip.zst"

        _create_archive(files, archive_path)

        # Decompress zstd outer layer, then read inner zip
        dctx = zstandard.ZstdDecompressor()
        zip_data = dctx.decompress(archive_path.read_bytes())
        with zipfile.ZipFile(io.BytesIO(zip_data), "r") as zf:
            names = set(zf.namelist())
            assert "myapp.exe" in names
            assert "pyembed/python.exe" in names
            # Verify content survived
            assert zf.read("myapp.exe") == b"MZ" + b"\x00" * 100

    def test_deterministic_hash_ignores_mtime(self, tmp_path: Path) -> None:
        release_dir = _make_release_dir(tmp_path)
        files = _collect_app_files(release_dir)

        archive1 = tmp_path / "a1.zip"
        _create_archive(files, archive1)

        # Touch all files to change mtimes
        time.sleep(0.1)
        for abs_path, _ in files:
            abs_path.touch()

        archive2 = tmp_path / "a2.zip"
        _create_archive(files, archive2)

        assert archive1.read_bytes() == archive2.read_bytes()


class TestAssemblePortableExe:
    def test_footer_structure(self, tmp_path: Path) -> None:
        launcher_exe = tmp_path / "launcher.exe"
        launcher_exe.write_bytes(b"LAUNCHER-STUB")

        archive_path = tmp_path / "app.zip"
        archive_path.write_bytes(b"PK-ARCHIVE-DATA")

        output_path = tmp_path / "output" / "myapp-portable.exe"
        _assemble_portable_exe(launcher_exe, archive_path, output_path)

        data = output_path.read_bytes()

        # Verify magic at end
        assert data[-8:] == PORTABLE_MAGIC

        # Verify archive size
        archive_bytes = archive_path.read_bytes()
        size_bytes = data[-16:-8]
        stored_size = struct.unpack("<Q", size_bytes)[0]
        assert stored_size == len(archive_bytes)

        # Verify hash
        expected_hash = hashlib.sha256(archive_bytes).hexdigest()[:32]
        stored_hash = data[-48:-16].decode("ascii")
        assert stored_hash == expected_hash

    def test_archive_extractable_from_assembled(self, tmp_path: Path) -> None:
        launcher_exe = tmp_path / "launcher.exe"
        launcher_exe.write_bytes(b"LAUNCHER-STUB")

        # Create a real zip archive
        archive_path = tmp_path / "app.zip"
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.writestr("test.txt", "hello world")

        output_path = tmp_path / "output" / "myapp-portable.exe"
        _assemble_portable_exe(launcher_exe, archive_path, output_path)

        # Extract archive from the assembled exe
        data = output_path.read_bytes()
        size_bytes = data[-16:-8]
        archive_size = struct.unpack("<Q", size_bytes)[0]
        archive_data = data[-(FOOTER_SIZE + archive_size) : -FOOTER_SIZE]

        with zipfile.ZipFile(io.BytesIO(archive_data), "r") as zf:
            assert zf.read("test.txt") == b"hello world"

    def test_hash_matches_archive_sha256(self, tmp_path: Path) -> None:
        launcher_exe = tmp_path / "launcher.exe"
        launcher_exe.write_bytes(b"X" * 50)

        archive_path = tmp_path / "app.zip"
        archive_content = b"some-archive-bytes"
        archive_path.write_bytes(archive_content)

        output_path = tmp_path / "output" / "myapp-portable.exe"
        _assemble_portable_exe(launcher_exe, archive_path, output_path)

        data = output_path.read_bytes()
        stored_hash = data[-48:-16].decode("ascii")
        computed_hash = hashlib.sha256(archive_content).hexdigest()[:32]
        assert stored_hash == computed_hash

    def test_creates_output_directory(self, tmp_path: Path) -> None:
        launcher_exe = tmp_path / "launcher.exe"
        launcher_exe.write_bytes(b"stub")
        archive_path = tmp_path / "app.zip"
        archive_path.write_bytes(b"data")

        output_path = tmp_path / "nested" / "deep" / "myapp-portable.exe"
        _assemble_portable_exe(launcher_exe, archive_path, output_path)
        assert output_path.exists()


class TestOutputFilename:
    def test_portable_naming(self) -> None:
        assert _output_filename("My App", "1.0.0", "exe") == "My-App-1.0.0.exe"

    def test_installer_naming(self) -> None:
        assert (
            _output_filename("My App", "1.0.0", "exe", installer=True)
            == "My-App-1.0.0-installer.exe"
        )

    def test_no_spaces_unchanged(self) -> None:
        assert _output_filename("myapp", "2.0.0", "dmg") == "myapp-2.0.0.dmg"

    def test_appimage_extension(self) -> None:
        assert (
            _output_filename("Widget Showcase", "0.1.0", "AppImage")
            == "Widget-Showcase-0.1.0.AppImage"
        )


class TestBuildPortableExe:
    def test_orchestration_flow(self, tmp_path: Path) -> None:
        rust = _make_rust_toolchain(tmp_path)
        scaffold_dir = tmp_path / "scaffold"
        release_dir = scaffold_dir / "target" / "release"

        release_dir.mkdir(parents=True)
        (release_dir / "myapp.exe").write_bytes(b"MZ-real-app")
        pyembed = release_dir / "pyembed"
        pyembed.mkdir()
        (pyembed / "python.exe").write_bytes(b"python")

        output_dir = tmp_path / "output"

        # cargo_name for "My App" is "my-app"; Cargo compiles hyphens to underscores
        launcher_exe_path = (
            scaffold_dir
            / "target"
            / "portable-build"
            / "launcher"
            / "target"
            / "release"
            / "my_app_launcher.exe"
        )

        def fake_cargo_build(cmd, *, cwd, env, check):
            launcher_exe_path.parent.mkdir(parents=True, exist_ok=True)
            launcher_exe_path.write_bytes(b"LAUNCHER-STUB")

        with patch("subprocess.run", side_effect=fake_cargo_build):
            result = build_windows_exe(
                rust=rust,
                scaffold_dir=scaffold_dir,
                product_name="My App",
                exe_name="myapp.exe",
                version="1.0.0",
                output_dir=output_dir,
            )

        assert result.exists()
        assert result.name == "My-App-1.0.0.exe"
        assert result.parent == output_dir

        data = result.read_bytes()
        assert data[-8:] == PORTABLE_MAGIC

    def test_cargo_invoked_with_correct_args(self, tmp_path: Path) -> None:
        rust = _make_rust_toolchain(tmp_path)
        scaffold_dir = tmp_path / "scaffold"
        release_dir = scaffold_dir / "target" / "release"
        release_dir.mkdir(parents=True)
        (release_dir / "myapp.exe").write_bytes(b"MZ")
        pyembed = release_dir / "pyembed"
        pyembed.mkdir()
        (pyembed / "python.exe").write_bytes(b"python")

        output_dir = tmp_path / "output"

        def fake_cargo_build(cmd, *, cwd, env, check):
            exe_path = cwd / "target" / "release" / "my_app_launcher.exe"
            exe_path.parent.mkdir(parents=True, exist_ok=True)
            exe_path.write_bytes(b"LAUNCHER")

        with patch("subprocess.run", side_effect=fake_cargo_build) as mock_run:
            build_windows_exe(
                rust=rust,
                scaffold_dir=scaffold_dir,
                product_name="My App",
                exe_name="myapp.exe",
                version="1.0.0",
                output_dir=output_dir,
            )

        cmd = mock_run.call_args[0][0]
        assert str(rust.cargo_bin) in cmd
        assert "build" in cmd
        assert "--release" in cmd

    def test_raises_when_no_files(self, tmp_path: Path) -> None:
        rust = _make_rust_toolchain(tmp_path)
        scaffold_dir = tmp_path / "scaffold"
        release_dir = scaffold_dir / "target" / "release"
        release_dir.mkdir(parents=True)

        with pytest.raises(RuntimeError, match="Expected app executable"):
            build_windows_exe(
                rust=rust,
                scaffold_dir=scaffold_dir,
                product_name="My App",
                exe_name="myapp.exe",
                version="1.0.0",
                output_dir=tmp_path / "output",
            )
