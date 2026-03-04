"""Unit tests for trellis.toolchain.python_standalone module."""

from __future__ import annotations

import io
import tarfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from trellis.toolchain.python_standalone import ensure_python_standalone


class TestEnsurePythonStandalone:
    """Tests for ensure_python_standalone function."""

    def test_returns_cached_binary(self, tmp_path: Path) -> None:
        """Returns existing installation without downloading."""
        with (
            patch("trellis.toolchain.python_standalone.BIN_DIR", tmp_path),
            patch("trellis.toolchain.python_standalone.PYTHON_STANDALONE_VERSION", "3.13.1"),
            patch(
                "trellis.toolchain.python_standalone.get_rust_target",
                return_value="aarch64-apple-darwin",
            ),
        ):
            # Create fake cached installation
            install_dir = tmp_path / "python-standalone-3.13.1"
            bin_dir = install_dir / "python" / "install" / "bin"
            bin_dir.mkdir(parents=True)
            python_bin = bin_dir / "python3"
            python_bin.write_text("fake python")

            result = ensure_python_standalone()

        assert result.python_bin == python_bin
        assert result.base_dir == install_dir / "python" / "install"

    def test_downloads_and_extracts(self, tmp_path: Path) -> None:
        """Downloads and extracts tarball when not cached."""
        # Create a mock tarball with python binary
        inner_tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=inner_tar_buffer, mode="w") as inner_tf:
            # python/install/bin/python3
            data = b"fake python binary"
            info = tarfile.TarInfo(name="python/install/bin/python3")
            info.size = len(data)
            inner_tf.addfile(info, io.BytesIO(data))

        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tf:
            data = b"fake python binary"
            info = tarfile.TarInfo(name="python/install/bin/python3")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
        tar_content = tar_buffer.getvalue()

        mock_response = MagicMock()
        mock_response.iter_bytes.return_value = [tar_content]
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch("trellis.toolchain.python_standalone.BIN_DIR", tmp_path),
            patch("trellis.toolchain.python_standalone.PYTHON_STANDALONE_VERSION", "3.13.1"),
            patch(
                "trellis.toolchain.python_standalone.get_rust_target",
                return_value="aarch64-apple-darwin",
            ),
            patch("httpx.stream", return_value=mock_response),
        ):
            result = ensure_python_standalone()

        assert result.python_bin.exists()
        assert result.python_bin.name == "python3"

    def test_url_format_macos(self, tmp_path: Path) -> None:
        """Verifies correct download URL for macOS."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tf:
            data = b"fake"
            info = tarfile.TarInfo(name="python/install/bin/python3")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
        tar_content = tar_buffer.getvalue()

        mock_response = MagicMock()
        mock_response.iter_bytes.return_value = [tar_content]
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch("trellis.toolchain.python_standalone.BIN_DIR", tmp_path),
            patch("trellis.toolchain.python_standalone.PYTHON_STANDALONE_VERSION", "3.13.1"),
            patch(
                "trellis.toolchain.python_standalone.get_rust_target",
                return_value="aarch64-apple-darwin",
            ),
            patch("httpx.stream", return_value=mock_response) as mock_stream,
        ):
            ensure_python_standalone()

        url = mock_stream.call_args[0][1]
        assert "aarch64-apple-darwin" in url
        assert "3.13.1" in url
        assert "install_only_stripped" in url
        assert url.endswith(".tar.gz")

    def test_url_format_windows_uses_shared(self, tmp_path: Path) -> None:
        """Windows uses -shared variant for python-build-standalone."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tf:
            data = b"fake"
            info = tarfile.TarInfo(name="python/install/python.exe")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
        tar_content = tar_buffer.getvalue()

        mock_response = MagicMock()
        mock_response.iter_bytes.return_value = [tar_content]
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch("trellis.toolchain.python_standalone.BIN_DIR", tmp_path),
            patch("trellis.toolchain.python_standalone.PYTHON_STANDALONE_VERSION", "3.13.1"),
            patch(
                "trellis.toolchain.python_standalone.get_rust_target",
                return_value="x86_64-pc-windows-msvc",
            ),
            patch("httpx.stream", return_value=mock_response) as mock_stream,
        ):
            ensure_python_standalone()

        url = mock_stream.call_args[0][1]
        assert "shared-install_only_stripped" in url

    def test_cleans_up_archive(self, tmp_path: Path) -> None:
        """Deletes archive after extraction."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tf:
            data = b"fake"
            info = tarfile.TarInfo(name="python/install/bin/python3")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
        tar_content = tar_buffer.getvalue()

        mock_response = MagicMock()
        mock_response.iter_bytes.return_value = [tar_content]
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch("trellis.toolchain.python_standalone.BIN_DIR", tmp_path),
            patch("trellis.toolchain.python_standalone.PYTHON_STANDALONE_VERSION", "3.13.1"),
            patch(
                "trellis.toolchain.python_standalone.get_rust_target",
                return_value="aarch64-apple-darwin",
            ),
            patch("httpx.stream", return_value=mock_response),
        ):
            ensure_python_standalone()

        archive_files = list(tmp_path.glob("*.tar.gz"))
        assert len(archive_files) == 0
