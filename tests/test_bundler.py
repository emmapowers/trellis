"""Unit tests for trellis.bundler module."""

from __future__ import annotations

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
