"""Unit tests for trellis.bundler module."""

from __future__ import annotations

import io
import tarfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestGetPlatform:
    def test_darwin_arm64(self) -> None:
        """Returns darwin-arm64 for macOS ARM."""
        from trellis.bundler import _get_platform

        with patch("platform.system", return_value="Darwin"):
            with patch("platform.machine", return_value="arm64"):
                assert _get_platform() == "darwin-arm64"

    def test_darwin_x64(self) -> None:
        """Returns darwin-x64 for macOS Intel."""
        from trellis.bundler import _get_platform

        with patch("platform.system", return_value="Darwin"):
            with patch("platform.machine", return_value="x86_64"):
                assert _get_platform() == "darwin-x64"

    def test_linux_x64(self) -> None:
        """Returns linux-x64 for Linux x86_64."""
        from trellis.bundler import _get_platform

        with patch("platform.system", return_value="Linux"):
            with patch("platform.machine", return_value="x86_64"):
                assert _get_platform() == "linux-x64"

    def test_linux_arm64(self) -> None:
        """Returns linux-arm64 for Linux aarch64."""
        from trellis.bundler import _get_platform

        with patch("platform.system", return_value="Linux"):
            with patch("platform.machine", return_value="aarch64"):
                assert _get_platform() == "linux-arm64"

    def test_windows_x64(self) -> None:
        """Returns win32-x64 for Windows x64."""
        from trellis.bundler import _get_platform

        with patch("platform.system", return_value="Windows"):
            with patch("platform.machine", return_value="AMD64"):
                assert _get_platform() == "win32-x64"

    def test_unsupported_os(self) -> None:
        """Raises RuntimeError for unsupported OS."""
        from trellis.bundler import _get_platform

        with patch("platform.system", return_value="FreeBSD"):
            with patch("platform.machine", return_value="x86_64"):
                with pytest.raises(RuntimeError, match="Unsupported platform"):
                    _get_platform()

    def test_unsupported_arch(self) -> None:
        """Raises RuntimeError for unsupported architecture."""
        from trellis.bundler import _get_platform

        with patch("platform.system", return_value="Linux"):
            with patch("platform.machine", return_value="riscv64"):
                with pytest.raises(RuntimeError, match="Unsupported platform"):
                    _get_platform()


class TestSafeExtract:
    """Tests for _safe_extract tarball security."""

    def test_safe_extract_normal_paths(self, tmp_path: Path) -> None:
        """Normal paths extract successfully."""
        from trellis.bundler import _safe_extract

        # Create a tarball with normal paths
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
            # Add a file
            data = b"hello world"
            info = tarfile.TarInfo(name="package/index.js")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

            # Add a subdirectory file
            data2 = b"nested content"
            info2 = tarfile.TarInfo(name="package/lib/utils.js")
            info2.size = len(data2)
            tar.addfile(info2, io.BytesIO(data2))

        tar_buffer.seek(0)
        with tarfile.open(fileobj=tar_buffer, mode="r:gz") as tar:
            _safe_extract(tar, tmp_path)

        assert (tmp_path / "package" / "index.js").read_bytes() == b"hello world"
        assert (tmp_path / "package" / "lib" / "utils.js").read_bytes() == b"nested content"

    def test_safe_extract_rejects_parent_traversal(self, tmp_path: Path) -> None:
        """Rejects paths with parent directory traversal."""
        from trellis.bundler import _safe_extract

        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
            data = b"malicious"
            info = tarfile.TarInfo(name="../../../etc/passwd")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

        tar_buffer.seek(0)
        with tarfile.open(fileobj=tar_buffer, mode="r:gz") as tar:
            with pytest.raises(ValueError, match="path traversal"):
                _safe_extract(tar, tmp_path)

    def test_safe_extract_rejects_hidden_traversal(self, tmp_path: Path) -> None:
        """Rejects paths with hidden traversal in middle of path."""
        from trellis.bundler import _safe_extract

        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
            data = b"malicious"
            info = tarfile.TarInfo(name="package/../../../etc/passwd")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

        tar_buffer.seek(0)
        with tarfile.open(fileobj=tar_buffer, mode="r:gz") as tar:
            with pytest.raises(ValueError, match="path traversal"):
                _safe_extract(tar, tmp_path)

    def test_safe_extract_rejects_absolute_paths(self, tmp_path: Path) -> None:
        """Rejects absolute paths that escape destination."""
        from trellis.bundler import _safe_extract

        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
            data = b"malicious"
            info = tarfile.TarInfo(name="/etc/passwd")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

        tar_buffer.seek(0)
        with tarfile.open(fileobj=tar_buffer, mode="r:gz") as tar:
            with pytest.raises(ValueError, match="path traversal"):
                _safe_extract(tar, tmp_path)
