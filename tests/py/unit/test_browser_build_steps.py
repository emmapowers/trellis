"""Unit tests for browser platform build steps."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from trellis.bundler.steps import BuildContext
from trellis.platforms.browser.build_steps import (
    PythonSourceBundleStep,
    WheelCopyStep,
    build_source_config,
)


class TestPythonSourceBundleStep:
    """Tests for PythonSourceBundleStep."""

    def _make_context(self, tmp_path: Path, **kwargs) -> BuildContext:
        """Create a BuildContext for testing."""
        mock_registry = MagicMock()
        mock_collected = MagicMock()
        return BuildContext(
            registry=mock_registry,
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=mock_collected,
            dist_dir=tmp_path / "dist",
            **kwargs,
        )

    def test_skips_when_no_entry_point(self, tmp_path: Path) -> None:
        """Step is a no-op when python_entry_point is None."""
        ctx = self._make_context(tmp_path)
        step = PythonSourceBundleStep()

        step.run(ctx)

        # template_context should remain empty
        assert "source_json" not in ctx.template_context

    def test_adds_source_json_for_single_file(self, tmp_path: Path) -> None:
        """Step adds source_json to template_context for single file."""
        # Create a single Python file
        app_file = tmp_path / "app.py"
        app_file.write_text("print('hello')")

        ctx = self._make_context(tmp_path, python_entry_point=app_file)
        step = PythonSourceBundleStep()

        step.run(ctx)

        assert "source_json" in ctx.template_context
        source_json = ctx.template_context["source_json"]
        assert '"type": "code"' in source_json
        assert "print('hello')" in source_json

    def test_adds_source_json_for_package(self, tmp_path: Path) -> None:
        """Step adds source_json to template_context for package."""
        # Create a package
        pkg = tmp_path / "myapp"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("# init")
        (pkg / "__main__.py").write_text("print('main')")

        ctx = self._make_context(tmp_path, python_entry_point=pkg / "__main__.py")
        step = PythonSourceBundleStep()

        step.run(ctx)

        assert "source_json" in ctx.template_context
        source_json = ctx.template_context["source_json"]
        assert '"type": "module"' in source_json
        assert '"moduleName": "myapp"' in source_json

    def test_adds_routing_mode_to_context(self, tmp_path: Path) -> None:
        """Step adds routing_mode to template_context."""
        app_file = tmp_path / "app.py"
        app_file.write_text("x = 1")

        ctx = self._make_context(tmp_path, python_entry_point=app_file)
        step = PythonSourceBundleStep()

        step.run(ctx)

        assert ctx.template_context["routing_mode"] == "hash_url"

    def test_escapes_script_tags_in_source(self, tmp_path: Path) -> None:
        """Step escapes </script> in source to prevent XSS."""
        app_file = tmp_path / "app.py"
        app_file.write_text('x = "</script><script>alert(1)</script>"')

        ctx = self._make_context(tmp_path, python_entry_point=app_file)
        step = PythonSourceBundleStep()

        step.run(ctx)

        source_json = ctx.template_context["source_json"]
        # Should escape </ to <\/
        assert "</script>" not in source_json
        assert r"<\/script>" in source_json

    def test_step_name(self) -> None:
        """Step has correct name."""
        step = PythonSourceBundleStep()
        assert step.name == "python-source-bundle"


class TestWheelCopyStep:
    """Tests for WheelCopyStep."""

    def _make_context(self, tmp_path: Path, **kwargs) -> BuildContext:
        """Create a BuildContext for testing."""
        mock_registry = MagicMock()
        mock_collected = MagicMock()
        dist_dir = tmp_path / "build_dist"
        dist_dir.mkdir(parents=True, exist_ok=True)
        return BuildContext(
            registry=mock_registry,
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=mock_collected,
            dist_dir=dist_dir,
            **kwargs,
        )

    def test_copies_wheel_to_dist(self, tmp_path: Path) -> None:
        """Step copies trellis wheel from project dist/ to build dist_dir."""
        # Create a fake project dist with wheel
        project_dist = tmp_path / "project" / "dist"
        project_dist.mkdir(parents=True)
        wheel_file = project_dist / "trellis-0.1.0-py3-none-any.whl"
        wheel_file.write_text("fake wheel content")

        ctx = self._make_context(tmp_path)
        step = WheelCopyStep(project_dist)

        step.run(ctx)

        # Wheel should be copied to build dist_dir
        copied_wheel = ctx.dist_dir / "trellis-0.1.0-py3-none-any.whl"
        assert copied_wheel.exists()
        assert copied_wheel.read_text() == "fake wheel content"

    def test_raises_when_no_wheel_found(self, tmp_path: Path) -> None:
        """Step raises RuntimeError when no wheel is found."""
        # Empty project dist
        project_dist = tmp_path / "project" / "dist"
        project_dist.mkdir(parents=True)

        ctx = self._make_context(tmp_path)
        step = WheelCopyStep(project_dist)

        with pytest.raises(RuntimeError, match=r"trellis wheel not found"):
            step.run(ctx)

    def test_raises_when_dist_dir_not_exists(self, tmp_path: Path) -> None:
        """Step raises RuntimeError when project dist/ doesn't exist."""
        project_dist = tmp_path / "nonexistent" / "dist"

        ctx = self._make_context(tmp_path)
        step = WheelCopyStep(project_dist)

        with pytest.raises(RuntimeError, match=r"trellis wheel not found"):
            step.run(ctx)

    def test_uses_latest_wheel_when_multiple(self, tmp_path: Path) -> None:
        """Step uses most recent wheel when multiple exist."""
        project_dist = tmp_path / "project" / "dist"
        project_dist.mkdir(parents=True)

        # Create older wheel
        old_wheel = project_dist / "trellis-0.1.0-py3-none-any.whl"
        old_wheel.write_text("old wheel")

        # Small delay to ensure different mtime
        time.sleep(0.01)

        # Create newer wheel
        new_wheel = project_dist / "trellis-0.2.0-py3-none-any.whl"
        new_wheel.write_text("new wheel")

        ctx = self._make_context(tmp_path)
        step = WheelCopyStep(project_dist)

        step.run(ctx)

        # Should copy the newer wheel
        wheels = list(ctx.dist_dir.glob("*.whl"))
        assert len(wheels) == 1
        assert wheels[0].read_text() == "new wheel"

    def test_step_name(self) -> None:
        """Step has correct name."""
        step = WheelCopyStep(Path("/fake"))
        assert step.name == "wheel-copy"


class TestBuildSourceConfig:
    """Tests for build_source_config function."""

    def test_single_file_returns_code_type(self, tmp_path: Path) -> None:
        """Returns type='code' config for single file outside package."""
        source = tmp_path / "script.py"
        source.write_text("print('hello')")

        result = build_source_config(source)

        assert result["type"] == "code"
        assert result["code"] == "print('hello')"

    def test_package_returns_module_type(self, tmp_path: Path) -> None:
        """Returns type='module' config for file inside package."""
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("# init")
        source = pkg / "main.py"
        source.write_text("# main")

        result = build_source_config(source)

        assert result["type"] == "module"
        assert "files" in result
        assert "mypkg/__init__.py" in result["files"]
        assert "mypkg/main.py" in result["files"]

    def test_package_uses_explicit_module_name(self, tmp_path: Path) -> None:
        """Uses explicit module_name when provided."""
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        source = pkg / "__main__.py"
        source.write_text("# main")

        result = build_source_config(source, module_name="mypkg")

        assert result["type"] == "module"
        assert result["moduleName"] == "mypkg"

    def test_package_infers_module_name_from_file(self, tmp_path: Path) -> None:
        """Infers module name from file path when not provided."""
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        source = pkg / "app.py"
        source.write_text("# app")

        result = build_source_config(source)

        # Should infer mypkg.app from the file path
        assert result["moduleName"] == "mypkg.app"

    def test_package_with_main_infers_package_name(self, tmp_path: Path) -> None:
        """Infers package name when __main__.py is the entry point."""
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        source = pkg / "__main__.py"
        source.write_text("# main")

        result = build_source_config(source)

        # __main__.py means run as package, so moduleName is just the package
        assert result["moduleName"] == "mypkg"

    def test_nested_package_infers_full_module_path(self, tmp_path: Path) -> None:
        """Infers full dotted module path for nested packages."""
        foo = tmp_path / "foo"
        foo.mkdir()
        (foo / "__init__.py").write_text("")

        bar = foo / "bar"
        bar.mkdir()
        (bar / "__init__.py").write_text("")

        source = bar / "baz.py"
        source.write_text("# baz")

        result = build_source_config(source)

        assert result["moduleName"] == "foo.bar.baz"
