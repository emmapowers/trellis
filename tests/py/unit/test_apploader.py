"""Unit tests for AppLoader configuration system."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

import pytest

from tests.helpers import requires_pytauri
from trellis.app.apploader import (
    AppLoader,
    find_app_path,
    get_app_root,
    get_apploader,
    get_config,
    set_apploader,
)
from trellis.platforms.browser import BrowserPlatform
from trellis.platforms.browser.serve_platform import BrowserServePlatform
from trellis.platforms.server import ServerPlatform


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


class TestAppLoader:
    """Tests for AppLoader class."""

    def test_constructor_stores_path(self, tmp_path: Path) -> None:
        """AppLoader constructor stores the provided path."""
        apploader = AppLoader(tmp_path)

        assert apploader.path == tmp_path

    def test_config_is_none_before_load(self, tmp_path: Path) -> None:
        """AppLoader.config is None before load_config is called."""
        apploader = AppLoader(tmp_path)

        assert apploader.config is None

    def test_load_config_populates_config(self, tmp_path: Path) -> None:
        """load_config populates config attribute from trellis.py."""
        (tmp_path / "trellis.py").write_text(
            """
from trellis.app.config import Config

config = Config(name="my-app", module="my_app.main")
"""
        )
        apploader = AppLoader(tmp_path)

        apploader.load_config()

        assert apploader.config is not None
        assert apploader.config.name == "my-app"
        assert apploader.config.module == "my_app.main"

    def test_load_config_error_file_not_found(self, tmp_path: Path) -> None:
        """load_config raises FileNotFoundError when trellis.py doesn't exist."""
        apploader = AppLoader(tmp_path)

        with pytest.raises(FileNotFoundError) as exc_info:
            apploader.load_config()

        assert "trellis.py not found at" in str(exc_info.value)
        assert str(tmp_path) in str(exc_info.value)

    def test_load_config_error_syntax_error(self, tmp_path: Path) -> None:
        """load_config propagates SyntaxError from trellis.py."""
        (tmp_path / "trellis.py").write_text("def broken(")
        apploader = AppLoader(tmp_path)

        with pytest.raises(SyntaxError):
            apploader.load_config()

    def test_load_config_error_import_error(self, tmp_path: Path) -> None:
        """load_config propagates ImportError from trellis.py."""
        (tmp_path / "trellis.py").write_text("import nonexistent_module_xyz")
        apploader = AppLoader(tmp_path)

        with pytest.raises(ModuleNotFoundError):
            apploader.load_config()

    def test_load_config_error_no_config_variable(self, tmp_path: Path) -> None:
        """load_config raises ValueError when config variable not defined."""
        (tmp_path / "trellis.py").write_text("x = 1")
        apploader = AppLoader(tmp_path)

        with pytest.raises(ValueError, match="'config' variable not defined"):
            apploader.load_config()

    def test_load_config_error_wrong_type(self, tmp_path: Path) -> None:
        """load_config raises TypeError when config is not a Config instance."""
        (tmp_path / "trellis.py").write_text("config = {'name': 'test'}")
        apploader = AppLoader(tmp_path)

        with pytest.raises(TypeError) as exc_info:
            apploader.load_config()

        assert "'config' must be a Config instance" in str(exc_info.value)
        assert "got dict" in str(exc_info.value)
        assert "config = Config(name=..., module=...)" in str(exc_info.value)


class TestAppLoaderImportModule:
    """Tests for AppLoader.import_module method."""

    def test_imports_simple_module(self, tmp_path: Path) -> None:
        """import_module imports a module in the app directory."""
        # Create trellis.py
        (tmp_path / "trellis.py").write_text(
            """
from trellis.app.config import Config
config = Config(name="test", module="myapp")
"""
        )
        # Create myapp.py
        (tmp_path / "myapp.py").write_text("VALUE = 42")

        apploader = AppLoader(tmp_path)
        apploader.load_config()

        module = apploader.import_module()

        assert module.VALUE == 42

    def test_imports_subpackage_module(self, tmp_path: Path) -> None:
        """import_module imports a module from a subpackage."""
        (tmp_path / "trellis.py").write_text(
            """
from trellis.app.config import Config
config = Config(name="test", module="mypkg.main")
"""
        )
        pkg_dir = tmp_path / "mypkg"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "main.py").write_text("VALUE = 'nested'")

        apploader = AppLoader(tmp_path)
        apploader.load_config()

        module = apploader.import_module()

        assert module.VALUE == "nested"

    def test_returns_module_object(self, tmp_path: Path) -> None:
        """import_module returns a ModuleType."""
        (tmp_path / "trellis.py").write_text(
            """
from trellis.app.config import Config
config = Config(name="test", module="myapp")
"""
        )
        (tmp_path / "myapp.py").write_text("")

        apploader = AppLoader(tmp_path)
        apploader.load_config()

        module = apploader.import_module()

        assert isinstance(module, ModuleType)

    def test_error_module_not_found(self, tmp_path: Path) -> None:
        """import_module raises ModuleNotFoundError with context when module doesn't exist."""
        (tmp_path / "trellis.py").write_text(
            """
from trellis.app.config import Config
config = Config(name="test", module="nonexistent")
"""
        )

        apploader = AppLoader(tmp_path)
        apploader.load_config()

        with pytest.raises(ModuleNotFoundError) as exc_info:
            apploader.import_module()

        assert "nonexistent" in str(exc_info.value)

    def test_error_config_not_loaded(self, tmp_path: Path) -> None:
        """import_module raises RuntimeError if config not loaded first."""
        apploader = AppLoader(tmp_path)

        with pytest.raises(RuntimeError, match=r"load_config.*first"):
            apploader.import_module()

    def test_propagates_syntax_error(self, tmp_path: Path) -> None:
        """import_module propagates SyntaxError from the module."""
        (tmp_path / "trellis.py").write_text(
            """
from trellis.app.config import Config
config = Config(name="test", module="broken")
"""
        )
        (tmp_path / "broken.py").write_text("def oops(")

        apploader = AppLoader(tmp_path)
        apploader.load_config()

        with pytest.raises(SyntaxError):
            apploader.import_module()

    def test_propagates_import_error(self, tmp_path: Path) -> None:
        """import_module propagates ImportError from module dependencies."""
        (tmp_path / "trellis.py").write_text(
            """
from trellis.app.config import Config
config = Config(name="test", module="has_bad_import")
"""
        )
        (tmp_path / "has_bad_import.py").write_text("import nonexistent_dependency_xyz")

        apploader = AppLoader(tmp_path)
        apploader.load_config()

        with pytest.raises(ModuleNotFoundError):
            apploader.import_module()

    def test_only_adds_to_sys_path_if_needed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """import_module only adds app path to sys.path if initial import fails."""
        # Create a module that's already importable (in existing sys.path)
        # We'll use tmp_path in sys.path to simulate this
        (tmp_path / "trellis.py").write_text(
            """
from trellis.app.config import Config
config = Config(name="test", module="already_there")
"""
        )
        (tmp_path / "already_there.py").write_text("VALUE = 'found'")

        # Pre-add tmp_path to sys.path
        monkeypatch.syspath_prepend(tmp_path)
        original_path_len = len(sys.path)

        apploader = AppLoader(tmp_path)
        apploader.load_config()

        module = apploader.import_module()

        # Should not have added to sys.path since module was already findable
        assert module.VALUE == "found"
        assert len(sys.path) == original_path_len


class TestAppLoaderGlobals:
    """Tests for get_apploader/set_apploader global accessors."""

    @pytest.fixture(autouse=True)
    def reset_apploader(self) -> None:
        """Reset global _apploader before each test."""
        import trellis.app.apploader as apploader_module  # noqa: PLC0415

        apploader_module._apploader = None
        yield
        apploader_module._apploader = None

    def test_round_trip_works(self, tmp_path: Path) -> None:
        """set_apploader/get_apploader round trip works correctly."""
        apploader = AppLoader(tmp_path)

        set_apploader(apploader)
        result = get_apploader()

        assert result is apploader

    def test_get_apploader_before_set_raises(self) -> None:
        """get_apploader raises RuntimeError when called before set_apploader."""
        with pytest.raises(RuntimeError) as exc_info:
            get_apploader()

        assert "AppLoader not initialized" in str(exc_info.value)
        assert "set_apploader()" in str(exc_info.value)
        assert "find_app_path()" in str(exc_info.value)

    def test_get_config_returns_config(self, tmp_path: Path) -> None:
        """get_config returns the config from the global AppLoader."""
        (tmp_path / "trellis.py").write_text(
            """
from trellis.app.config import Config
config = Config(name="test-app", module="test")
"""
        )
        apploader = AppLoader(tmp_path)
        apploader.load_config()
        set_apploader(apploader)

        config = get_config()

        assert config is not None
        assert config.name == "test-app"

    def test_get_config_returns_none_before_load(self, tmp_path: Path) -> None:
        """get_config returns None if load_config hasn't been called."""
        apploader = AppLoader(tmp_path)
        set_apploader(apploader)

        config = get_config()

        assert config is None

    def test_get_config_raises_before_set(self) -> None:
        """get_config raises RuntimeError if set_apploader hasn't been called."""
        with pytest.raises(RuntimeError, match="AppLoader not initialized"):
            get_config()

    def test_get_app_root_returns_path(self, tmp_path: Path) -> None:
        """get_app_root returns the path from the global AppLoader."""
        apploader = AppLoader(tmp_path)
        set_apploader(apploader)

        path = get_app_root()

        assert path == tmp_path

    def test_get_app_root_raises_before_set(self) -> None:
        """get_app_root raises RuntimeError if set_apploader hasn't been called."""
        with pytest.raises(RuntimeError, match="AppLoader not initialized"):
            get_app_root()


class TestAppLoaderPlatform:
    """Tests for AppLoader.platform property."""

    def test_platform_raises_without_config(self, tmp_path: Path) -> None:
        """platform property raises RuntimeError if config not loaded."""
        apploader = AppLoader(tmp_path)

        with pytest.raises(RuntimeError, match=r"load_config.*first"):
            _ = apploader.platform

    def test_platform_returns_server_platform(self, tmp_path: Path) -> None:
        """platform returns ServerPlatform when config.platform is SERVER."""
        (tmp_path / "trellis.py").write_text(
            """
from trellis.app.config import Config
from trellis.platforms.common.base import PlatformType

config = Config(name="test", module="test", platform=PlatformType.SERVER)
"""
        )
        apploader = AppLoader(tmp_path)
        apploader.load_config()

        assert isinstance(apploader.platform, ServerPlatform)

    @requires_pytauri
    def test_platform_returns_desktop_platform(self, tmp_path: Path) -> None:
        """platform returns DesktopPlatform when config.platform is DESKTOP."""
        (tmp_path / "trellis.py").write_text(
            """
from trellis.app.config import Config
from trellis.platforms.common.base import PlatformType

config = Config(name="test", module="test", platform=PlatformType.DESKTOP)
"""
        )
        apploader = AppLoader(tmp_path)
        apploader.load_config()

        # Import inside test because pytauri may not be installed
        from trellis.platforms.desktop import DesktopPlatform  # noqa: PLC0415

        assert isinstance(apploader.platform, DesktopPlatform)

    def test_platform_returns_browser_serve_platform(self, tmp_path: Path) -> None:
        """platform returns BrowserServePlatform when not in Pyodide."""
        (tmp_path / "trellis.py").write_text(
            """
from trellis.app.config import Config
from trellis.platforms.common.base import PlatformType

config = Config(name="test", module="test", platform=PlatformType.BROWSER)
"""
        )
        apploader = AppLoader(tmp_path)
        apploader.load_config()

        assert isinstance(apploader.platform, BrowserServePlatform)

    def test_platform_returns_browser_platform_in_pyodide(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """platform returns BrowserPlatform when running in Pyodide."""
        (tmp_path / "trellis.py").write_text(
            """
from trellis.app.config import Config
from trellis.platforms.common.base import PlatformType

config = Config(name="test", module="test", platform=PlatformType.BROWSER)
"""
        )
        apploader = AppLoader(tmp_path)
        apploader.load_config()

        # Mock _is_pyodide to return True
        monkeypatch.setattr("trellis.app.apploader._is_pyodide", lambda: True)

        assert isinstance(apploader.platform, BrowserPlatform)

    def test_platform_caches_instance(self, tmp_path: Path) -> None:
        """platform returns same instance on subsequent accesses."""
        (tmp_path / "trellis.py").write_text(
            """
from trellis.app.config import Config
from trellis.platforms.common.base import PlatformType

config = Config(name="test", module="test", platform=PlatformType.SERVER)
"""
        )
        apploader = AppLoader(tmp_path)
        apploader.load_config()

        first = apploader.platform
        second = apploader.platform

        assert first is second

    def test_platform_returns_cached_without_config_check(self, tmp_path: Path) -> None:
        """If _platform is already set, returns it without checking config."""
        apploader = AppLoader(tmp_path)

        # Manually set _platform (simulating pre-cached state)
        apploader._platform = ServerPlatform()

        # Should return cached platform even though config is None
        assert isinstance(apploader.platform, ServerPlatform)
