"""Unit tests for App configuration system."""

from __future__ import annotations

from pathlib import Path

import pytest

from trellis.app.app import App, find_app_path, get_app, set_app


class TestFindAppPath:
    """Tests for find_app_path function."""

    def test_finds_trellis_py_in_cwd(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """find_app_path finds trellis.py in current working directory."""
        (tmp_path / "trellis.py").write_text("config = None")
        monkeypatch.chdir(tmp_path)

        result = find_app_path()

        assert result == tmp_path

    def test_finds_trellis_py_in_parent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """find_app_path finds trellis.py in parent directory."""
        (tmp_path / "trellis.py").write_text("config = None")
        child = tmp_path / "subdir"
        child.mkdir()
        monkeypatch.chdir(child)

        result = find_app_path()

        assert result == tmp_path

    def test_finds_trellis_py_multiple_levels_up(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """find_app_path finds trellis.py multiple levels up."""
        (tmp_path / "trellis.py").write_text("config = None")
        deep = tmp_path / "a" / "b" / "c"
        deep.mkdir(parents=True)
        monkeypatch.chdir(deep)

        result = find_app_path()

        assert result == tmp_path

    def test_raises_when_not_found(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """find_app_path raises FileNotFoundError when trellis.py not found."""
        # tmp_path has no trellis.py
        monkeypatch.chdir(tmp_path)

        with pytest.raises(FileNotFoundError) as exc_info:
            find_app_path()

        assert "trellis.py not found" in str(exc_info.value)
        assert "trellis init" in str(exc_info.value)

    def test_returns_directory_not_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """find_app_path returns the directory containing trellis.py, not the file itself."""
        trellis_file = tmp_path / "trellis.py"
        trellis_file.write_text("config = None")
        monkeypatch.chdir(tmp_path)

        result = find_app_path()

        assert result.is_dir()
        assert result == tmp_path
        assert result != trellis_file

    def test_nearest_wins(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """find_app_path returns the nearest trellis.py when multiple exist."""
        # Create trellis.py in parent
        (tmp_path / "trellis.py").write_text("config = 'parent'")

        # Create trellis.py in child
        child = tmp_path / "subproject"
        child.mkdir()
        (child / "trellis.py").write_text("config = 'child'")

        monkeypatch.chdir(child)

        result = find_app_path()

        assert result == child


class TestApp:
    """Tests for App class."""

    def test_constructor_stores_path(self, tmp_path: Path) -> None:
        """App constructor stores the provided path."""
        app = App(tmp_path)

        assert app.path == tmp_path

    def test_config_is_none_before_load(self, tmp_path: Path) -> None:
        """App.config is None before load_config is called."""
        app = App(tmp_path)

        assert app.config is None

    def test_load_config_populates_config(self, tmp_path: Path) -> None:
        """load_config populates config attribute from trellis.py."""
        (tmp_path / "trellis.py").write_text(
            """
from trellis.app.config import Config

config = Config(name="my-app", module="my_app.main")
"""
        )
        app = App(tmp_path)

        app.load_config()

        assert app.config is not None
        assert app.config.name == "my-app"
        assert app.config.module == "my_app.main"

    def test_load_config_error_file_not_found(self, tmp_path: Path) -> None:
        """load_config raises FileNotFoundError when trellis.py doesn't exist."""
        app = App(tmp_path)

        with pytest.raises(FileNotFoundError) as exc_info:
            app.load_config()

        assert "trellis.py not found at" in str(exc_info.value)
        assert str(tmp_path) in str(exc_info.value)

    def test_load_config_error_syntax_error(self, tmp_path: Path) -> None:
        """load_config propagates SyntaxError from trellis.py."""
        (tmp_path / "trellis.py").write_text("def broken(")
        app = App(tmp_path)

        with pytest.raises(SyntaxError):
            app.load_config()

    def test_load_config_error_import_error(self, tmp_path: Path) -> None:
        """load_config propagates ImportError from trellis.py."""
        (tmp_path / "trellis.py").write_text("import nonexistent_module_xyz")
        app = App(tmp_path)

        with pytest.raises(ModuleNotFoundError):
            app.load_config()

    def test_load_config_error_no_config_variable(self, tmp_path: Path) -> None:
        """load_config raises ValueError when config variable not defined."""
        (tmp_path / "trellis.py").write_text("x = 1")
        app = App(tmp_path)

        with pytest.raises(ValueError, match="'config' variable not defined"):
            app.load_config()

    def test_load_config_error_wrong_type(self, tmp_path: Path) -> None:
        """load_config raises TypeError when config is not a Config instance."""
        (tmp_path / "trellis.py").write_text("config = {'name': 'test'}")
        app = App(tmp_path)

        with pytest.raises(TypeError) as exc_info:
            app.load_config()

        assert "'config' must be a Config instance" in str(exc_info.value)
        assert "got dict" in str(exc_info.value)
        assert "config = Config(name=..., module=...)" in str(exc_info.value)


class TestAppGlobals:
    """Tests for get_app/set_app global accessors."""

    @pytest.fixture(autouse=True)
    def reset_app(self) -> None:
        """Reset global _app before each test."""
        import trellis.app.app as app_module  # noqa: PLC0415

        app_module._app = None
        yield
        app_module._app = None

    def test_round_trip_works(self, tmp_path: Path) -> None:
        """set_app/get_app round trip works correctly."""
        app = App(tmp_path)

        set_app(app)
        result = get_app()

        assert result is app

    def test_get_app_before_set_raises(self) -> None:
        """get_app raises RuntimeError when called before set_app."""
        with pytest.raises(RuntimeError) as exc_info:
            get_app()

        assert "App not initialized" in str(exc_info.value)
        assert "set_app()" in str(exc_info.value)
        assert "find_app_path()" in str(exc_info.value)
