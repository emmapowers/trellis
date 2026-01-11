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


class TestIsRebuildNeeded:
    """Tests for incremental build checking."""

    def test_rebuild_needed_when_output_missing(self, tmp_path: Path) -> None:
        """Rebuild is needed when output files don't exist."""
        from trellis.bundler.build import is_rebuild_needed

        input_file = tmp_path / "input.ts"
        input_file.write_text("const x = 1;")
        output_file = tmp_path / "bundle.js"
        # output doesn't exist

        assert is_rebuild_needed([input_file], [output_file]) is True

    def test_rebuild_not_needed_when_output_newer(self, tmp_path: Path) -> None:
        """Rebuild not needed when output is newer than all inputs."""
        import time

        from trellis.bundler.build import is_rebuild_needed

        input_file = tmp_path / "input.ts"
        input_file.write_text("const x = 1;")

        time.sleep(0.01)  # Ensure different mtime

        output_file = tmp_path / "bundle.js"
        output_file.write_text("bundled")

        assert is_rebuild_needed([input_file], [output_file]) is False

    def test_rebuild_needed_when_input_newer(self, tmp_path: Path) -> None:
        """Rebuild is needed when any input is newer than output."""
        import time

        from trellis.bundler.build import is_rebuild_needed

        output_file = tmp_path / "bundle.js"
        output_file.write_text("bundled")

        time.sleep(0.01)  # Ensure different mtime

        input_file = tmp_path / "input.ts"
        input_file.write_text("const x = 1;")

        assert is_rebuild_needed([input_file], [output_file]) is True

    def test_rebuild_needed_when_any_input_newer(self, tmp_path: Path) -> None:
        """Rebuild is needed when any one input is newer than output."""
        import time

        from trellis.bundler.build import is_rebuild_needed

        # Create inputs first
        input1 = tmp_path / "input1.ts"
        input1.write_text("const x = 1;")

        time.sleep(0.01)

        # Create output
        output_file = tmp_path / "bundle.js"
        output_file.write_text("bundled")

        time.sleep(0.01)

        # Create second input after output
        input2 = tmp_path / "input2.ts"
        input2.write_text("const y = 2;")

        assert is_rebuild_needed([input1, input2], [output_file]) is True

    def test_rebuild_checks_all_outputs(self, tmp_path: Path) -> None:
        """Rebuild is needed if any output is missing."""
        import time

        from trellis.bundler.build import is_rebuild_needed

        input_file = tmp_path / "input.ts"
        input_file.write_text("const x = 1;")

        time.sleep(0.01)

        output_js = tmp_path / "bundle.js"
        output_js.write_text("bundled")
        output_css = tmp_path / "bundle.css"
        # css doesn't exist

        assert is_rebuild_needed([input_file], [output_js, output_css]) is True

    def test_rebuild_not_needed_with_empty_inputs(self, tmp_path: Path) -> None:
        """No rebuild needed if no inputs (edge case)."""
        from trellis.bundler.build import is_rebuild_needed

        output_file = tmp_path / "bundle.js"
        output_file.write_text("bundled")

        assert is_rebuild_needed([], [output_file]) is False


class TestComputeSnippetsHash:
    """Tests for snippet hash computation."""

    def test_consistent_hash_for_same_snippets(self) -> None:
        """Same snippets produce same hash."""
        from trellis.bundler.build import compute_snippets_hash
        from trellis.bundler.registry import CollectedModules, Module

        module = Module(name="test", snippets={"helper.ts": "export const x = 1;"})
        collected = CollectedModules(modules=[module], packages={})

        hash1 = compute_snippets_hash(collected)
        hash2 = compute_snippets_hash(collected)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex digest

    def test_different_hash_for_different_content(self) -> None:
        """Different snippet content produces different hash."""
        from trellis.bundler.build import compute_snippets_hash
        from trellis.bundler.registry import CollectedModules, Module

        module1 = Module(name="test", snippets={"helper.ts": "export const x = 1;"})
        collected1 = CollectedModules(modules=[module1], packages={})

        module2 = Module(name="test", snippets={"helper.ts": "export const x = 2;"})
        collected2 = CollectedModules(modules=[module2], packages={})

        assert compute_snippets_hash(collected1) != compute_snippets_hash(collected2)

    def test_different_hash_for_different_filename(self) -> None:
        """Different snippet filename produces different hash."""
        from trellis.bundler.build import compute_snippets_hash
        from trellis.bundler.registry import CollectedModules, Module

        module1 = Module(name="test", snippets={"a.ts": "code"})
        collected1 = CollectedModules(modules=[module1], packages={})

        module2 = Module(name="test", snippets={"b.ts": "code"})
        collected2 = CollectedModules(modules=[module2], packages={})

        assert compute_snippets_hash(collected1) != compute_snippets_hash(collected2)

    def test_empty_snippets_returns_consistent_hash(self) -> None:
        """Empty snippets produce consistent hash."""
        from trellis.bundler.build import compute_snippets_hash
        from trellis.bundler.registry import CollectedModules, Module

        module = Module(name="test", snippets={})
        collected = CollectedModules(modules=[module], packages={})

        hash1 = compute_snippets_hash(collected)
        hash2 = compute_snippets_hash(collected)

        assert hash1 == hash2

    def test_hash_is_order_independent(self) -> None:
        """Hash is same regardless of module/snippet order."""
        from trellis.bundler.build import compute_snippets_hash
        from trellis.bundler.registry import CollectedModules, Module

        # Different order of modules
        mod_a = Module(name="aaa", snippets={"x.ts": "a"})
        mod_b = Module(name="bbb", snippets={"y.ts": "b"})

        collected1 = CollectedModules(modules=[mod_a, mod_b], packages={})
        collected2 = CollectedModules(modules=[mod_b, mod_a], packages={})

        assert compute_snippets_hash(collected1) == compute_snippets_hash(collected2)


class TestSnippetsHashFile:
    """Tests for snippet hash file integration."""

    def test_snippets_changed_triggers_rebuild(self, tmp_path: Path) -> None:
        """Changed snippets trigger rebuild even if files unchanged."""
        from trellis.bundler.build import compute_snippets_hash, snippets_changed
        from trellis.bundler.registry import CollectedModules, Module

        hash_file = tmp_path / ".snippets-hash"

        module = Module(name="test", snippets={"helper.ts": "export const x = 1;"})
        collected = CollectedModules(modules=[module], packages={})

        # First time - no hash file exists
        assert snippets_changed(collected, hash_file) is True

        # Write hash file
        hash_file.write_text(compute_snippets_hash(collected))

        # Same snippets - no change
        assert snippets_changed(collected, hash_file) is False

        # Different snippets - change detected
        module2 = Module(name="test", snippets={"helper.ts": "export const x = 2;"})
        collected2 = CollectedModules(modules=[module2], packages={})

        assert snippets_changed(collected2, hash_file) is True
