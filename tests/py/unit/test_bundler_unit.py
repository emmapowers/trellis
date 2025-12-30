"""Unit tests for trellis.bundler module."""

from __future__ import annotations

import io
import tarfile
from pathlib import Path
from unittest.mock import MagicMock, patch

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


class TestBundleConfig:
    """Tests for BundleConfig dataclass."""

    def test_static_files_default_is_none(self) -> None:
        """static_files defaults to None."""
        from trellis.bundler import BundleConfig

        config = BundleConfig(
            name="test",
            src_dir=Path("/src"),
            dist_dir=Path("/dist"),
            packages={},
        )
        assert config.static_files is None

    def test_static_files_can_be_set(self) -> None:
        """static_files can be configured as dict."""
        from trellis.bundler import BundleConfig

        config = BundleConfig(
            name="test",
            src_dir=Path("/src"),
            dist_dir=Path("/dist"),
            packages={},
            static_files={"index.html": Path("/src/index.html")},
        )
        assert config.static_files == {"index.html": Path("/src/index.html")}


class TestBuildBundleStaticFiles:
    """Tests for static file copying in build_bundle."""

    def test_copies_static_files_to_dist(self, tmp_path: Path) -> None:
        """Static files are copied to dist directory."""
        from trellis.bundler import BundleConfig, build_bundle

        # Set up directories
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        dist_dir = tmp_path / "dist"
        common_dir = tmp_path / "common"
        common_dir.mkdir()

        # Create source static file
        static_src = src_dir / "index.html"
        static_src.write_text("<html>test</html>")

        # Create minimal TypeScript file
        (src_dir / "main.tsx").write_text("export {}")

        config = BundleConfig(
            name="test",
            src_dir=src_dir,
            dist_dir=dist_dir,
            packages={},
            static_files={"index.html": static_src},
        )

        # Mock esbuild and package fetching to avoid network
        with patch("trellis.bundler.ensure_esbuild") as mock_esbuild:
            with patch("trellis.bundler.ensure_packages") as mock_packages:
                with patch("subprocess.run") as mock_run:
                    mock_esbuild.return_value = Path("/fake/esbuild")
                    mock_packages.return_value = Path("/fake/node_modules")
                    mock_run.return_value = MagicMock(returncode=0)

                    # Create the bundle.js that esbuild would create
                    dist_dir.mkdir(parents=True, exist_ok=True)
                    (dist_dir / "bundle.js").write_text("// bundle")

                    build_bundle(config, common_dir, force=True)

        # Verify static file was copied
        copied_file = dist_dir / "index.html"
        assert copied_file.exists()
        assert copied_file.read_text() == "<html>test</html>"
