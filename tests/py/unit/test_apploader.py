"""Unit tests for AppLoader configuration system."""

from __future__ import annotations

from pathlib import Path
from types import ModuleType
from unittest.mock import patch

import pytest

from tests.conftest import WriteApp, WriteAppModule, WriteTrellisConfig
from tests.helpers import requires_pytauri
from trellis.app.app import App
from trellis.app.apploader import (
    AppLoader,
    find_app_path,
    get_app,
    get_app_root,
    get_apploader,
    get_config,
    get_dist_dir,
    get_workspace_dir,
    set_apploader,
)
from trellis.app.config import Config
from trellis.platforms.browser import BrowserPlatform
from trellis.platforms.browser.serve_platform import BrowserServePlatform
from trellis.platforms.server import ServerPlatform


class TestFindAppPath:
    """Tests for find_app_path function."""

    def test_finds_trellis_py_in_cwd(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """find_app_path finds trellis_config.py in current working directory."""
        (tmp_path / "trellis_config.py").write_text("config = None")
        monkeypatch.chdir(tmp_path)

        result = find_app_path()

        assert result == tmp_path

    def test_finds_trellis_py_in_parent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """find_app_path finds trellis_config.py in parent directory."""
        (tmp_path / "trellis_config.py").write_text("config = None")
        child = tmp_path / "subdir"
        child.mkdir()
        monkeypatch.chdir(child)

        result = find_app_path()

        assert result == tmp_path

    def test_finds_trellis_py_multiple_levels_up(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """find_app_path finds trellis_config.py multiple levels up."""
        (tmp_path / "trellis_config.py").write_text("config = None")
        deep = tmp_path / "a" / "b" / "c"
        deep.mkdir(parents=True)
        monkeypatch.chdir(deep)

        result = find_app_path()

        assert result == tmp_path

    def test_raises_when_not_found(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """find_app_path raises FileNotFoundError when trellis_config.py not found."""
        # tmp_path has no trellis_config.py
        monkeypatch.chdir(tmp_path)

        with pytest.raises(FileNotFoundError) as exc_info:
            find_app_path()

        assert "trellis_config.py not found" in str(exc_info.value)
        assert "trellis init" in str(exc_info.value)

    def test_returns_directory_not_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """find_app_path returns the directory containing trellis_config.py, not the file itself."""
        trellis_file = tmp_path / "trellis_config.py"
        trellis_file.write_text("config = None")
        monkeypatch.chdir(tmp_path)

        result = find_app_path()

        assert result.is_dir()
        assert result == tmp_path
        assert result != trellis_file

    def test_nearest_wins(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """find_app_path returns the nearest trellis_config.py when multiple exist."""
        # Create trellis_config.py in parent
        (tmp_path / "trellis_config.py").write_text("config = 'parent'")

        # Create trellis_config.py in child
        child = tmp_path / "subproject"
        child.mkdir()
        (child / "trellis_config.py").write_text("config = 'child'")

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

    def test_load_config_populates_config(self, write_trellis_config: WriteTrellisConfig) -> None:
        """load_config populates config attribute from trellis_config.py."""
        app_root = write_trellis_config(name="my-app", module="my_app.main")
        apploader = AppLoader(app_root)

        apploader.load_config()

        assert apploader.config is not None
        assert apploader.config.name == "my-app"
        assert apploader.config.module == "my_app.main"

    def test_load_config_error_file_not_found(self, tmp_path: Path) -> None:
        """load_config raises FileNotFoundError when trellis_config.py doesn't exist."""
        apploader = AppLoader(tmp_path)

        with pytest.raises(FileNotFoundError) as exc_info:
            apploader.load_config()

        assert "trellis_config.py not found at" in str(exc_info.value)
        assert str(tmp_path) in str(exc_info.value)

    def test_load_config_error_syntax_error(self, write_trellis_config: WriteTrellisConfig) -> None:
        """load_config propagates SyntaxError from trellis_config.py."""
        app_root = write_trellis_config(content="def broken(")
        apploader = AppLoader(app_root)

        with pytest.raises(SyntaxError):
            apploader.load_config()

    def test_load_config_error_import_error(self, write_trellis_config: WriteTrellisConfig) -> None:
        """load_config propagates ImportError from trellis_config.py."""
        app_root = write_trellis_config(content="import nonexistent_module_xyz")
        apploader = AppLoader(app_root)

        with pytest.raises(ModuleNotFoundError):
            apploader.load_config()

    def test_load_config_error_no_config_variable(
        self, write_trellis_config: WriteTrellisConfig
    ) -> None:
        """load_config raises ValueError when config variable not defined."""
        app_root = write_trellis_config(content="x = 1")
        apploader = AppLoader(app_root)

        with pytest.raises(ValueError, match="'config' variable not defined"):
            apploader.load_config()

    def test_load_config_error_wrong_type(self, write_trellis_config: WriteTrellisConfig) -> None:
        """load_config raises TypeError when config is not a Config instance."""
        app_root = write_trellis_config(content="config = {'name': 'test'}")
        apploader = AppLoader(app_root)

        with pytest.raises(TypeError) as exc_info:
            apploader.load_config()

        assert "'config' must be a Config instance" in str(exc_info.value)
        assert "got dict" in str(exc_info.value)
        assert "config = Config(name=..., module=...)" in str(exc_info.value)


class TestAppLoaderImportModule:
    """Tests for AppLoader.import_module method."""

    def test_imports_simple_module(
        self,
        write_trellis_config: WriteTrellisConfig,
        write_app_module: WriteAppModule,
    ) -> None:
        """import_module imports a module in the app directory."""
        app_root = write_trellis_config(name="test", module="myapp")
        write_app_module(module_name="myapp", content="VALUE = 42")

        apploader = AppLoader(app_root)
        apploader.load_config()

        module = apploader.import_module()

        assert module.VALUE == 42

    def test_imports_subpackage_module(
        self, tmp_path: Path, write_trellis_config: WriteTrellisConfig
    ) -> None:
        """import_module imports a module from a subpackage."""
        app_root = write_trellis_config(name="test", module="mypkg.main")
        pkg_dir = tmp_path / "mypkg"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "main.py").write_text("VALUE = 'nested'")

        apploader = AppLoader(app_root)
        apploader.load_config()

        module = apploader.import_module()

        assert module.VALUE == "nested"

    def test_returns_module_object(
        self,
        write_trellis_config: WriteTrellisConfig,
        write_app_module: WriteAppModule,
    ) -> None:
        """import_module returns a ModuleType."""
        app_root = write_trellis_config(name="test", module="myapp")
        write_app_module(module_name="myapp", content="")

        apploader = AppLoader(app_root)
        apploader.load_config()

        module = apploader.import_module()

        assert isinstance(module, ModuleType)

    def test_error_module_not_found(self, write_trellis_config: WriteTrellisConfig) -> None:
        """import_module raises ModuleNotFoundError with context when module doesn't exist."""
        app_root = write_trellis_config(name="test", module="nonexistent")

        apploader = AppLoader(app_root)
        apploader.load_config()

        with pytest.raises(ModuleNotFoundError) as exc_info:
            apploader.import_module()

        assert "nonexistent" in str(exc_info.value)

    def test_error_config_not_loaded(self, tmp_path: Path) -> None:
        """import_module raises RuntimeError if config not loaded first."""
        apploader = AppLoader(tmp_path)

        with pytest.raises(RuntimeError, match=r"load_config.*first"):
            apploader.import_module()

    def test_propagates_syntax_error(
        self,
        write_trellis_config: WriteTrellisConfig,
        write_app_module: WriteAppModule,
    ) -> None:
        """import_module propagates SyntaxError from the module."""
        app_root = write_trellis_config(name="test", module="broken")
        write_app_module(module_name="broken", content="def oops(")

        apploader = AppLoader(app_root)
        apploader.load_config()

        with pytest.raises(SyntaxError):
            apploader.import_module()

    def test_propagates_import_error(
        self,
        write_trellis_config: WriteTrellisConfig,
        write_app_module: WriteAppModule,
    ) -> None:
        """import_module propagates ImportError from module dependencies."""
        app_root = write_trellis_config(name="test", module="has_bad_import")
        write_app_module(module_name="has_bad_import", content="import nonexistent_dependency_xyz")

        apploader = AppLoader(app_root)
        apploader.load_config()

        with pytest.raises(ModuleNotFoundError):
            apploader.import_module()

    def test_import_with_src_subdirectory(
        self, tmp_path: Path, write_trellis_config: WriteTrellisConfig
    ) -> None:
        """python_path=["src"] allows importing from src/ subdirectory."""
        app_root = write_trellis_config(
            content=(
                "from pathlib import Path\n"
                "from trellis.app.config import Config\n"
                'config = Config(name="test", module="myapp_src_subdir",'
                ' python_path=[Path("src")])\n'
            )
        )
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "myapp_src_subdir.py").write_text("VALUE = 'from_src'")

        apploader = AppLoader(app_root)
        apploader.load_config()
        module = apploader.import_module()

        assert module.VALUE == "from_src"

    def test_import_with_multiple_python_paths(
        self, tmp_path: Path, write_trellis_config: WriteTrellisConfig
    ) -> None:
        """python_path with multiple entries adds all to sys.path."""
        app_root = write_trellis_config(
            content=(
                "from pathlib import Path\n"
                "from trellis.app.config import Config\n"
                'config = Config(name="test", module="myapp_multi_path",'
                ' python_path=[Path("src"), Path("lib")])\n'
            )
        )
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "myapp_multi_path.py").write_text("from helper_multi import VALUE")

        lib_dir = tmp_path / "lib"
        lib_dir.mkdir()
        (lib_dir / "helper_multi.py").write_text("VALUE = 'from_lib'")

        apploader = AppLoader(app_root)
        apploader.load_config()
        module = apploader.import_module()

        assert module.VALUE == "from_lib"

    def test_import_default_python_path_includes_app_root(
        self,
        write_trellis_config: WriteTrellisConfig,
        write_app_module: WriteAppModule,
    ) -> None:
        """Default python_path=[Path(".")] allows importing from app root."""
        app_root = write_trellis_config(name="test", module="myapp_default_path")
        write_app_module(module_name="myapp_default_path", content="VALUE = 'from_root'")

        apploader = AppLoader(app_root)
        apploader.load_config()
        module = apploader.import_module()

        assert module.VALUE == "from_root"


class TestAppLoaderLoadApp:
    """Tests for AppLoader.load_app method."""

    def test_load_app_requires_config_loaded(self, tmp_path: Path) -> None:
        """load_app raises RuntimeError if load_config not called first."""
        apploader = AppLoader(tmp_path)

        with pytest.raises(RuntimeError, match=r"load_config.*first"):
            apploader.load_app()

    def test_load_app_discovers_app_from_module(self, write_app: WriteApp) -> None:
        """load_app successfully loads App instance from module."""
        app_root = write_app(module="app_discover_test", component_name="MyComponent")

        apploader = AppLoader(app_root)
        apploader.load_config()
        apploader.load_app()

        assert apploader.app is not None
        assert isinstance(apploader.app, App)

    def test_load_app_missing_app_variable(
        self,
        write_trellis_config: WriteTrellisConfig,
        write_app_module: WriteAppModule,
    ) -> None:
        """load_app raises ValueError with helpful message if no 'app' in module."""
        app_root = write_trellis_config(name="test", module="app_missing_test")
        write_app_module(module_name="app_missing_test", content="VALUE = 42")

        apploader = AppLoader(app_root)
        apploader.load_config()

        with pytest.raises(ValueError, match="'app' variable not defined"):
            apploader.load_app()

    def test_load_app_wrong_type(
        self,
        write_trellis_config: WriteTrellisConfig,
        write_app_module: WriteAppModule,
    ) -> None:
        """load_app raises TypeError if 'app' is not an App instance."""
        app_root = write_trellis_config(name="test", module="app_wrongtype_test")
        write_app_module(module_name="app_wrongtype_test", content="app = {'not': 'an App'}")

        apploader = AppLoader(app_root)
        apploader.load_config()

        with pytest.raises(TypeError, match="'app' must be an App instance"):
            apploader.load_app()

    def test_load_app_sets_app_attribute(self, write_app: WriteApp) -> None:
        """After load_app, apploader.app is the App instance from the module."""
        app_root = write_app(module="app_sets_attr_test")

        apploader = AppLoader(app_root)
        apploader.load_config()

        assert apploader.app is None
        apploader.load_app()
        assert apploader.app is not None

    def test_app_is_none_before_load(self, tmp_path: Path) -> None:
        """AppLoader.app is None before load_app is called."""
        apploader = AppLoader(tmp_path)

        assert apploader.app is None


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

    def test_get_config_returns_config(self, write_trellis_config: WriteTrellisConfig) -> None:
        """get_config returns the config from the global AppLoader."""
        app_root = write_trellis_config(name="test-app", module="test")
        apploader = AppLoader(app_root)
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

    def test_get_app_returns_none_before_load(self, tmp_path: Path) -> None:
        """get_app returns None when app not loaded."""
        apploader = AppLoader(tmp_path)
        set_apploader(apploader)

        app = get_app()

        assert app is None

    def test_get_app_returns_app_after_load(self, write_app: WriteApp) -> None:
        """get_app returns App instance after load_app()."""
        app_root = write_app(module="get_app_test")
        apploader = AppLoader(app_root)
        apploader.load_config()
        apploader.load_app()
        set_apploader(apploader)

        app = get_app()

        assert app is not None
        assert isinstance(app, App)

    def test_get_app_raises_without_apploader(self) -> None:
        """get_app raises RuntimeError if set_apploader not called."""
        with pytest.raises(RuntimeError, match="AppLoader not initialized"):
            get_app()


class TestAppLoaderPlatform:
    """Tests for AppLoader.platform property."""

    def test_platform_raises_without_config(self, tmp_path: Path) -> None:
        """platform property raises RuntimeError if config not loaded."""
        apploader = AppLoader(tmp_path)

        with pytest.raises(RuntimeError, match=r"load_config.*first"):
            _ = apploader.platform

    def test_platform_returns_server_platform(
        self, write_trellis_config: WriteTrellisConfig
    ) -> None:
        """platform returns ServerPlatform when config.platform is SERVER."""
        app_root = write_trellis_config(module="test", platform="SERVER")
        apploader = AppLoader(app_root)
        apploader.load_config()

        assert isinstance(apploader.platform, ServerPlatform)

    @requires_pytauri
    def test_platform_returns_desktop_platform(
        self, write_trellis_config: WriteTrellisConfig
    ) -> None:
        """platform returns DesktopPlatform when config.platform is DESKTOP."""
        app_root = write_trellis_config(module="test", platform="DESKTOP")
        apploader = AppLoader(app_root)
        apploader.load_config()

        # Import inside test because pytauri may not be installed
        from trellis.platforms.desktop import DesktopPlatform  # noqa: PLC0415

        assert isinstance(apploader.platform, DesktopPlatform)

    def test_platform_returns_browser_serve_platform(
        self, write_trellis_config: WriteTrellisConfig
    ) -> None:
        """platform returns BrowserServePlatform when not in Pyodide."""
        app_root = write_trellis_config(module="test", platform="BROWSER")
        apploader = AppLoader(app_root)
        apploader.load_config()

        assert isinstance(apploader.platform, BrowserServePlatform)

    def test_platform_returns_browser_platform_in_pyodide(
        self,
        write_trellis_config: WriteTrellisConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """platform returns BrowserPlatform when running in Pyodide."""
        app_root = write_trellis_config(module="test", platform="BROWSER")
        apploader = AppLoader(app_root)
        apploader.load_config()

        monkeypatch.setattr("trellis.app.apploader._is_pyodide", lambda: True)

        assert isinstance(apploader.platform, BrowserPlatform)

    def test_platform_caches_instance(self, write_trellis_config: WriteTrellisConfig) -> None:
        """platform returns same instance on subsequent accesses."""
        app_root = write_trellis_config(module="test", platform="SERVER")
        apploader = AppLoader(app_root)
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


class TestGetWorkspaceDir:
    """Tests for get_workspace_dir function."""

    def test_returns_workspace_path(self, tmp_path: Path, reset_apploader: None) -> None:
        """get_workspace_dir returns {app_root}/.workspace"""
        apploader = AppLoader(tmp_path)
        set_apploader(apploader)

        result = get_workspace_dir()

        assert result == tmp_path / ".workspace"

    def test_raises_without_apploader(self, reset_apploader: None) -> None:
        """get_workspace_dir raises RuntimeError if apploader not set."""
        with pytest.raises(RuntimeError, match="AppLoader not initialized"):
            get_workspace_dir()


class TestGetDistDir:
    """Tests for get_dist_dir function."""

    def test_returns_dist_path(self, tmp_path: Path, reset_apploader: None) -> None:
        """get_dist_dir returns {app_root}/.dist"""
        apploader = AppLoader(tmp_path)
        set_apploader(apploader)

        result = get_dist_dir()

        assert result == tmp_path / ".dist"

    def test_raises_without_apploader(self, reset_apploader: None) -> None:
        """get_dist_dir raises RuntimeError if apploader not set."""
        with pytest.raises(RuntimeError, match="AppLoader not initialized"):
            get_dist_dir()


class TestAppLoaderBundle:
    """Tests for AppLoader.bundle() method."""

    @pytest.fixture(autouse=True)
    def _setup(self, reset_apploader: None) -> None:
        """Reset apploader for each test."""

    def test_calls_build_with_server_config(
        self,
        write_trellis_config: WriteTrellisConfig,
    ) -> None:
        """bundle() calls build() with entry_point and steps from get_build_config()."""
        app_root = write_trellis_config(name="myapp", module="main")
        apploader = AppLoader(app_root)
        apploader.load_config()
        set_apploader(apploader)

        with patch("trellis.app.apploader.build") as mock_build:
            apploader.bundle()

        mock_build.assert_called_once()
        kwargs = mock_build.call_args.kwargs
        assert "server" in str(kwargs["entry_point"])
        assert kwargs["output_dir"] == app_root / ".dist"
        assert kwargs["force"] is False

    def test_passes_dest_to_build(
        self,
        tmp_path: Path,
        write_trellis_config: WriteTrellisConfig,
    ) -> None:
        """Custom dest overrides get_dist_dir()."""
        app_root = write_trellis_config(name="myapp", module="main")
        apploader = AppLoader(app_root)
        apploader.load_config()
        set_apploader(apploader)

        custom_dest = tmp_path / "custom_output"
        with patch("trellis.app.apploader.build") as mock_build:
            apploader.bundle(dest=custom_dest)

        assert mock_build.call_args.kwargs["output_dir"] == custom_dest

    def test_uses_force_build_from_config(
        self,
        write_trellis_config: WriteTrellisConfig,
    ) -> None:
        """bundle() passes config.force_build to build()."""
        app_root = write_trellis_config(
            content=(
                "from trellis.app.config import Config\n"
                "config = Config(name='myapp', module='main', force_build=True)\n"
            )
        )
        apploader = AppLoader(app_root)
        apploader.load_config()
        set_apploader(apploader)

        with patch("trellis.app.apploader.build") as mock_build:
            apploader.bundle()

        assert mock_build.call_args.kwargs["force"] is True

    def test_raises_without_config(self, tmp_path: Path) -> None:
        """bundle() raises RuntimeError if config not loaded."""
        apploader = AppLoader(tmp_path)

        with pytest.raises(RuntimeError, match="Config not loaded"):
            apploader.bundle()

    def test_returns_workspace_path(
        self,
        write_trellis_config: WriteTrellisConfig,
    ) -> None:
        """bundle() returns the workspace directory."""
        app_root = write_trellis_config(name="myapp", module="main")
        apploader = AppLoader(app_root)
        apploader.load_config()
        set_apploader(apploader)

        with patch("trellis.app.apploader.build"):
            result = apploader.bundle()

        assert result == app_root / ".workspace"


class TestAppLoaderFromConfig:
    """Tests for AppLoader.from_config classmethod."""

    def test_from_config_sets_config(self) -> None:
        """from_config sets config directly and path to None."""
        config = Config(name="myapp", module="myapp.main")

        apploader = AppLoader.from_config(config)

        assert apploader.config is config
        assert apploader.path is None

    def test_from_config_clears_python_path(self) -> None:
        """from_config clears python_path even if input config had entries."""
        config = Config(name="myapp", module="myapp.main", python_path=[Path("src")])

        apploader = AppLoader.from_config(config)

        assert apploader.config is not None
        assert apploader.config.python_path == []

    def test_from_config_load_app(
        self,
        write_app_module: WriteAppModule,
        tmp_path: Path,
    ) -> None:
        """from_config → load_app() round-trip loads the app."""
        write_app_module(module_name="from_config_test")
        import sys  # noqa: PLC0415

        sys.path.insert(0, str(tmp_path))
        try:
            config = Config(name="test", module="from_config_test")
            apploader = AppLoader.from_config(config)
            apploader.load_app()

            assert apploader.app is not None
            assert isinstance(apploader.app, App)
        finally:
            sys.path.remove(str(tmp_path))

    def test_get_app_root_raises_without_path(self, reset_apploader: None) -> None:
        """get_app_root raises RuntimeError when apploader has no path."""
        config = Config(name="myapp", module="myapp.main")
        apploader = AppLoader.from_config(config)
        set_apploader(apploader)

        with pytest.raises(RuntimeError, match="no app root directory"):
            get_app_root()
