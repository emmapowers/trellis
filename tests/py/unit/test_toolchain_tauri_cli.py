"""Unit tests for trellis.toolchain.tauri_cli module."""

from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from trellis.toolchain import TAURI_CLI_VERSION
from trellis.toolchain.rustup import RustToolchain
from trellis.toolchain.tauri_cli import ensure_tauri_cli


def _make_rust_toolchain(tmp_path: Path) -> RustToolchain:
    """Create a minimal RustToolchain pointing at tmp_path."""
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


class TestEnsureTauriCli:
    """Tests for ensure_tauri_cli function."""

    def test_returns_cached_binary(self, tmp_path: Path) -> None:
        """Returns existing binary without downloading."""
        rust = _make_rust_toolchain(tmp_path)

        with (
            patch("trellis.toolchain.tauri_cli.BIN_DIR", tmp_path),
            patch("trellis.toolchain.tauri_cli.TAURI_CLI_VERSION", "2.10.0"),
            patch(
                "trellis.toolchain.tauri_cli.get_rust_target", return_value="aarch64-apple-darwin"
            ),
        ):
            # Create fake cached binary
            binary_dir = tmp_path / f"tauri-cli-{TAURI_CLI_VERSION}"
            binary_dir.mkdir(parents=True)
            binary_path = binary_dir / "cargo-tauri"
            binary_path.write_text("fake tauri cli")

            result = ensure_tauri_cli(rust)

        assert result == binary_path

    def test_downloads_and_extracts_tgz(self, tmp_path: Path) -> None:
        """Downloads and extracts .tgz archive on macOS/Linux."""
        rust = _make_rust_toolchain(tmp_path)

        # Create a mock .tgz with the tauri cli binary
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tf:
            data = b"fake tauri cli binary"
            info = tarfile.TarInfo(name="cargo-tauri")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
        tar_content = tar_buffer.getvalue()

        mock_response = MagicMock()
        mock_response.iter_bytes.return_value = [tar_content]
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch("trellis.toolchain.tauri_cli.BIN_DIR", tmp_path),
            patch("trellis.toolchain.tauri_cli.TAURI_CLI_VERSION", "2.10.0"),
            patch(
                "trellis.toolchain.tauri_cli.get_rust_target", return_value="aarch64-apple-darwin"
            ),
            patch("httpx.stream", return_value=mock_response),
        ):
            result = ensure_tauri_cli(rust)

        assert result.exists()
        assert result.name == "cargo-tauri"

    def test_downloads_zip_on_windows(self, tmp_path: Path) -> None:
        """Downloads and extracts .zip archive on Windows."""
        rust = _make_rust_toolchain(tmp_path)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("cargo-tauri.exe", "fake tauri cli binary")
        zip_content = zip_buffer.getvalue()

        mock_response = MagicMock()
        mock_response.iter_bytes.return_value = [zip_content]
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch("trellis.toolchain.tauri_cli.BIN_DIR", tmp_path),
            patch("trellis.toolchain.tauri_cli.TAURI_CLI_VERSION", "2.10.0"),
            patch(
                "trellis.toolchain.tauri_cli.get_rust_target", return_value="x86_64-pc-windows-msvc"
            ),
            patch("httpx.stream", return_value=mock_response),
        ):
            result = ensure_tauri_cli(rust)

        assert result.exists()
        assert result.name == "cargo-tauri.exe"

    def test_url_format(self, tmp_path: Path) -> None:
        """Verifies correct GitHub release URL."""
        rust = _make_rust_toolchain(tmp_path)

        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tf:
            data = b"fake"
            info = tarfile.TarInfo(name="cargo-tauri")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
        tar_content = tar_buffer.getvalue()

        mock_response = MagicMock()
        mock_response.iter_bytes.return_value = [tar_content]
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch("trellis.toolchain.tauri_cli.BIN_DIR", tmp_path),
            patch("trellis.toolchain.tauri_cli.TAURI_CLI_VERSION", "2.10.0"),
            patch(
                "trellis.toolchain.tauri_cli.get_rust_target",
                return_value="x86_64-unknown-linux-gnu",
            ),
            patch("httpx.stream", return_value=mock_response) as mock_stream,
        ):
            ensure_tauri_cli(rust)

        expected_url = (
            "https://github.com/tauri-apps/tauri/releases/download/"
            "tauri-cli-v2.10.0/cargo-tauri-x86_64-unknown-linux-gnu.tgz"
        )
        actual_url = mock_stream.call_args[0][1]
        assert actual_url == expected_url

    def test_falls_back_to_cargo_install(self, tmp_path: Path) -> None:
        """Falls back to cargo install when prebuilt download fails."""
        rust = _make_rust_toolchain(tmp_path)

        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.raise_for_status.side_effect = Exception("404")

        # After cargo install, the binary should appear
        def create_binary_on_install(*args: object, **kwargs: object) -> MagicMock:
            binary = rust.cargo_home / "bin" / "cargo-tauri"
            binary.write_text("installed via cargo")
            return MagicMock()

        with (
            patch("trellis.toolchain.tauri_cli.BIN_DIR", tmp_path),
            patch("trellis.toolchain.tauri_cli.TAURI_CLI_VERSION", "2.10.0"),
            patch(
                "trellis.toolchain.tauri_cli.get_rust_target",
                return_value="aarch64-unknown-linux-gnu",
            ),
            patch("httpx.stream", return_value=mock_response),
            patch("subprocess.run", side_effect=create_binary_on_install) as mock_run,
        ):
            ensure_tauri_cli(rust)

        # Should have called cargo install
        cmd = mock_run.call_args[0][0]
        assert "cargo" in str(cmd[0])
        assert "install" in cmd
        assert "tauri-cli" in cmd

    def test_cleans_up_archive_after_extraction(self, tmp_path: Path) -> None:
        """Deletes the archive file after successful extraction."""
        rust = _make_rust_toolchain(tmp_path)

        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tf:
            data = b"fake"
            info = tarfile.TarInfo(name="cargo-tauri")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
        tar_content = tar_buffer.getvalue()

        mock_response = MagicMock()
        mock_response.iter_bytes.return_value = [tar_content]
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch("trellis.toolchain.tauri_cli.BIN_DIR", tmp_path),
            patch("trellis.toolchain.tauri_cli.TAURI_CLI_VERSION", "2.10.0"),
            patch(
                "trellis.toolchain.tauri_cli.get_rust_target", return_value="aarch64-apple-darwin"
            ),
            patch("httpx.stream", return_value=mock_response),
        ):
            ensure_tauri_cli(rust)

        # No .tgz or .zip files should remain
        archive_files = list(tmp_path.glob("*.tgz")) + list(tmp_path.glob("*.zip"))
        assert len(archive_files) == 0
