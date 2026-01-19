"""Unit tests for trellis.bundler.python_source module."""

from __future__ import annotations

from pathlib import Path

from trellis.bundler.python_source import (
    collect_package_files,
    find_package_root,
)


class TestFindPackageRoot:
    """Tests for find_package_root function."""

    def test_returns_topmost_package(self, tmp_path: Path) -> None:
        """Returns topmost package directory when nested packages exist."""
        # Create nested packages: foo/bar/baz.py
        foo = tmp_path / "foo"
        foo.mkdir()
        (foo / "__init__.py").write_text("")

        bar = foo / "bar"
        bar.mkdir()
        (bar / "__init__.py").write_text("")

        source = bar / "baz.py"
        source.write_text("x = 1")

        result = find_package_root(source)
        assert result == foo

    def test_returns_single_package_root(self, tmp_path: Path) -> None:
        """Returns package directory for single-level package."""
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        source = pkg / "main.py"
        source.write_text("x = 1")

        result = find_package_root(source)
        assert result == pkg

    def test_returns_none_for_non_package(self, tmp_path: Path) -> None:
        """Returns None when source is not in a package."""
        source = tmp_path / "script.py"
        source.write_text("x = 1")

        result = find_package_root(source)
        assert result is None

    def test_returns_none_for_file_next_to_package(self, tmp_path: Path) -> None:
        """Returns None when file is next to a package but not inside it."""
        # Create a package
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")

        # Source file is next to the package, not inside
        source = tmp_path / "script.py"
        source.write_text("x = 1")

        result = find_package_root(source)
        assert result is None


class TestCollectPackageFiles:
    """Tests for collect_package_files function."""

    def test_returns_all_py_files(self, tmp_path: Path) -> None:
        """Returns all .py files in the package."""
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("# init")
        (pkg / "main.py").write_text("# main")
        (pkg / "utils.py").write_text("# utils")

        result = collect_package_files(pkg)

        assert len(result) == 3
        assert "mypkg/__init__.py" in result
        assert "mypkg/main.py" in result
        assert "mypkg/utils.py" in result
        assert result["mypkg/main.py"] == "# main"

    def test_includes_nested_files(self, tmp_path: Path) -> None:
        """Includes files in nested subdirectories."""
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")

        subpkg = pkg / "sub"
        subpkg.mkdir()
        (subpkg / "__init__.py").write_text("")
        (subpkg / "deep.py").write_text("# deep")

        result = collect_package_files(pkg)

        assert "mypkg/sub/__init__.py" in result
        assert "mypkg/sub/deep.py" in result
        assert result["mypkg/sub/deep.py"] == "# deep"

    def test_excludes_pycache(self, tmp_path: Path) -> None:
        """Excludes __pycache__ directories."""
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "main.py").write_text("# main")

        # Create pycache
        pycache = pkg / "__pycache__"
        pycache.mkdir()
        (pycache / "main.cpython-313.pyc").write_text("bytecode")

        result = collect_package_files(pkg)

        assert len(result) == 2
        assert "__pycache__" not in str(result)

    def test_excludes_hidden_directories(self, tmp_path: Path) -> None:
        """Excludes .hidden directories."""
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")

        hidden = pkg / ".hidden"
        hidden.mkdir()
        (hidden / "secret.py").write_text("# secret")

        result = collect_package_files(pkg)

        assert len(result) == 1
        assert ".hidden" not in str(result)
