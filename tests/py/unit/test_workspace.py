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


class TestStageWorkspace:
    """Tests for stage_workspace function."""

    def test_creates_module_directories(self, tmp_path: Path) -> None:
        """Creates a directory for each module in staged/."""
        from trellis.bundler.workspace import stage_workspace

        workspace = tmp_path / "workspace"
        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        collected = CollectedModules(
            modules=[
                Module(name="module-a"),
                Module(name="module-b"),
            ],
            packages={},
        )

        stage_workspace(workspace, collected, entry_point)

        assert (workspace / "staged" / "module-a").is_dir()
        assert (workspace / "staged" / "module-b").is_dir()

    def test_copies_files_from_modules(self, tmp_path: Path) -> None:
        """Copies files from module's base path to staged directory."""
        from trellis.bundler.workspace import stage_workspace

        # Set up module source directory
        module_src = tmp_path / "src" / "my_module"
        module_src.mkdir(parents=True)
        (module_src / "Widget.tsx").write_text("export const Widget = () => null;")
        (module_src / "utils" / "helper.ts").parent.mkdir()
        (module_src / "utils" / "helper.ts").write_text("export const helper = () => {};")

        workspace = tmp_path / "workspace"
        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        collected = CollectedModules(
            modules=[
                Module(
                    name="my-module",
                    files=["Widget.tsx", "utils/helper.ts"],
                    _base_path=module_src,
                ),
            ],
            packages={},
        )

        stage_workspace(workspace, collected, entry_point)

        staged_widget = workspace / "staged" / "my-module" / "Widget.tsx"
        staged_helper = workspace / "staged" / "my-module" / "utils" / "helper.ts"

        assert staged_widget.exists()
        assert staged_widget.read_text() == "export const Widget = () => null;"
        assert staged_helper.exists()
        assert staged_helper.read_text() == "export const helper = () => {};"

    def test_writes_snippets_as_files(self, tmp_path: Path) -> None:
        """Writes snippet code as files in staged directory."""
        from trellis.bundler.workspace import stage_workspace

        workspace = tmp_path / "workspace"
        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        collected = CollectedModules(
            modules=[
                Module(
                    name="my-module",
                    snippets={
                        "Generated.tsx": "export const Generated = () => <div>Hi</div>;",
                        "nested/Config.ts": "export const config = {};",
                    },
                ),
            ],
            packages={},
        )

        stage_workspace(workspace, collected, entry_point)

        generated = workspace / "staged" / "my-module" / "Generated.tsx"
        config = workspace / "staged" / "my-module" / "nested" / "Config.ts"

        assert generated.exists()
        assert generated.read_text() == "export const Generated = () => <div>Hi</div>;"
        assert config.exists()
        assert config.read_text() == "export const config = {};"

    def test_copies_entry_point(self, tmp_path: Path) -> None:
        """Copies entry point file to workspace root."""
        from trellis.bundler.workspace import stage_workspace

        workspace = tmp_path / "workspace"
        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("import React from 'react';\n// app entry")

        collected = CollectedModules(modules=[], packages={})

        stage_workspace(workspace, collected, entry_point)

        staged_entry = workspace / "entry.tsx"
        assert staged_entry.exists()
        assert staged_entry.read_text() == "import React from 'react';\n// app entry"


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


class TestGenerateTsconfig:
    """Tests for generate_tsconfig function."""

    def test_includes_path_aliases_for_modules(self) -> None:
        """Generates path aliases for each module."""
        from trellis.bundler.workspace import generate_tsconfig

        collected = CollectedModules(
            modules=[
                Module(name="trellis-core"),
                Module(name="my-widgets"),
            ],
            packages={},
        )

        config = generate_tsconfig(collected)

        # Should be valid JSON
        import json

        parsed = json.loads(config)

        paths = parsed["compilerOptions"]["paths"]
        assert "@trellis/trellis-core/*" in paths
        assert "@trellis/my-widgets/*" in paths
        assert paths["@trellis/trellis-core/*"] == ["./staged/trellis-core/*"]
        assert paths["@trellis/my-widgets/*"] == ["./staged/my-widgets/*"]

    def test_includes_registry_alias(self) -> None:
        """Includes path alias for _registry module."""
        from trellis.bundler.workspace import generate_tsconfig

        collected = CollectedModules(modules=[], packages={})

        config = generate_tsconfig(collected)

        import json

        parsed = json.loads(config)
        paths = parsed["compilerOptions"]["paths"]
        assert "@trellis/_registry" in paths

    def test_valid_json_output(self) -> None:
        """Output is valid JSON."""
        from trellis.bundler.workspace import generate_tsconfig

        collected = CollectedModules(modules=[], packages={})

        config = generate_tsconfig(collected)

        import json

        # Should not raise
        json.loads(config)
