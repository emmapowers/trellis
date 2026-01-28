"""Unit tests for trellis.bundler.registry module."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from trellis.bundler.registry import (
    CollectedModules,
    ExportKind,
    Module,
    ModuleExport,
    ModuleRegistry,
    registry,
)


class TestModuleExport:
    """Tests for ModuleExport dataclass."""

    def test_creation(self) -> None:
        """ModuleExport can be created with required fields."""
        export = ModuleExport(
            name="Button",
            kind=ExportKind.COMPONENT,
            source="widgets/Button.tsx",
        )
        assert export.name == "Button"
        assert export.kind == ExportKind.COMPONENT
        assert export.source == "widgets/Button.tsx"


class TestModule:
    """Tests for Module dataclass."""

    def test_creation_with_required_fields(self) -> None:
        """Module can be created with just name."""
        module = Module(name="my-module")
        assert module.name == "my-module"

    def test_packages_defaults_to_empty(self) -> None:
        """packages defaults to empty dict."""
        module = Module(name="my-module")
        assert module.packages == {}

    def test_exports_defaults_to_empty(self) -> None:
        """exports defaults to empty list."""
        module = Module(name="my-module")
        assert module.exports == []

    def test_base_path_defaults_to_none(self) -> None:
        """_base_path defaults to None."""
        module = Module(name="my-module")
        assert module._base_path is None

    def test_creation_with_all_fields(self) -> None:
        """Module can be created with all fields populated."""
        module = Module(
            name="my-module",
            packages={"react": "18.2.0"},
            exports=[ModuleExport("Widget", ExportKind.COMPONENT, "Widget.tsx")],
            _base_path=Path("/some/path"),
        )
        assert module.name == "my-module"
        assert module.packages == {"react": "18.2.0"}
        assert len(module.exports) == 1
        assert module.exports[0].name == "Widget"
        assert module._base_path == Path("/some/path")


class TestModuleRegistry:
    """Tests for ModuleRegistry class."""

    def test_register_stores_module(self) -> None:
        """register() stores module in registry."""
        registry = ModuleRegistry()
        registry.register("my-module", packages={"react": "18.2.0"})

        collected = registry.collect()
        assert len(collected.modules) == 1
        assert collected.modules[0].name == "my-module"
        assert collected.modules[0].packages == {"react": "18.2.0"}

    def test_register_resolves_paths_relative_to_caller(self, tmp_path: Path) -> None:
        """register() resolves base_path relative to calling file."""
        registry = ModuleRegistry()

        # Create a temporary module that registers itself
        module_file = tmp_path / "my_package" / "register.py"
        module_file.parent.mkdir(parents=True)

        # Write a registration script that we'll execute
        module_file.write_text(
            """\
from trellis.bundler.registry import ModuleRegistry

def register_module(registry):
    registry.register("test-module")
"""
        )

        # Execute the registration from that module's context
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
        registry = ModuleRegistry()
        registry.register("my-module")

        with pytest.raises(ValueError, match="already registered"):
            registry.register("my-module")

    def test_collect_returns_all_modules(self) -> None:
        """collect() returns all registered modules."""
        registry = ModuleRegistry()
        registry.register("module-a")
        registry.register("module-b")
        registry.register("module-c")

        collected = registry.collect()
        names = [m.name for m in collected.modules]
        assert names == ["module-a", "module-b", "module-c"]

    def test_collect_merges_packages(self) -> None:
        """collect() merges packages from all modules."""
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
        registry = ModuleRegistry()
        registry.register("module-a", packages={"react": "18.2.0"})
        registry.register("module-b", packages={"react": "18.2.0"})

        collected = registry.collect()
        assert collected.packages == {"react": "18.2.0"}

    def test_collect_errors_on_package_version_conflict(self) -> None:
        """collect() raises error if same package has different versions."""
        registry = ModuleRegistry()
        registry.register("module-a", packages={"react": "18.2.0"})
        registry.register("module-b", packages={"react": "17.0.0"})

        with pytest.raises(ValueError, match="version conflict"):
            registry.collect()

    def test_collect_errors_on_duplicate_component_name(self) -> None:
        """collect() raises error if two modules export components with same name."""
        registry = ModuleRegistry()
        registry.register(
            "module-a",
            exports=[("Button", ExportKind.COMPONENT, "Button.tsx")],
        )
        registry.register(
            "module-b",
            exports=[("Button", ExportKind.COMPONENT, "widgets/Button.tsx")],
        )

        with pytest.raises(ValueError, match=r"Export name collision.*Button"):
            registry.collect()

    def test_collect_errors_on_duplicate_function_name(self) -> None:
        """collect() raises error if two modules export functions with same name."""
        registry = ModuleRegistry()
        registry.register(
            "module-a",
            exports=[("formatDate", ExportKind.FUNCTION, "utils.ts")],
        )
        registry.register(
            "module-b",
            exports=[("formatDate", ExportKind.FUNCTION, "helpers.ts")],
        )

        with pytest.raises(ValueError, match=r"Export name collision.*formatDate"):
            registry.collect()

    def test_collect_allows_same_name_for_initializers(self) -> None:
        """collect() allows duplicate names for initializers (side-effect imports)."""
        registry = ModuleRegistry()
        registry.register(
            "module-a",
            exports=[("setup", ExportKind.INITIALIZER, "setup.ts")],
        )
        registry.register(
            "module-b",
            exports=[("setup", ExportKind.INITIALIZER, "setup.ts")],
        )

        # Should not raise - initializers don't create named bindings
        collected = registry.collect()
        assert len(collected.modules) == 2

    def test_collect_allows_same_name_for_stylesheets(self) -> None:
        """collect() allows duplicate names for stylesheets (side-effect imports)."""
        registry = ModuleRegistry()
        registry.register(
            "module-a",
            exports=[("styles", ExportKind.STYLESHEET, "theme.css")],
        )
        registry.register(
            "module-b",
            exports=[("styles", ExportKind.STYLESHEET, "base.css")],
        )

        # Should not raise - stylesheets don't create named bindings
        collected = registry.collect()
        assert len(collected.modules) == 2

    def test_collect_allows_same_name_different_kinds(self) -> None:
        """collect() allows same name if one is initializer/stylesheet."""
        registry = ModuleRegistry()
        registry.register(
            "module-a",
            exports=[("Button", ExportKind.COMPONENT, "Button.tsx")],
        )
        registry.register(
            "module-b",
            exports=[("Button", ExportKind.INITIALIZER, "Button.ts")],
        )

        # Should not raise - initializer doesn't conflict with component
        collected = registry.collect()
        assert len(collected.modules) == 2

    def test_clear_removes_all_modules(self) -> None:
        """clear() removes all registered modules."""
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
        assert isinstance(registry, ModuleRegistry)

    def test_global_registry_is_singleton(self) -> None:
        """Multiple imports return same registry instance."""
        # Verify that the registry accessed via the package is the same singleton
        # Note: trellis.bundler.registry (the attribute) is the ModuleRegistry instance,
        # not the module, because __init__.py re-exports it
        import trellis.bundler  # noqa: PLC0415

        assert trellis.bundler.registry is registry
