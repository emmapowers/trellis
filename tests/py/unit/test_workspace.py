"""Unit tests for trellis.bundler.workspace module."""

from __future__ import annotations

from pathlib import Path

from trellis.bundler.registry import CollectedModules, ExportKind, Module, ModuleExport


class TestFindProjectRoot:
    """Tests for find_project_root function."""

    def test_finds_pyproject_toml(self, tmp_path: Path) -> None:
        """Finds project root by pyproject.toml presence."""
        from trellis.bundler.utils import find_project_root

        # Create pyproject.toml in project root
        (tmp_path / "pyproject.toml").touch()
        # Create nested entry point
        nested = tmp_path / "src" / "app"
        nested.mkdir(parents=True)
        entry_point = nested / "main.py"
        entry_point.touch()

        result = find_project_root(entry_point)

        assert result == tmp_path

    def test_finds_git_directory(self, tmp_path: Path) -> None:
        """Finds project root by .git directory presence."""
        from trellis.bundler.utils import find_project_root

        # Create .git directory in project root
        (tmp_path / ".git").mkdir()
        # Create nested entry point
        nested = tmp_path / "src"
        nested.mkdir()
        entry_point = nested / "app.py"
        entry_point.touch()

        result = find_project_root(entry_point)

        assert result == tmp_path

    def test_finds_git_file_for_worktrees(self, tmp_path: Path) -> None:
        """Finds project root by .git file presence (git worktree case)."""
        from trellis.bundler.utils import find_project_root

        # Create .git file (not directory) like in worktrees
        (tmp_path / ".git").write_text("gitdir: /some/path/.git/worktrees/foo")
        # Create entry point
        entry_point = tmp_path / "app.py"
        entry_point.touch()

        result = find_project_root(entry_point)

        assert result == tmp_path

    def test_pyproject_toml_takes_priority_over_git(self, tmp_path: Path) -> None:
        """pyproject.toml is preferred over .git when both exist at different levels."""
        from trellis.bundler.utils import find_project_root

        # Create .git in parent
        parent = tmp_path / "parent"
        parent.mkdir()
        (parent / ".git").mkdir()

        # Create pyproject.toml in child (closer to entry point)
        child = parent / "child"
        child.mkdir()
        (child / "pyproject.toml").touch()

        # Entry point in child
        entry_point = child / "app.py"
        entry_point.touch()

        result = find_project_root(entry_point)

        # Should find pyproject.toml first (closer)
        assert result == child

    def test_fallback_to_entry_point_parent(self, tmp_path: Path) -> None:
        """Falls back to entry point parent when no markers found."""
        from trellis.bundler.utils import find_project_root

        # Create entry point with no project markers above
        subdir = tmp_path / "isolated"
        subdir.mkdir()
        entry_point = subdir / "app.py"
        entry_point.touch()

        result = find_project_root(entry_point)

        assert result == subdir

    def test_handles_entry_point_in_root(self, tmp_path: Path) -> None:
        """Works when entry point is directly in project root."""
        from trellis.bundler.utils import find_project_root

        (tmp_path / "pyproject.toml").touch()
        entry_point = tmp_path / "app.py"
        entry_point.touch()

        result = find_project_root(entry_point)

        assert result == tmp_path


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


class TestGetProjectWorkspace:
    """Tests for get_project_workspace function."""

    def test_returns_project_local_trellis_directory(self, tmp_path: Path) -> None:
        """Workspace is under .trellis in project root, not global cache."""
        from trellis.bundler.workspace import get_project_workspace

        # Create project with pyproject.toml
        (tmp_path / "pyproject.toml").touch()
        entry_point = tmp_path / "app.py"
        entry_point.touch()

        workspace = get_project_workspace(entry_point)

        # Should be under .trellis in project root
        assert workspace.parent.parent == tmp_path
        assert workspace.parent.name == ".trellis"

    def test_creates_trellis_directory_if_needed(self, tmp_path: Path) -> None:
        """Creates .trellis directory and workspace if they don't exist."""
        from trellis.bundler.workspace import get_project_workspace

        (tmp_path / "pyproject.toml").touch()
        entry_point = tmp_path / "app.py"
        entry_point.touch()

        workspace = get_project_workspace(entry_point)

        assert workspace.exists()
        assert workspace.is_dir()

    def test_uses_project_hash_for_workspace_name(self, tmp_path: Path) -> None:
        """Workspace subdirectory is named by project hash."""
        from trellis.bundler.workspace import get_project_hash, get_project_workspace

        (tmp_path / "pyproject.toml").touch()
        entry_point = tmp_path / "app.py"
        entry_point.touch()

        workspace = get_project_workspace(entry_point)
        expected_hash = get_project_hash(entry_point)

        assert workspace.name == expected_hash

    def test_different_entry_points_get_different_workspaces(self, tmp_path: Path) -> None:
        """Different entry points get separate workspace directories."""
        from trellis.bundler.workspace import get_project_workspace

        (tmp_path / "pyproject.toml").touch()

        entry1 = tmp_path / "app1.py"
        entry1.touch()
        entry2 = tmp_path / "app2.py"
        entry2.touch()

        workspace1 = get_project_workspace(entry1)
        workspace2 = get_project_workspace(entry2)

        # Both under same .trellis but different subdirs
        assert workspace1.parent == workspace2.parent
        assert workspace1 != workspace2


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
        from trellis.bundler.workspace import generate_registry_ts

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
        from trellis.bundler.workspace import generate_registry_ts

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
        from trellis.bundler.workspace import generate_registry_ts

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
        from trellis.bundler.workspace import generate_registry_ts

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
        from trellis.bundler.workspace import generate_registry_ts

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
        from trellis.bundler.workspace import generate_registry_ts

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
