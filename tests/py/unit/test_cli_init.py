"""Tests for the trellis init CLI command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from trellis.cli import trellis
from trellis.cli.init import (
    _check_conflicts,
    _is_valid_package_name,
    _render_template_tree,
    _to_package_name,
)

TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "src" / "trellis" / "cli" / "project_template"


# =============================================================================
# _to_package_name
# =============================================================================


class TestToPackageName:
    def test_lowercase(self) -> None:
        assert _to_package_name("MyApp") == "myapp"

    def test_hyphens_to_underscores(self) -> None:
        assert _to_package_name("my-app") == "my_app"

    def test_spaces_to_underscores(self) -> None:
        assert _to_package_name("my app") == "my_app"

    def test_mixed(self) -> None:
        assert _to_package_name("My Cool-App") == "my_cool_app"

    def test_already_valid(self) -> None:
        assert _to_package_name("hello") == "hello"

    def test_consecutive_separators_collapsed(self) -> None:
        assert _to_package_name("my--app") == "my_app"

    def test_leading_trailing_separators_stripped(self) -> None:
        assert _to_package_name("-my-app-") == "my_app"


# =============================================================================
# _is_valid_package_name
# =============================================================================


class TestIsValidPackageName:
    def test_valid_simple(self) -> None:
        assert _is_valid_package_name("myapp") is True

    def test_valid_with_underscores(self) -> None:
        assert _is_valid_package_name("my_app") is True

    def test_invalid_starts_with_digit(self) -> None:
        assert _is_valid_package_name("3app") is False

    def test_invalid_has_hyphen(self) -> None:
        assert _is_valid_package_name("my-app") is False

    def test_invalid_python_keyword(self) -> None:
        assert _is_valid_package_name("class") is False

    def test_invalid_empty(self) -> None:
        assert _is_valid_package_name("") is False

    def test_valid_with_digits(self) -> None:
        assert _is_valid_package_name("app2") is True


# =============================================================================
# _check_conflicts
# =============================================================================


class TestCheckConflicts:
    def test_no_conflicts_empty_dir(self, tmp_path: Path) -> None:
        dest = tmp_path / "project"
        dest.mkdir()
        conflicts = _check_conflicts(dest, TEMPLATE_DIR, "myapp")
        assert conflicts == []

    def test_detects_file_conflict(self, tmp_path: Path) -> None:
        dest = tmp_path / "project"
        dest.mkdir()
        (dest / "pyproject.toml").write_text("existing")
        conflicts = _check_conflicts(dest, TEMPLATE_DIR, "myapp")
        assert Path("pyproject.toml") in conflicts

    def test_detects_package_dir_conflict(self, tmp_path: Path) -> None:
        dest = tmp_path / "project"
        dest.mkdir()
        pkg = dest / "myapp"
        pkg.mkdir()
        (pkg / "app.py").write_text("existing")
        conflicts = _check_conflicts(dest, TEMPLATE_DIR, "myapp")
        assert Path("myapp/app.py") in conflicts

    def test_nonexistent_dest_no_conflicts(self, tmp_path: Path) -> None:
        dest = tmp_path / "does_not_exist"
        conflicts = _check_conflicts(dest, TEMPLATE_DIR, "myapp")
        assert conflicts == []


# =============================================================================
# _render_template_tree
# =============================================================================


class TestRenderTemplateTree:
    def test_renders_all_template_files(self, tmp_path: Path) -> None:
        context = {
            "name": "my-app",
            "title": "My App",
            "package_name": "my_app",
            "module": "my_app.app",
            "platform": "server",
            "platform_upper": "SERVER",
        }
        _render_template_tree(TEMPLATE_DIR, tmp_path, context)

        assert (tmp_path / "pyproject.toml").exists()
        assert (tmp_path / "trellis_config.py").exists()
        assert (tmp_path / "README.md").exists()
        assert (tmp_path / "my_app" / "__init__.py").exists()
        assert (tmp_path / "my_app" / "app.py").exists()

    def test_j2_suffix_stripped(self, tmp_path: Path) -> None:
        context = {
            "name": "test",
            "title": "Test",
            "package_name": "test_pkg",
            "module": "test_pkg.app",
            "platform": "server",
            "platform_upper": "SERVER",
        }
        _render_template_tree(TEMPLATE_DIR, tmp_path, context)

        # No .j2 files should exist in output
        j2_files = list(tmp_path.rglob("*.j2"))
        assert j2_files == []

    def test_package_name_substituted_in_directory(self, tmp_path: Path) -> None:
        context = {
            "name": "cool-project",
            "title": "Cool Project",
            "package_name": "cool_project",
            "module": "cool_project.app",
            "platform": "server",
            "platform_upper": "SERVER",
        }
        _render_template_tree(TEMPLATE_DIR, tmp_path, context)

        assert (tmp_path / "cool_project").is_dir()
        # __package_name__ directory should NOT exist
        assert not (tmp_path / "__package_name__").exists()

    def test_template_variables_rendered(self, tmp_path: Path) -> None:
        context = {
            "name": "my-app",
            "title": "My App",
            "package_name": "my_app",
            "module": "my_app.app",
            "platform": "server",
            "platform_upper": "SERVER",
        }
        _render_template_tree(TEMPLATE_DIR, tmp_path, context)

        config_content = (tmp_path / "trellis_config.py").read_text()
        assert "my-app" in config_content
        assert "my_app.app" in config_content

    def test_pyproject_contains_project_name(self, tmp_path: Path) -> None:
        context = {
            "name": "my-app",
            "title": "My App",
            "package_name": "my_app",
            "module": "my_app.app",
            "platform": "server",
            "platform_upper": "SERVER",
        }
        _render_template_tree(TEMPLATE_DIR, tmp_path, context)

        pyproject = (tmp_path / "pyproject.toml").read_text()
        assert 'name = "my-app"' in pyproject

    def test_browser_platform_rendered(self, tmp_path: Path) -> None:
        context = {
            "name": "browser-app",
            "title": "Browser App",
            "package_name": "browser_app",
            "module": "browser_app.app",
            "platform": "browser",
            "platform_upper": "BROWSER",
        }
        _render_template_tree(TEMPLATE_DIR, tmp_path, context)

        config_content = (tmp_path / "trellis_config.py").read_text()
        assert "BROWSER" in config_content


# =============================================================================
# CLI Integration
# =============================================================================


class TestInitCommandExists:
    def test_init_in_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(trellis, ["--help"])
        assert "init" in result.output

    def test_init_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(trellis, ["init", "--help"])
        assert result.exit_code == 0
        assert "--name" in result.output
        assert "--title" in result.output
        assert "--platform" in result.output
        assert "--directory" in result.output


class TestInitNonInteractive:
    """Test init with all CLI flags provided (no prompts)."""

    def test_creates_project(self, tmp_path: Path) -> None:
        dest = tmp_path / "my_app"
        runner = CliRunner()
        result = runner.invoke(trellis, ["init", "--name", "my-app", "--directory", str(dest)])
        assert result.exit_code == 0, f"output: {result.output}"
        assert (dest / "pyproject.toml").exists()
        assert (dest / "trellis_config.py").exists()
        assert (dest / "my_app" / "__init__.py").exists()
        assert (dest / "my_app" / "app.py").exists()

    def test_title_defaults_to_titlecased_name(self, tmp_path: Path) -> None:
        dest = tmp_path / "my_app"
        runner = CliRunner()
        result = runner.invoke(trellis, ["init", "--name", "my-app", "--directory", str(dest)])
        assert result.exit_code == 0, f"output: {result.output}"
        readme = (dest / "README.md").read_text()
        assert "My App" in readme

    def test_custom_title(self, tmp_path: Path) -> None:
        dest = tmp_path / "my_app"
        runner = CliRunner()
        result = runner.invoke(
            trellis,
            ["init", "--name", "my-app", "--title", "Custom Title", "--directory", str(dest)],
        )
        assert result.exit_code == 0, f"output: {result.output}"
        readme = (dest / "README.md").read_text()
        assert "Custom Title" in readme

    def test_custom_platform(self, tmp_path: Path) -> None:
        dest = tmp_path / "my_app"
        runner = CliRunner()
        result = runner.invoke(
            trellis,
            ["init", "--name", "my-app", "--platform", "desktop", "--directory", str(dest)],
        )
        assert result.exit_code == 0, f"output: {result.output}"
        config = (dest / "trellis_config.py").read_text()
        assert "DESKTOP" in config

    def test_directory_defaults_to_package_name(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(trellis, ["init", "--name", "my-app"])
            assert result.exit_code == 0, f"output: {result.output}"
            assert (Path(td) / "my_app" / "pyproject.toml").exists()

    def test_creates_destination_directory(self, tmp_path: Path) -> None:
        dest = tmp_path / "nested" / "project"
        runner = CliRunner()
        result = runner.invoke(trellis, ["init", "--name", "my-app", "--directory", str(dest)])
        assert result.exit_code == 0, f"output: {result.output}"
        assert dest.is_dir()


class TestInitValidation:
    def test_rejects_invalid_package_name(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            trellis, ["init", "--name", "123bad", "--directory", str(tmp_path / "out")]
        )
        assert result.exit_code != 0
        assert "valid Python package name" in result.output

    def test_detects_conflicts(self, tmp_path: Path) -> None:
        dest = tmp_path / "project"
        dest.mkdir()
        (dest / "pyproject.toml").write_text("existing")
        runner = CliRunner()
        result = runner.invoke(trellis, ["init", "--name", "project", "--directory", str(dest)])
        assert result.exit_code != 0
        assert "already exist" in result.output.lower()


class TestInitInteractive:
    """Test interactive prompts when flags are omitted."""

    @patch("trellis.cli.init._ask_select")
    @patch("trellis.cli.init._ask_text")
    def test_prompts_for_all_when_no_flags(
        self, mock_text: MagicMock, mock_select: MagicMock, tmp_path: Path
    ) -> None:
        mock_text.side_effect = [
            "my-app",  # name
            "My App",  # title
            str(tmp_path / "my_app"),  # directory
        ]
        mock_select.return_value = "server"  # platform
        runner = CliRunner()
        result = runner.invoke(trellis, ["init"])
        assert result.exit_code == 0, f"output: {result.output}"
        assert (tmp_path / "my_app" / "pyproject.toml").exists()
        assert mock_text.call_count == 3
        assert mock_select.call_count == 1

    @patch("trellis.cli.init._ask_select")
    @patch("trellis.cli.init._ask_text")
    def test_skips_prompts_when_flags_given(
        self, mock_text: MagicMock, mock_select: MagicMock, tmp_path: Path
    ) -> None:
        dest = tmp_path / "my_app"
        runner = CliRunner()
        result = runner.invoke(
            trellis,
            [
                "init",
                "--name",
                "my-app",
                "--title",
                "My App",
                "--platform",
                "server",
                "--directory",
                str(dest),
            ],
        )
        assert result.exit_code == 0, f"output: {result.output}"
        mock_text.assert_not_called()
        mock_select.assert_not_called()

    @patch("trellis.cli.init._ask_select")
    @patch("trellis.cli.init._ask_text")
    def test_no_prompts_when_name_given(
        self, mock_text: MagicMock, mock_select: MagicMock, tmp_path: Path
    ) -> None:
        # Providing --name triggers non-interactive mode; defaults are applied silently
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(trellis, ["init", "--name", "my-app"])
        assert result.exit_code == 0, f"output: {result.output}"
        mock_text.assert_not_called()
        mock_select.assert_not_called()
