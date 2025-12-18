"""Unit tests for trellis.platforms.browser.serve_platform module."""

from __future__ import annotations

from pathlib import Path


class TestFindPackageRoot:
    """Tests for _find_package_root function."""

    def test_not_in_package_returns_none(self, tmp_path: Path) -> None:
        """Returns None when source is not in a package."""
        from trellis.platforms.browser.serve_platform import _find_package_root

        # Create a standalone Python file (no __init__.py)
        source_file = tmp_path / "standalone.py"
        source_file.write_text("# standalone")

        result = _find_package_root(source_file)
        assert result is None

    def test_single_level_package(self, tmp_path: Path) -> None:
        """Returns package directory for single-level package."""
        from trellis.platforms.browser.serve_platform import _find_package_root

        # Create a package: mypackage/__init__.py, mypackage/app.py
        pkg_dir = tmp_path / "mypackage"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        source_file = pkg_dir / "app.py"
        source_file.write_text("# app")

        result = _find_package_root(source_file)
        assert result == pkg_dir

    def test_nested_packages_returns_topmost(self, tmp_path: Path) -> None:
        """Returns topmost package directory for nested packages."""
        from trellis.platforms.browser.serve_platform import _find_package_root

        # Create nested packages: outer/inner/module.py
        outer = tmp_path / "outer"
        inner = outer / "inner"
        inner.mkdir(parents=True)
        (outer / "__init__.py").write_text("")
        (inner / "__init__.py").write_text("")
        source_file = inner / "module.py"
        source_file.write_text("# module")

        result = _find_package_root(source_file)
        assert result == outer

    def test_source_in_init_file(self, tmp_path: Path) -> None:
        """Works when source is the __init__.py itself."""
        from trellis.platforms.browser.serve_platform import _find_package_root

        pkg_dir = tmp_path / "mypackage"
        pkg_dir.mkdir()
        source_file = pkg_dir / "__init__.py"
        source_file.write_text("# init")

        result = _find_package_root(source_file)
        assert result == pkg_dir


class TestCollectPackageFiles:
    """Tests for _collect_package_files function."""

    def test_collects_all_py_files(self, tmp_path: Path) -> None:
        """Collects all .py files in package."""
        from trellis.platforms.browser.serve_platform import _collect_package_files

        pkg_dir = tmp_path / "mypackage"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("# init")
        (pkg_dir / "app.py").write_text("# app")
        (pkg_dir / "utils.py").write_text("# utils")

        result = _collect_package_files(pkg_dir)

        assert len(result) == 3
        assert "mypackage/__init__.py" in result
        assert "mypackage/app.py" in result
        assert "mypackage/utils.py" in result
        assert result["mypackage/app.py"] == "# app"

    def test_includes_nested_subdirectories(self, tmp_path: Path) -> None:
        """Includes files from nested subdirectories."""
        from trellis.platforms.browser.serve_platform import _collect_package_files

        pkg_dir = tmp_path / "mypackage"
        subpkg = pkg_dir / "sub"
        subpkg.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "main.py").write_text("# main")
        (subpkg / "__init__.py").write_text("")
        (subpkg / "helper.py").write_text("# helper")

        result = _collect_package_files(pkg_dir)

        assert len(result) == 4
        assert "mypackage/sub/helper.py" in result
        assert result["mypackage/sub/helper.py"] == "# helper"

    def test_ignores_non_py_files(self, tmp_path: Path) -> None:
        """Ignores non-.py files."""
        from trellis.platforms.browser.serve_platform import _collect_package_files

        pkg_dir = tmp_path / "mypackage"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "readme.md").write_text("# readme")
        (pkg_dir / "data.json").write_text("{}")

        result = _collect_package_files(pkg_dir)

        assert len(result) == 1
        assert "mypackage/__init__.py" in result


class TestDetectEntryPoint:
    """Tests for _detect_entry_point function."""

    def test_returns_main_file_path(self) -> None:
        """Returns the __main__ module's file path."""
        import sys
        from unittest.mock import MagicMock, patch
        from trellis.platforms.browser.serve_platform import _detect_entry_point

        # Mock __main__ module
        mock_main = MagicMock()
        mock_main.__file__ = "/path/to/script.py"
        mock_main.__spec__ = None

        with patch.dict(sys.modules, {"__main__": mock_main}):
            entry_path, module_name = _detect_entry_point()

        assert entry_path == Path("/path/to/script.py")
        assert module_name is None

    def test_returns_module_name_when_run_as_module(self) -> None:
        """Returns module name when run with python -m."""
        import sys
        from unittest.mock import MagicMock, patch
        from trellis.platforms.browser.serve_platform import _detect_entry_point

        # Mock __main__ module run as "python -m mypackage.module"
        mock_spec = MagicMock()
        mock_spec.name = "mypackage.module"

        mock_main = MagicMock()
        mock_main.__file__ = "/path/to/mypackage/module.py"
        mock_main.__spec__ = mock_spec

        with patch.dict(sys.modules, {"__main__": mock_main}):
            entry_path, module_name = _detect_entry_point()

        assert entry_path == Path("/path/to/mypackage/module.py")
        assert module_name == "mypackage.module"

    def test_raises_when_main_not_found(self) -> None:
        """Raises RuntimeError when __main__ is not in sys.modules."""
        import sys
        import pytest
        from unittest.mock import patch
        from trellis.platforms.browser.serve_platform import _detect_entry_point

        # Remove __main__ from modules
        with patch.dict(sys.modules, {"__main__": None}):
            with pytest.raises(RuntimeError, match="__main__ not found"):
                _detect_entry_point()

    def test_raises_when_file_not_set(self) -> None:
        """Raises RuntimeError when __main__.__file__ is None."""
        import sys
        import pytest
        from unittest.mock import MagicMock, patch
        from trellis.platforms.browser.serve_platform import _detect_entry_point

        mock_main = MagicMock()
        mock_main.__file__ = None

        with patch.dict(sys.modules, {"__main__": mock_main}):
            with pytest.raises(RuntimeError, match="__file__ not set"):
                _detect_entry_point()


class TestGenerateHtml:
    """Tests for _generate_html function."""

    def test_module_source_contains_files_json(self) -> None:
        """Generated HTML contains the files as JSON for module source."""
        from trellis.platforms.browser.serve_platform import _generate_html

        source = {
            "type": "module",
            "files": {
                "pkg/__init__.py": "",
                "pkg/app.py": "def App(): pass",
            },
            "moduleName": "pkg.app",
        }

        result = _generate_html(source)

        assert '"type": "module"' in result
        assert "pkg/__init__.py" in result
        assert "pkg/app.py" in result
        assert "pkg.app" in result

    def test_code_source_contains_code(self) -> None:
        """Generated HTML contains the code for code source."""
        from trellis.platforms.browser.serve_platform import _generate_html

        source = {"type": "code", "code": "print('hello')"}

        result = _generate_html(source)

        assert '"type": "code"' in result
        assert "print" in result
        assert "hello" in result

    def test_valid_html_structure(self) -> None:
        """Generated HTML has valid structure."""
        from trellis.platforms.browser.serve_platform import _generate_html

        source = {"type": "code", "code": "# test"}

        result = _generate_html(source)

        assert "<!DOCTYPE html>" in result
        assert "<html>" in result
        assert "</html>" in result
        assert '<div id="root"></div>' in result
        assert "bundle.js" in result
        assert "__TRELLIS_CONFIG__" in result

    def test_escapes_special_characters(self) -> None:
        """Properly escapes special characters in code."""
        from trellis.platforms.browser.serve_platform import _generate_html

        source = {
            "type": "module",
            "files": {
                "pkg/app.py": 'print("hello\\nworld")\n# Comment with "quotes"',
            },
            "moduleName": "pkg",
        }

        result = _generate_html(source)

        # Should not break JavaScript - JSON.dumps handles escaping
        assert "__TRELLIS_CONFIG__" in result
        # The escaped code should be in the output
        assert "pkg/app.py" in result
        # Verify HTML is well-formed
        assert "</script>" in result
        assert "</html>" in result

    def test_escapes_script_tags_in_code(self) -> None:
        """Code containing </script> is escaped to prevent HTML injection."""
        from trellis.platforms.browser.serve_platform import _generate_html

        # Code that tries to break out of the script context
        source = {
            "type": "code",
            "code": 'x = "</script><script>alert(1)</script>"',
        }

        result = _generate_html(source)

        # The closing script tag should be escaped
        assert r"<\/" in result or "<\\/" in result
        # The literal </script> should NOT appear in the code section
        # (it should only appear as the actual closing tag for the script element)
        script_section = result.split("<script>")[1].split("</script>")[0]
        assert "</script>" not in script_section
