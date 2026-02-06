"""Unit tests for trellis.bundler.workspace module."""

from __future__ import annotations

from pathlib import Path

import pytest

from trellis.app.apploader import AppLoader, set_apploader
from trellis.bundler.registry import CollectedModules, ExportKind, Module, ModuleExport
from trellis.bundler.workspace import (
    generate_registry_ts,
    get_dist_dir,
    get_workspace_dir,
    node_modules_path,
    write_registry_ts,
)


def test_node_modules_path_returns_workspace_node_modules(tmp_path: Path) -> None:
    """node_modules_path returns workspace/node_modules."""
    workspace = tmp_path / "workspace"
    result = node_modules_path(workspace)
    assert result == workspace / "node_modules"


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


class TestWriteRegistryTs:
    """Tests for write_registry_ts function."""

    def test_writes_registry_file(self, tmp_path: Path) -> None:
        """Writes _registry.ts file to workspace directory."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        collected = CollectedModules(
            modules=[
                Module(
                    name="widgets",
                    exports=[
                        ModuleExport("Button", ExportKind.COMPONENT, "Button.tsx"),
                    ],
                ),
            ],
            packages={},
        )

        result = write_registry_ts(workspace, collected)

        assert result == workspace / "_registry.ts"
        assert result.exists()
        content = result.read_text()
        assert "registerWidget" in content
        assert "Button" in content

    def test_returns_path_to_file(self, tmp_path: Path) -> None:
        """Returns the path to the written file."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        collected = CollectedModules(modules=[], packages={})

        result = write_registry_ts(workspace, collected)

        assert isinstance(result, Path)
        assert result.name == "_registry.ts"

    def test_creates_workspace_if_needed(self, tmp_path: Path) -> None:
        """Creates workspace directory if it doesn't exist."""
        workspace = tmp_path / "new_workspace"
        collected = CollectedModules(modules=[], packages={})

        result = write_registry_ts(workspace, collected)

        assert workspace.is_dir()
        assert result.exists()


class TestGenerateRegistryTs:
    """Tests for generate_registry_ts function."""

    def test_imports_components(self) -> None:
        """Generates import statements for component exports."""
        collected = CollectedModules(
            modules=[
                Module(
                    name="my-widgets",
                    exports=[
                        ModuleExport("Button", ExportKind.COMPONENT, "Button.tsx"),
                        ModuleExport("Card", ExportKind.COMPONENT, "Card.tsx"),
                    ],
                ),
            ],
            packages={},
        )

        code = generate_registry_ts(collected)

        assert 'import { Button } from "@trellis/my-widgets/Button";' in code
        assert 'import { Card } from "@trellis/my-widgets/Card";' in code

    def test_registers_components(self) -> None:
        """Generates registerWidget calls for component exports."""
        collected = CollectedModules(
            modules=[
                Module(
                    name="my-widgets",
                    exports=[
                        ModuleExport("Button", ExportKind.COMPONENT, "Button.tsx"),
                    ],
                ),
            ],
            packages={},
        )

        code = generate_registry_ts(collected)

        assert 'registerWidget("Button", Button);' in code

    def test_exports_functions(self) -> None:
        """Re-exports function exports."""
        collected = CollectedModules(
            modules=[
                Module(
                    name="utils",
                    exports=[
                        ModuleExport("formatDate", ExportKind.FUNCTION, "format.ts"),
                    ],
                ),
            ],
            packages={},
        )

        code = generate_registry_ts(collected)

        assert 'import { formatDate } from "@trellis/utils/format";' in code
        assert "export { formatDate };" in code

    def test_imports_initializers(self) -> None:
        """Generates import statements for initializer exports (side-effect imports)."""
        collected = CollectedModules(
            modules=[
                Module(
                    name="setup",
                    exports=[
                        ModuleExport("polyfills", ExportKind.INITIALIZER, "polyfills.ts"),
                    ],
                ),
            ],
            packages={},
        )

        code = generate_registry_ts(collected)

        # Initializers are imported for side effects
        assert 'import "@trellis/setup/polyfills";' in code

    def test_includes_registerWidget_import(self) -> None:
        """Includes import for registerWidget when there are components."""
        collected = CollectedModules(
            modules=[
                Module(
                    name="widgets",
                    exports=[
                        ModuleExport("Button", ExportKind.COMPONENT, "Button.tsx"),
                    ],
                ),
            ],
            packages={},
        )

        code = generate_registry_ts(collected)

        assert "registerWidget" in code
        # Should import from trellis-core widgets
        assert "@trellis/trellis-core/widgets" in code

    def test_exports_initRegistry_function(self) -> None:
        """Exports an initRegistry function that registers all components."""
        collected = CollectedModules(
            modules=[
                Module(
                    name="widgets",
                    exports=[
                        ModuleExport("Button", ExportKind.COMPONENT, "Button.tsx"),
                    ],
                ),
            ],
            packages={},
        )

        code = generate_registry_ts(collected)

        assert "export function initRegistry()" in code

    def test_imports_stylesheets(self) -> None:
        """Generates import statements for stylesheet exports (keeps .css extension)."""
        collected = CollectedModules(
            modules=[
                Module(
                    name="my-theme",
                    exports=[
                        ModuleExport("styles", ExportKind.STYLESHEET, "theme.css"),
                    ],
                ),
            ],
            packages={},
        )

        code = generate_registry_ts(collected)

        # Stylesheets are imported for side effects, keeping .css extension
        assert 'import "@trellis/my-theme/theme.css";' in code
