"""Unit tests for trellis.bundler.bun module."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestGetBunPlatform:
    """Tests for get_bun_platform function."""

    def test_darwin_arm64(self) -> None:
        """Returns darwin-aarch64 for macOS ARM."""
        from trellis.bundler.bun import get_bun_platform

        with patch("platform.system", return_value="Darwin"):
            with patch("platform.machine", return_value="arm64"):
                assert get_bun_platform() == "darwin-aarch64"

    def test_darwin_x64(self) -> None:
        """Returns darwin-x64 for macOS Intel."""
        from trellis.bundler.bun import get_bun_platform

        with patch("platform.system", return_value="Darwin"):
            with patch("platform.machine", return_value="x86_64"):
                assert get_bun_platform() == "darwin-x64"

    def test_linux_x64(self) -> None:
        """Returns linux-x64 for Linux x86_64."""
        from trellis.bundler.bun import get_bun_platform

        with patch("platform.system", return_value="Linux"):
            with patch("platform.machine", return_value="x86_64"):
                assert get_bun_platform() == "linux-x64"

    def test_linux_arm64(self) -> None:
        """Returns linux-aarch64 for Linux aarch64."""
        from trellis.bundler.bun import get_bun_platform

        with patch("platform.system", return_value="Linux"):
            with patch("platform.machine", return_value="aarch64"):
                assert get_bun_platform() == "linux-aarch64"

    def test_linux_arm64_alternate(self) -> None:
        """Returns linux-aarch64 for Linux arm64 (alternate name)."""
        from trellis.bundler.bun import get_bun_platform

        with patch("platform.system", return_value="Linux"):
            with patch("platform.machine", return_value="arm64"):
                assert get_bun_platform() == "linux-aarch64"

    def test_windows_x64(self) -> None:
        """Returns windows-x64 for Windows x64."""
        from trellis.bundler.bun import get_bun_platform

        with patch("platform.system", return_value="Windows"):
            with patch("platform.machine", return_value="AMD64"):
                assert get_bun_platform() == "windows-x64"

    def test_windows_x64_alternate(self) -> None:
        """Returns windows-x64 for Windows x86_64."""
        from trellis.bundler.bun import get_bun_platform

        with patch("platform.system", return_value="Windows"):
            with patch("platform.machine", return_value="x86_64"):
                assert get_bun_platform() == "windows-x64"

    def test_unsupported_os(self) -> None:
        """Raises RuntimeError for unsupported OS."""
        from trellis.bundler.bun import get_bun_platform

        with patch("platform.system", return_value="FreeBSD"):
            with patch("platform.machine", return_value="x86_64"):
                with pytest.raises(RuntimeError, match="Unsupported platform"):
                    get_bun_platform()

    def test_unsupported_arch(self) -> None:
        """Raises RuntimeError for unsupported architecture."""
        from trellis.bundler.bun import get_bun_platform

        with patch("platform.system", return_value="Linux"):
            with patch("platform.machine", return_value="riscv64"):
                with pytest.raises(RuntimeError, match="Unsupported platform"):
                    get_bun_platform()

    def test_windows_arm_unsupported(self) -> None:
        """Raises RuntimeError for Windows ARM (not supported by Bun)."""
        from trellis.bundler.bun import get_bun_platform

        with patch("platform.system", return_value="Windows"):
            with patch("platform.machine", return_value="arm64"):
                with pytest.raises(RuntimeError, match="Unsupported platform"):
                    get_bun_platform()


class TestEnsureBun:
    """Tests for ensure_bun function."""

    def test_returns_cached_binary(self, tmp_path: Path) -> None:
        """Returns existing binary path without downloading."""
        from trellis.bundler.bun import ensure_bun

        with patch("trellis.bundler.bun.BIN_DIR", tmp_path):
            with patch("trellis.bundler.bun.BUN_VERSION", "1.0.0"):
                with patch("trellis.bundler.bun.get_bun_platform", return_value="darwin-aarch64"):
                    # Create fake cached binary
                    binary_dir = tmp_path / "bun-1.0.0-darwin-aarch64" / "bun-darwin-aarch64"
                    binary_dir.mkdir(parents=True)
                    binary_path = binary_dir / "bun"
                    binary_path.write_text("fake binary")

                    result = ensure_bun()

                    assert result == binary_path

    def test_returns_cached_windows_binary(self, tmp_path: Path) -> None:
        """Returns existing .exe binary path on Windows."""
        from trellis.bundler.bun import ensure_bun

        with patch("trellis.bundler.bun.BIN_DIR", tmp_path):
            with patch("trellis.bundler.bun.BUN_VERSION", "1.0.0"):
                with patch("trellis.bundler.bun.get_bun_platform", return_value="windows-x64"):
                    # Create fake cached binary
                    binary_dir = tmp_path / "bun-1.0.0-windows-x64" / "bun-windows-x64"
                    binary_dir.mkdir(parents=True)
                    binary_path = binary_dir / "bun.exe"
                    binary_path.write_text("fake binary")

                    result = ensure_bun()

                    assert result == binary_path

    def test_downloads_and_extracts_zip(self, tmp_path: Path) -> None:
        """Downloads and extracts Bun ZIP when not cached."""
        from trellis.bundler.bun import ensure_bun

        # Create a mock ZIP file with bun binary
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("bun-darwin-aarch64/bun", "fake bun binary content")

        zip_content = zip_buffer.getvalue()

        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.iter_bytes.return_value = [zip_content]
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("trellis.bundler.bun.BIN_DIR", tmp_path):
            with patch("trellis.bundler.bun.BUN_VERSION", "1.0.0"):
                with patch("trellis.bundler.bun.get_bun_platform", return_value="darwin-aarch64"):
                    with patch("httpx.stream", return_value=mock_response):
                        result = ensure_bun()

        # Verify binary was extracted
        assert result.exists()
        assert result.name == "bun"
        assert result.read_text() == "fake bun binary content"

    def test_download_url_format(self, tmp_path: Path) -> None:
        """Verifies correct GitHub release URL is used."""
        from trellis.bundler.bun import ensure_bun

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("bun-linux-x64/bun", "fake bun")
        zip_content = zip_buffer.getvalue()

        mock_response = MagicMock()
        mock_response.iter_bytes.return_value = [zip_content]
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("trellis.bundler.bun.BIN_DIR", tmp_path):
            with patch("trellis.bundler.bun.BUN_VERSION", "1.3.5"):
                with patch("trellis.bundler.bun.get_bun_platform", return_value="linux-x64"):
                    with patch("httpx.stream", return_value=mock_response) as mock_stream:
                        ensure_bun()

        expected_url = (
            "https://github.com/oven-sh/bun/releases/download/bun-v1.3.5/bun-linux-x64.zip"
        )
        mock_stream.assert_called_once()
        actual_url = mock_stream.call_args[0][1]
        assert actual_url == expected_url

    def test_sets_executable_permission(self, tmp_path: Path) -> None:
        """Binary gets executable permission (0o755) after extraction."""
        from trellis.bundler.bun import ensure_bun

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("bun-darwin-x64/bun", "fake bun")
        zip_content = zip_buffer.getvalue()

        mock_response = MagicMock()
        mock_response.iter_bytes.return_value = [zip_content]
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("trellis.bundler.bun.BIN_DIR", tmp_path):
            with patch("trellis.bundler.bun.BUN_VERSION", "1.0.0"):
                with patch("trellis.bundler.bun.get_bun_platform", return_value="darwin-x64"):
                    with patch("httpx.stream", return_value=mock_response):
                        result = ensure_bun()

        # Check executable permission (on Unix)
        import os
        import stat

        mode = os.stat(result).st_mode
        assert mode & stat.S_IXUSR  # User execute permission

    def test_cleans_up_zip_after_extraction(self, tmp_path: Path) -> None:
        """Deletes the ZIP file after successful extraction."""
        from trellis.bundler.bun import ensure_bun

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("bun-darwin-aarch64/bun", "fake bun")
        zip_content = zip_buffer.getvalue()

        mock_response = MagicMock()
        mock_response.iter_bytes.return_value = [zip_content]
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("trellis.bundler.bun.BIN_DIR", tmp_path):
            with patch("trellis.bundler.bun.BUN_VERSION", "1.0.0"):
                with patch("trellis.bundler.bun.get_bun_platform", return_value="darwin-aarch64"):
                    with patch("httpx.stream", return_value=mock_response):
                        ensure_bun()

        # No .zip files should remain
        zip_files = list(tmp_path.glob("*.zip"))
        assert len(zip_files) == 0
