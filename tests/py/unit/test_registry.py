"""Unit tests for trellis.bundler.registry module."""

from __future__ import annotations

from pathlib import Path

import pytest


class TestExportKind:
    """Tests for ExportKind enum."""

    def test_component_value(self) -> None:
        """ExportKind.component exists."""
        from trellis.bundler.registry import ExportKind

        assert ExportKind.component is not None

    def test_function_value(self) -> None:
        """ExportKind.function exists."""
        from trellis.bundler.registry import ExportKind

        assert ExportKind.function is not None

    def test_initializer_value(self) -> None:
        """ExportKind.initializer exists."""
        from trellis.bundler.registry import ExportKind

        assert ExportKind.initializer is not None


class TestModuleExport:
    """Tests for ModuleExport dataclass."""

    def test_creation(self) -> None:
        """ModuleExport can be created with required fields."""
        from trellis.bundler.registry import ExportKind, ModuleExport

        export = ModuleExport(
            name="Button",
            kind=ExportKind.component,
            source="widgets/Button.tsx",
        )
        assert export.name == "Button"
        assert export.kind == ExportKind.component
        assert export.source == "widgets/Button.tsx"


class TestModule:
    """Tests for Module dataclass."""

    def test_creation_with_required_fields(self) -> None:
        """Module can be created with just name."""
        from trellis.bundler.registry import Module

        module = Module(name="my-module")
        assert module.name == "my-module"

    def test_packages_defaults_to_empty(self) -> None:
        """packages defaults to empty dict."""
        from trellis.bundler.registry import Module

        module = Module(name="my-module")
        assert module.packages == {}

    def test_files_defaults_to_empty(self) -> None:
        """files defaults to empty list."""
        from trellis.bundler.registry import Module

        module = Module(name="my-module")
        assert module.files == []

    def test_snippets_defaults_to_empty(self) -> None:
        """snippets defaults to empty dict."""
        from trellis.bundler.registry import Module

        module = Module(name="my-module")
        assert module.snippets == {}

    def test_static_files_defaults_to_empty(self) -> None:
        """static_files defaults to empty dict."""
        from trellis.bundler.registry import Module

        module = Module(name="my-module")
        assert module.static_files == {}

    def test_exports_defaults_to_empty(self) -> None:
        """exports defaults to empty list."""
        from trellis.bundler.registry import Module

        module = Module(name="my-module")
        assert module.exports == []

    def test_worker_entries_defaults_to_empty(self) -> None:
        """worker_entries defaults to empty dict."""
        from trellis.bundler.registry import Module

        module = Module(name="my-module")
        assert module.worker_entries == {}

    def test_base_path_defaults_to_none(self) -> None:
        """_base_path defaults to None."""
        from trellis.bundler.registry import Module

        module = Module(name="my-module")
        assert module._base_path is None

    def test_creation_with_all_fields(self) -> None:
        """Module can be created with all fields populated."""
        from trellis.bundler.registry import ExportKind, Module, ModuleExport

        module = Module(
            name="my-module",
            packages={"react": "18.2.0"},
            files=["Widget.tsx"],
            snippets={"Helper.tsx": "export const Helper = () => null;"},
            static_files={"icon.png": Path("/path/to/icon.png")},
            exports=[ModuleExport("Widget", ExportKind.component, "Widget.tsx")],
            worker_entries={"service": "service-worker.ts"},
            _base_path=Path("/some/path"),
        )
        assert module.name == "my-module"
        assert module.packages == {"react": "18.2.0"}
        assert module.files == ["Widget.tsx"]
        assert module.snippets == {"Helper.tsx": "export const Helper = () => null;"}
        assert module.static_files == {"icon.png": Path("/path/to/icon.png")}
        assert len(module.exports) == 1
        assert module.exports[0].name == "Widget"
        assert module.worker_entries == {"service": "service-worker.ts"}
        assert module._base_path == Path("/some/path")


class TestModuleRegistry:
    """Tests for ModuleRegistry class."""

    def test_register_stores_module(self) -> None:
        """register() stores module in registry."""
        from trellis.bundler.registry import ModuleRegistry

        registry = ModuleRegistry()
        registry.register("my-module", packages={"react": "18.2.0"})

        collected = registry.collect()
        assert len(collected.modules) == 1
        assert collected.modules[0].name == "my-module"
        assert collected.modules[0].packages == {"react": "18.2.0"}

    def test_register_resolves_paths_relative_to_caller(self, tmp_path: Path) -> None:
        """register() resolves file paths relative to calling file."""
        from trellis.bundler.registry import ModuleRegistry

        registry = ModuleRegistry()

        # Create a temporary module that registers itself
        module_file = tmp_path / "my_package" / "register.py"
        module_file.parent.mkdir(parents=True)

        # Write a registration script that we'll execute
        module_file.write_text(
            """\
from trellis.bundler.registry import ModuleRegistry

def register_module(registry):
    registry.register("test-module", files=["Widget.tsx"])
"""
        )

        # Create the Widget.tsx file
        widget_file = tmp_path / "my_package" / "Widget.tsx"
        widget_file.write_text("export const Widget = () => null;")

        # Execute the registration from that module's context
        import importlib.util

        spec = importlib.util.spec_from_file_location("register", module_file)
        assert spec is not None
        assert spec.loader is not None
        register_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(register_mod)
        register_mod.register_module(registry)

        collected = registry.collect()
        assert len(collected.modules) == 1
        # The base path should be resolved to the directory containing register.py
        assert collected.modules[0]._base_path == module_file.parent

    def test_register_errors_on_duplicate_name(self) -> None:
        """register() raises error if module name already registered."""
        from trellis.bundler.registry import ModuleRegistry

        registry = ModuleRegistry()
        registry.register("my-module")

        with pytest.raises(ValueError, match="already registered"):
            registry.register("my-module")

    def test_collect_returns_all_modules(self) -> None:
        """collect() returns all registered modules."""
        from trellis.bundler.registry import ModuleRegistry

        registry = ModuleRegistry()
        registry.register("module-a")
        registry.register("module-b")
        registry.register("module-c")

        collected = registry.collect()
        names = [m.name for m in collected.modules]
        assert names == ["module-a", "module-b", "module-c"]

    def test_collect_merges_packages(self) -> None:
        """collect() merges packages from all modules."""
        from trellis.bundler.registry import ModuleRegistry

        registry = ModuleRegistry()
        registry.register("module-a", packages={"react": "18.2.0"})
        registry.register("module-b", packages={"lodash": "4.17.21"})
        registry.register("module-c", packages={"react-dom": "18.2.0"})

        collected = registry.collect()
        assert collected.packages == {
            "react": "18.2.0",
            "lodash": "4.17.21",
            "react-dom": "18.2.0",
        }

    def test_collect_allows_same_package_same_version(self) -> None:
        """collect() allows same package with same version across modules."""
        from trellis.bundler.registry import ModuleRegistry

        registry = ModuleRegistry()
        registry.register("module-a", packages={"react": "18.2.0"})
        registry.register("module-b", packages={"react": "18.2.0"})

        collected = registry.collect()
        assert collected.packages == {"react": "18.2.0"}

    def test_collect_errors_on_package_version_conflict(self) -> None:
        """collect() raises error if same package has different versions."""
        from trellis.bundler.registry import ModuleRegistry

        registry = ModuleRegistry()
        registry.register("module-a", packages={"react": "18.2.0"})
        registry.register("module-b", packages={"react": "17.0.0"})

        with pytest.raises(ValueError, match="version conflict"):
            registry.collect()

    def test_clear_removes_all_modules(self) -> None:
        """clear() removes all registered modules."""
        from trellis.bundler.registry import ModuleRegistry

        registry = ModuleRegistry()
        registry.register("module-a")
        registry.register("module-b")

        registry.clear()
        collected = registry.collect()
        assert len(collected.modules) == 0


class TestCollectedModules:
    """Tests for CollectedModules dataclass."""

    def test_creation(self) -> None:
        """CollectedModules can be created with modules and packages."""
        from trellis.bundler.registry import CollectedModules, Module

        modules = [Module(name="mod-a"), Module(name="mod-b")]
        packages = {"react": "18.2.0"}

        collected = CollectedModules(modules=modules, packages=packages)
        assert len(collected.modules) == 2
        assert collected.packages == {"react": "18.2.0"}


class TestGlobalRegistry:
    """Tests for the global registry singleton."""

    def test_global_registry_exists(self) -> None:
        """Module exposes a global registry singleton."""
        # Should be a ModuleRegistry instance
        from trellis.bundler.registry import ModuleRegistry, registry

        assert isinstance(registry, ModuleRegistry)

    def test_global_registry_is_singleton(self) -> None:
        """Multiple imports return same registry instance."""
        from trellis.bundler.registry import registry as reg1
        from trellis.bundler.registry import registry as reg2

        assert reg1 is reg2


class TestGlobPatterns:
    """Tests for glob pattern expansion in files."""

    def test_glob_pattern_expands_to_matching_files(self, tmp_path: Path) -> None:
        """Glob patterns in files are expanded to matching files."""
        from trellis.bundler.registry import ModuleRegistry

        # Create test files
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "Widget.tsx").write_text("export const Widget = () => null;")
        (src_dir / "Button.tsx").write_text("export const Button = () => null;")
        (src_dir / "utils.ts").write_text("export const util = 1;")

        # Create a module that uses a glob pattern
        module_file = tmp_path / "register.py"
        module_file.write_text(
            """\
from trellis.bundler.registry import ModuleRegistry

def register_module(registry):
    registry.register("test-module", files=["src/**/*.tsx"])
"""
        )

        registry = ModuleRegistry()
        import importlib.util

        spec = importlib.util.spec_from_file_location("register", module_file)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.register_module(registry)

        collected = registry.collect()
        files = sorted(collected.modules[0].files)
        assert files == ["src/Button.tsx", "src/Widget.tsx"]

    def test_literal_path_still_works(self, tmp_path: Path) -> None:
        """Literal file paths (non-glob) still work."""
        from trellis.bundler.registry import ModuleRegistry

        # Create test file
        (tmp_path / "Widget.tsx").write_text("export const Widget = () => null;")

        module_file = tmp_path / "register.py"
        module_file.write_text(
            """\
from trellis.bundler.registry import ModuleRegistry

def register_module(registry):
    registry.register("test-module", files=["Widget.tsx"])
"""
        )

        registry = ModuleRegistry()
        import importlib.util

        spec = importlib.util.spec_from_file_location("register", module_file)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.register_module(registry)

        collected = registry.collect()
        assert collected.modules[0].files == ["Widget.tsx"]

    def test_mixed_globs_and_literals(self, tmp_path: Path) -> None:
        """Can mix glob patterns and literal paths."""
        from trellis.bundler.registry import ModuleRegistry

        # Create test files
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "A.tsx").write_text("export const A = () => null;")
        (src_dir / "B.tsx").write_text("export const B = () => null;")
        (tmp_path / "index.ts").write_text("export * from './src';")

        module_file = tmp_path / "register.py"
        module_file.write_text(
            """\
from trellis.bundler.registry import ModuleRegistry

def register_module(registry):
    registry.register("test-module", files=["index.ts", "src/**/*.tsx"])
"""
        )

        registry = ModuleRegistry()
        import importlib.util

        spec = importlib.util.spec_from_file_location("register", module_file)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.register_module(registry)

        collected = registry.collect()
        files = sorted(collected.modules[0].files)
        assert files == ["index.ts", "src/A.tsx", "src/B.tsx"]

    def test_glob_no_matches_returns_empty(self, tmp_path: Path) -> None:
        """Glob pattern with no matches returns empty list (no error)."""
        from trellis.bundler.registry import ModuleRegistry

        module_file = tmp_path / "register.py"
        module_file.write_text(
            """\
from trellis.bundler.registry import ModuleRegistry

def register_module(registry):
    registry.register("test-module", files=["src/**/*.tsx"])
"""
        )

        registry = ModuleRegistry()
        import importlib.util

        spec = importlib.util.spec_from_file_location("register", module_file)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.register_module(registry)

        collected = registry.collect()
        assert collected.modules[0].files == []

    def test_glob_nested_directories(self, tmp_path: Path) -> None:
        """Glob patterns work with nested directories."""
        from trellis.bundler.registry import ModuleRegistry

        # Create nested structure
        deep = tmp_path / "a" / "b" / "c"
        deep.mkdir(parents=True)
        (deep / "Widget.tsx").write_text("export const Widget = () => null;")
        (tmp_path / "a" / "Top.tsx").write_text("export const Top = () => null;")

        module_file = tmp_path / "register.py"
        module_file.write_text(
            """\
from trellis.bundler.registry import ModuleRegistry

def register_module(registry):
    registry.register("test-module", files=["a/**/*.tsx"])
"""
        )

        registry = ModuleRegistry()
        import importlib.util

        spec = importlib.util.spec_from_file_location("register", module_file)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.register_module(registry)

        collected = registry.collect()
        files = sorted(collected.modules[0].files)
        assert files == ["a/Top.tsx", "a/b/c/Widget.tsx"]

    def test_multiple_glob_patterns(self, tmp_path: Path) -> None:
        """Multiple different glob patterns work together."""
        from trellis.bundler.registry import ModuleRegistry

        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "App.tsx").write_text("export const App = () => null;")
        (src_dir / "utils.ts").write_text("export const util = 1;")
        (src_dir / "theme.css").write_text("body { margin: 0; }")

        module_file = tmp_path / "register.py"
        module_file.write_text(
            """\
from trellis.bundler.registry import ModuleRegistry

def register_module(registry):
    registry.register("test-module", files=["src/**/*.tsx", "src/**/*.ts", "src/**/*.css"])
"""
        )

        registry = ModuleRegistry()
        import importlib.util

        spec = importlib.util.spec_from_file_location("register", module_file)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.register_module(registry)

        collected = registry.collect()
        files = sorted(collected.modules[0].files)
        assert files == ["src/App.tsx", "src/theme.css", "src/utils.ts"]

    def test_brace_expansion_pattern(self, tmp_path: Path) -> None:
        """Brace expansion patterns like {ts,tsx,css} work."""
        from trellis.bundler.registry import ModuleRegistry

        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "App.tsx").write_text("export const App = () => null;")
        (src_dir / "utils.ts").write_text("export const util = 1;")
        (src_dir / "theme.css").write_text("body { margin: 0; }")
        (src_dir / "readme.md").write_text("# README")  # Should not match

        module_file = tmp_path / "register.py"
        module_file.write_text(
            """\
from trellis.bundler.registry import ModuleRegistry

def register_module(registry):
    registry.register("test-module", files=["src/**/*.{ts,tsx,css}"])
"""
        )

        registry = ModuleRegistry()
        import importlib.util

        spec = importlib.util.spec_from_file_location("register", module_file)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.register_module(registry)

        collected = registry.collect()
        files = sorted(collected.modules[0].files)
        assert files == ["src/App.tsx", "src/theme.css", "src/utils.ts"]
        assert "src/readme.md" not in files


class TestSourceFileTypes:
    """Tests for source file type validation and directory expansion."""

    def test_supported_source_types_constant_exists(self) -> None:
        """SUPPORTED_SOURCE_TYPES constant is exported."""
        from trellis.bundler.registry import SUPPORTED_SOURCE_TYPES

        assert isinstance(SUPPORTED_SOURCE_TYPES, frozenset)
        assert ".ts" in SUPPORTED_SOURCE_TYPES
        assert ".tsx" in SUPPORTED_SOURCE_TYPES
        assert ".css" in SUPPORTED_SOURCE_TYPES

    def test_unsupported_file_type_raises_error(self, tmp_path: Path) -> None:
        """Registering files with unsupported types raises ValueError."""
        from trellis.bundler.registry import ModuleRegistry

        # Create an unsupported file
        (tmp_path / "readme.md").write_text("# README")

        module_file = tmp_path / "register.py"
        module_file.write_text(
            """\
from trellis.bundler.registry import ModuleRegistry

def register_module(registry):
    registry.register("test-module", files=["readme.md"])
"""
        )

        registry = ModuleRegistry()
        import importlib.util

        spec = importlib.util.spec_from_file_location("register", module_file)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        with pytest.raises(ValueError, match="Unsupported source file type"):
            mod.register_module(registry)

    def test_glob_result_with_unsupported_type_raises_error(self, tmp_path: Path) -> None:
        """Glob patterns that match unsupported files raise ValueError."""
        from trellis.bundler.registry import ModuleRegistry

        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "App.tsx").write_text("export const App = () => null;")
        (src_dir / "readme.md").write_text("# README")

        module_file = tmp_path / "register.py"
        module_file.write_text(
            """\
from trellis.bundler.registry import ModuleRegistry

def register_module(registry):
    # Glob matches .md file which is not a supported source type
    registry.register("test-module", files=["src/**/*"])
"""
        )

        registry = ModuleRegistry()
        import importlib.util

        spec = importlib.util.spec_from_file_location("register", module_file)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        with pytest.raises(ValueError, match="Unsupported source file type"):
            mod.register_module(registry)

    def test_directory_expands_to_supported_source_types(self, tmp_path: Path) -> None:
        """Directory path expands to **/*.{supported types}."""
        from trellis.bundler.registry import ModuleRegistry

        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "App.tsx").write_text("export const App = () => null;")
        (src_dir / "utils.ts").write_text("export const util = 1;")
        (src_dir / "theme.css").write_text("body { margin: 0; }")
        (src_dir / "readme.md").write_text("# README")  # Should NOT be included

        module_file = tmp_path / "register.py"
        module_file.write_text(
            """\
from trellis.bundler.registry import ModuleRegistry

def register_module(registry):
    registry.register("test-module", files=["src"])
"""
        )

        registry = ModuleRegistry()
        import importlib.util

        spec = importlib.util.spec_from_file_location("register", module_file)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.register_module(registry)

        collected = registry.collect()
        files = sorted(collected.modules[0].files)
        assert files == ["src/App.tsx", "src/theme.css", "src/utils.ts"]
        assert "src/readme.md" not in files

    def test_directory_with_nested_files(self, tmp_path: Path) -> None:
        """Directory expansion includes nested files."""
        from trellis.bundler.registry import ModuleRegistry

        src_dir = tmp_path / "client" / "src"
        src_dir.mkdir(parents=True)
        (src_dir / "App.tsx").write_text("export const App = () => null;")
        widgets_dir = src_dir / "widgets"
        widgets_dir.mkdir()
        (widgets_dir / "Button.tsx").write_text("export const Button = () => null;")

        module_file = tmp_path / "register.py"
        module_file.write_text(
            """\
from trellis.bundler.registry import ModuleRegistry

def register_module(registry):
    registry.register("test-module", files=["client/src"])
"""
        )

        registry = ModuleRegistry()
        import importlib.util

        spec = importlib.util.spec_from_file_location("register", module_file)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.register_module(registry)

        collected = registry.collect()
        files = sorted(collected.modules[0].files)
        assert files == ["client/src/App.tsx", "client/src/widgets/Button.tsx"]


class TestStaticFilesDirectory:
    """Tests for static_files directory expansion."""

    def test_static_files_directory_expands_excluding_source_types(self, tmp_path: Path) -> None:
        """Directory in static_files includes all files EXCEPT source types."""

        from trellis.bundler.registry import ModuleRegistry

        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        (assets_dir / "icon.png").write_text("PNG DATA")
        (assets_dir / "logo.svg").write_text("<svg/>")
        (assets_dir / "data.json").write_text("{}")
        (assets_dir / "utils.ts").write_text("export const x = 1;")  # Excluded

        module_file = tmp_path / "register.py"
        module_file.write_text(
            """\
from pathlib import Path
from trellis.bundler.registry import ModuleRegistry

def register_module(registry):
    registry.register("test-module", static_files={"assets": Path(__file__).parent / "assets"})
"""
        )

        registry = ModuleRegistry()
        import importlib.util

        spec = importlib.util.spec_from_file_location("register", module_file)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.register_module(registry)

        collected = registry.collect()
        static = collected.modules[0].static_files
        # Directory was expanded to individual files
        assert "assets/icon.png" in static
        assert "assets/logo.svg" in static
        assert "assets/data.json" in static
        assert "assets/utils.ts" not in static

    def test_static_files_single_file_still_works(self, tmp_path: Path) -> None:
        """Single file path in static_files still works as before."""

        from trellis.bundler.registry import ModuleRegistry

        (tmp_path / "index.html").write_text("<html/>")

        module_file = tmp_path / "register.py"
        module_file.write_text(
            """\
from pathlib import Path
from trellis.bundler.registry import ModuleRegistry

def register_module(registry):
    registry.register("test-module", static_files={"index.html": Path(__file__).parent / "index.html"})
"""
        )

        registry = ModuleRegistry()
        import importlib.util

        spec = importlib.util.spec_from_file_location("register", module_file)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.register_module(registry)

        collected = registry.collect()
        static = collected.modules[0].static_files
        assert "index.html" in static
        assert static["index.html"] == tmp_path / "index.html"

    def test_static_files_nested_directory(self, tmp_path: Path) -> None:
        """Nested directory in static_files expands correctly."""

        from trellis.bundler.registry import ModuleRegistry

        public_dir = tmp_path / "public"
        images_dir = public_dir / "images"
        images_dir.mkdir(parents=True)
        (images_dir / "icon.png").write_text("PNG")
        (public_dir / "manifest.json").write_text("{}")

        module_file = tmp_path / "register.py"
        module_file.write_text(
            """\
from pathlib import Path
from trellis.bundler.registry import ModuleRegistry

def register_module(registry):
    registry.register("test-module", static_files={"public": Path(__file__).parent / "public"})
"""
        )

        registry = ModuleRegistry()
        import importlib.util

        spec = importlib.util.spec_from_file_location("register", module_file)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.register_module(registry)

        collected = registry.collect()
        static = collected.modules[0].static_files
        assert "public/manifest.json" in static
        assert "public/images/icon.png" in static
