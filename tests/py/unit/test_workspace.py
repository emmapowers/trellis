"""Unit tests for trellis.bundler.workspace module."""

from __future__ import annotations

from pathlib import Path

from trellis.bundler.registry import CollectedModules, ExportKind, Module, ModuleExport


class TestGetProjectHash:
    """Tests for get_project_hash function."""

    def test_consistent_hash_for_same_path(self) -> None:
        """Same path always produces same hash."""
        from trellis.bundler.workspace import get_project_hash

        path = Path("/some/project/app.py")
        hash1 = get_project_hash(path)
        hash2 = get_project_hash(path)
        assert hash1 == hash2

    def test_different_hash_for_different_paths(self) -> None:
        """Different paths produce different hashes."""
        from trellis.bundler.workspace import get_project_hash

        hash1 = get_project_hash(Path("/project1/app.py"))
        hash2 = get_project_hash(Path("/project2/app.py"))
        assert hash1 != hash2


class TestWriteRegistryTs:
    """Tests for write_registry_ts function."""

    def test_writes_registry_file(self, tmp_path: Path) -> None:
        """Writes _registry.ts file to workspace directory."""
        from trellis.bundler.workspace import write_registry_ts

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        collected = CollectedModules(
            modules=[
                Module(
                    name="widgets",
                    exports=[
                        ModuleExport("Button", ExportKind.component, "Button.tsx"),
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
        from trellis.bundler.workspace import write_registry_ts

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        collected = CollectedModules(modules=[], packages={})

        result = write_registry_ts(workspace, collected)

        assert isinstance(result, Path)
        assert result.name == "_registry.ts"

    def test_creates_workspace_if_needed(self, tmp_path: Path) -> None:
        """Creates workspace directory if it doesn't exist."""
        from trellis.bundler.workspace import write_registry_ts

        workspace = tmp_path / "new_workspace"
        collected = CollectedModules(modules=[], packages={})

        result = write_registry_ts(workspace, collected)

        assert workspace.is_dir()
        assert result.exists()


class TestGenerateRegistryTs:
    """Tests for generate_registry_ts function."""

    def test_imports_components(self) -> None:
        """Generates import statements for component exports."""
        from trellis.bundler.workspace import generate_registry_ts

        collected = CollectedModules(
            modules=[
                Module(
                    name="my-widgets",
                    exports=[
                        ModuleExport("Button", ExportKind.component, "Button.tsx"),
                        ModuleExport("Card", ExportKind.component, "Card.tsx"),
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
        from trellis.bundler.workspace import generate_registry_ts

        collected = CollectedModules(
            modules=[
                Module(
                    name="my-widgets",
                    exports=[
                        ModuleExport("Button", ExportKind.component, "Button.tsx"),
                    ],
                ),
            ],
            packages={},
        )

        code = generate_registry_ts(collected)

        assert 'registerWidget("Button", Button);' in code

    def test_exports_functions(self) -> None:
        """Re-exports function exports."""
        from trellis.bundler.workspace import generate_registry_ts

        collected = CollectedModules(
            modules=[
                Module(
                    name="utils",
                    exports=[
                        ModuleExport("formatDate", ExportKind.function, "format.ts"),
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
        from trellis.bundler.workspace import generate_registry_ts

        collected = CollectedModules(
            modules=[
                Module(
                    name="setup",
                    exports=[
                        ModuleExport("polyfills", ExportKind.initializer, "polyfills.ts"),
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
        from trellis.bundler.workspace import generate_registry_ts

        collected = CollectedModules(
            modules=[
                Module(
                    name="widgets",
                    exports=[
                        ModuleExport("Button", ExportKind.component, "Button.tsx"),
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
        from trellis.bundler.workspace import generate_registry_ts

        collected = CollectedModules(
            modules=[
                Module(
                    name="widgets",
                    exports=[
                        ModuleExport("Button", ExportKind.component, "Button.tsx"),
                    ],
                ),
            ],
            packages={},
        )

        code = generate_registry_ts(collected)

        assert "export function initRegistry()" in code
