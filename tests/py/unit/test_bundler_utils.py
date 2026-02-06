"""Unit tests for bundler utilities."""

from __future__ import annotations

import io
import tarfile
import time
from pathlib import Path

import pytest

from trellis.bundler.utils import (
    _get_newest_mtime,
    is_rebuild_needed,
    safe_extract,
)


class TestGetNewestMtime:
    """Tests for _get_newest_mtime helper function."""

    def test_returns_file_mtime_for_single_file(self, tmp_path: Path) -> None:
        """_get_newest_mtime returns mtime of single file."""
        file = tmp_path / "test.txt"
        file.write_text("content")

        result = _get_newest_mtime(file)

        assert result == file.stat().st_mtime

    def test_returns_directory_mtime_for_empty_directory(self, tmp_path: Path) -> None:
        """_get_newest_mtime returns mtime of empty directory itself."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = _get_newest_mtime(empty_dir)

        assert result == empty_dir.stat().st_mtime

    def test_returns_newest_file_mtime_in_directory(self, tmp_path: Path) -> None:
        """_get_newest_mtime returns newest mtime among files in directory."""
        # Create old file
        old_file = tmp_path / "old.txt"
        old_file.write_text("old")
        time.sleep(0.01)

        # Create new file
        new_file = tmp_path / "new.txt"
        new_file.write_text("new")

        result = _get_newest_mtime(tmp_path)

        assert result == new_file.stat().st_mtime

    def test_finds_newest_in_nested_directories(self, tmp_path: Path) -> None:
        """_get_newest_mtime recursively finds newest file in nested structure."""
        # Create nested directory structure
        subdir = tmp_path / "sub"
        subdir.mkdir()
        deep_dir = subdir / "deep"
        deep_dir.mkdir()

        # Create old file at top
        old_file = tmp_path / "old.txt"
        old_file.write_text("old")
        time.sleep(0.01)

        # Create newest file in deep directory
        newest_file = deep_dir / "newest.txt"
        newest_file.write_text("newest")

        result = _get_newest_mtime(tmp_path)

        assert result == newest_file.stat().st_mtime

    def test_handles_directory_newer_than_contents(self, tmp_path: Path) -> None:
        """_get_newest_mtime returns directory mtime if newer than contents."""
        # Create file first
        file = tmp_path / "file.txt"
        file.write_text("content")
        file_mtime = file.stat().st_mtime
        time.sleep(0.01)

        # Create subdirectory (will be newer than file)
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        result = _get_newest_mtime(tmp_path)

        # Should return the subdir mtime (newest item)
        assert result >= subdir.stat().st_mtime
        assert result > file_mtime


class TestIsRebuildNeeded:
    """Tests for is_rebuild_needed helper function."""

    def test_returns_false_when_no_inputs(self, tmp_path: Path) -> None:
        """is_rebuild_needed returns False when no inputs provided."""
        output = tmp_path / "output.js"
        output.write_text("output")

        result = is_rebuild_needed(inputs=[], outputs=[output])

        assert result is False

    def test_returns_true_when_output_missing(self, tmp_path: Path) -> None:
        """is_rebuild_needed returns True when any output is missing."""
        input_file = tmp_path / "input.ts"
        input_file.write_text("input")
        output = tmp_path / "output.js"  # Does not exist

        result = is_rebuild_needed(inputs=[input_file], outputs=[output])

        assert result is True

    def test_returns_true_when_input_newer_than_output(self, tmp_path: Path) -> None:
        """is_rebuild_needed returns True when input is newer than output."""
        output = tmp_path / "output.js"
        output.write_text("output")

        # Wait to ensure different mtime
        time.sleep(0.01)

        input_file = tmp_path / "input.ts"
        input_file.write_text("input")  # Created after output

        result = is_rebuild_needed(inputs=[input_file], outputs=[output])

        assert result is True

    def test_returns_false_when_outputs_up_to_date(self, tmp_path: Path) -> None:
        """is_rebuild_needed returns False when outputs are newer than inputs."""
        input_file = tmp_path / "input.ts"
        input_file.write_text("input")

        # Wait to ensure different mtime
        time.sleep(0.01)

        output = tmp_path / "output.js"
        output.write_text("output")  # Created after input

        result = is_rebuild_needed(inputs=[input_file], outputs=[output])

        assert result is False

    def test_checks_all_outputs_exist(self, tmp_path: Path) -> None:
        """is_rebuild_needed returns True if any output is missing."""
        input_file = tmp_path / "input.ts"
        input_file.write_text("input")

        output1 = tmp_path / "output.js"
        output1.write_text("output1")
        output2 = tmp_path / "output.css"  # Does not exist

        result = is_rebuild_needed(inputs=[input_file], outputs=[output1, output2])

        assert result is True

    def test_uses_oldest_output_for_comparison(self, tmp_path: Path) -> None:
        """is_rebuild_needed uses oldest output mtime for comparison."""
        # Create input
        input_file = tmp_path / "input.ts"
        input_file.write_text("input")
        time.sleep(0.01)

        # Create old output
        old_output = tmp_path / "old.js"
        old_output.write_text("old")
        time.sleep(0.01)

        # Modify input (now newer than old output)
        input_file.write_text("modified input")
        time.sleep(0.01)

        # Create new output (newer than input)
        new_output = tmp_path / "new.js"
        new_output.write_text("new")

        # Should return True because input is newer than old_output
        result = is_rebuild_needed(inputs=[input_file], outputs=[old_output, new_output])

        assert result is True

    def test_handles_directory_inputs(self, tmp_path: Path) -> None:
        """is_rebuild_needed handles directory inputs with nested files."""
        # Create input directory with file
        input_dir = tmp_path / "src"
        input_dir.mkdir()
        input_file = input_dir / "module.ts"
        input_file.write_text("input")
        time.sleep(0.01)

        # Create output (newer than input)
        output = tmp_path / "bundle.js"
        output.write_text("output")

        result = is_rebuild_needed(inputs=[input_dir], outputs=[output])

        assert result is False

        # Now modify a file in the input directory
        time.sleep(0.01)
        input_file.write_text("modified")

        result = is_rebuild_needed(inputs=[input_dir], outputs=[output])

        assert result is True

    def test_detects_new_file_in_directory(self, tmp_path: Path) -> None:
        """is_rebuild_needed detects new files added to a directory input."""
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        (static_dir / "existing.txt").write_text("existing")

        # Create output after the directory contents
        time.sleep(0.01)
        output = tmp_path / "bundle.js"
        output.write_text("output")

        # Initially should be up to date
        assert is_rebuild_needed([static_dir], [output]) is False

        # Add a new file to the directory
        time.sleep(0.01)
        (static_dir / "new.txt").write_text("new file")

        # Now should need rebuild
        assert is_rebuild_needed([static_dir], [output]) is True

    def test_detects_modified_file_in_nested_dir(self, tmp_path: Path) -> None:
        """is_rebuild_needed detects modified files in nested directories."""
        static_dir = tmp_path / "static"
        nested_dir = static_dir / "assets" / "images"
        nested_dir.mkdir(parents=True)
        nested_file = nested_dir / "logo.png"
        nested_file.write_bytes(b"original")

        # Create output after the directory contents
        time.sleep(0.01)
        output = tmp_path / "bundle.js"
        output.write_text("output")

        # Initially should be up to date
        assert is_rebuild_needed([static_dir], [output]) is False

        # Modify the nested file
        time.sleep(0.01)
        nested_file.write_bytes(b"modified")

        # Now should need rebuild
        assert is_rebuild_needed([static_dir], [output]) is True

    def test_detects_deleted_file_in_directory(self, tmp_path: Path) -> None:
        """is_rebuild_needed detects when a file is deleted from directory.

        Note: Deletion typically updates the directory's mtime, which triggers rebuild.
        """
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        to_delete = static_dir / "deleteme.txt"
        to_delete.write_text("will be deleted")

        # Create output after the directory contents
        time.sleep(0.01)
        output = tmp_path / "bundle.js"
        output.write_text("output")

        # Initially should be up to date
        assert is_rebuild_needed([static_dir], [output]) is False

        # Delete the file (this updates directory mtime)
        time.sleep(0.01)
        to_delete.unlink()

        # Should need rebuild because directory was modified
        assert is_rebuild_needed([static_dir], [output]) is True

    def test_handles_mixed_files_and_directories(self, tmp_path: Path) -> None:
        """is_rebuild_needed handles a mix of file and directory inputs."""
        # Create a regular file
        source_file = tmp_path / "main.ts"
        source_file.write_text("// source")

        # Create a directory
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        (static_dir / "data.json").write_text("{}")

        # Create output after inputs
        time.sleep(0.01)
        output = tmp_path / "bundle.js"
        output.write_text("output")

        # Initially should be up to date
        assert is_rebuild_needed([source_file, static_dir], [output]) is False

        # Modify the source file
        time.sleep(0.01)
        source_file.write_text("// modified source")

        # Should need rebuild
        assert is_rebuild_needed([source_file, static_dir], [output]) is True

    def test_returns_true_when_input_missing(self, tmp_path: Path) -> None:
        """is_rebuild_needed returns True when input file doesn't exist."""
        output = tmp_path / "output.js"
        output.write_text("output")
        missing_input = tmp_path / "missing.ts"  # Does not exist

        result = is_rebuild_needed(inputs=[missing_input], outputs=[output])

        assert result is True

    def test_returns_true_when_any_input_missing(self, tmp_path: Path) -> None:
        """is_rebuild_needed returns True when any input in list is missing."""
        output = tmp_path / "output.js"
        output.write_text("output")
        existing_input = tmp_path / "exists.ts"
        existing_input.write_text("exists")
        missing_input = tmp_path / "missing.ts"  # Does not exist

        result = is_rebuild_needed(inputs=[existing_input, missing_input], outputs=[output])

        assert result is True


class TestSafeExtract:
    """Tests for safe_extract tarball security."""

    def test_extracts_normal_paths(self, tmp_path: Path) -> None:
        """Normal paths extract successfully."""
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
            safe_extract(tar, tmp_path)

        assert (tmp_path / "package" / "index.js").read_bytes() == b"hello world"
        assert (tmp_path / "package" / "lib" / "utils.js").read_bytes() == b"nested content"

    def test_rejects_parent_traversal(self, tmp_path: Path) -> None:
        """Rejects paths with parent directory traversal."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
            data = b"malicious"
            info = tarfile.TarInfo(name="../../../etc/passwd")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

        tar_buffer.seek(0)
        with tarfile.open(fileobj=tar_buffer, mode="r:gz") as tar:
            with pytest.raises(ValueError, match="path traversal"):
                safe_extract(tar, tmp_path)

    def test_rejects_hidden_traversal(self, tmp_path: Path) -> None:
        """Rejects paths with hidden traversal in middle of path."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
            data = b"malicious"
            info = tarfile.TarInfo(name="package/../../../etc/passwd")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

        tar_buffer.seek(0)
        with tarfile.open(fileobj=tar_buffer, mode="r:gz") as tar:
            with pytest.raises(ValueError, match="path traversal"):
                safe_extract(tar, tmp_path)

    def test_rejects_absolute_paths(self, tmp_path: Path) -> None:
        """Rejects absolute paths that escape destination."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
            data = b"malicious"
            info = tarfile.TarInfo(name="/etc/passwd")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

        tar_buffer.seek(0)
        with tarfile.open(fileobj=tar_buffer, mode="r:gz") as tar:
            with pytest.raises(ValueError, match="path traversal"):
                safe_extract(tar, tmp_path)

    def test_rejects_symlinks(self, tmp_path: Path) -> None:
        """Rejects symlink entries to prevent link-based escapes."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
            # Add a symlink pointing outside destination
            info = tarfile.TarInfo(name="package/link")
            info.type = tarfile.SYMTYPE
            info.linkname = "/etc/passwd"
            tar.addfile(info)

        tar_buffer.seek(0)
        with tarfile.open(fileobj=tar_buffer, mode="r:gz") as tar:
            with pytest.raises(ValueError, match="link entry"):
                safe_extract(tar, tmp_path)

    def test_rejects_hardlinks(self, tmp_path: Path) -> None:
        """Rejects hardlink entries to prevent link-based escapes."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
            # Add a hardlink
            info = tarfile.TarInfo(name="package/hardlink")
            info.type = tarfile.LNKTYPE
            info.linkname = "package/original"
            tar.addfile(info)

        tar_buffer.seek(0)
        with tarfile.open(fileobj=tar_buffer, mode="r:gz") as tar:
            with pytest.raises(ValueError, match="link entry"):
                safe_extract(tar, tmp_path)

    def test_rejects_character_device(self, tmp_path: Path) -> None:
        """Rejects character device entries."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
            info = tarfile.TarInfo(name="package/dev")
            info.type = tarfile.CHRTYPE
            tar.addfile(info)

        tar_buffer.seek(0)
        with tarfile.open(fileobj=tar_buffer, mode="r:gz") as tar:
            with pytest.raises(ValueError, match="device/fifo"):
                safe_extract(tar, tmp_path)

    def test_rejects_block_device(self, tmp_path: Path) -> None:
        """Rejects block device entries."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
            info = tarfile.TarInfo(name="package/blk")
            info.type = tarfile.BLKTYPE
            tar.addfile(info)

        tar_buffer.seek(0)
        with tarfile.open(fileobj=tar_buffer, mode="r:gz") as tar:
            with pytest.raises(ValueError, match="device/fifo"):
                safe_extract(tar, tmp_path)

    def test_rejects_fifo(self, tmp_path: Path) -> None:
        """Rejects FIFO/named pipe entries."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
            info = tarfile.TarInfo(name="package/pipe")
            info.type = tarfile.FIFOTYPE
            tar.addfile(info)

        tar_buffer.seek(0)
        with tarfile.open(fileobj=tar_buffer, mode="r:gz") as tar:
            with pytest.raises(ValueError, match="device/fifo"):
                safe_extract(tar, tmp_path)
