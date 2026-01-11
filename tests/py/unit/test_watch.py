"""Unit tests for bundler watch functionality."""

from __future__ import annotations

from pathlib import Path

from trellis.bundler.registry import CollectedModules, Module


class TestGetWatchPaths:
    """Tests for collecting paths to watch."""

    def test_includes_entry_point(self, tmp_path: Path) -> None:
        """Watch paths include the entry point file."""
        from trellis.bundler.watch import get_watch_paths

        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        collected = CollectedModules(modules=[], packages={})

        paths = get_watch_paths(entry_point, collected)

        assert entry_point in paths

    def test_includes_module_files(self, tmp_path: Path) -> None:
        """Watch paths include all module source files."""
        from trellis.bundler.watch import get_watch_paths

        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        module_dir = tmp_path / "my-module"
        module_dir.mkdir()
        (module_dir / "Widget.tsx").write_text("// widget")
        (module_dir / "utils.ts").write_text("// utils")

        module = Module(
            name="my-module",
            files=["Widget.tsx", "utils.ts"],
            _base_path=module_dir,
        )
        collected = CollectedModules(modules=[module], packages={})

        paths = get_watch_paths(entry_point, collected)

        assert module_dir / "Widget.tsx" in paths
        assert module_dir / "utils.ts" in paths

    def test_includes_static_files(self, tmp_path: Path) -> None:
        """Watch paths include static file sources."""
        from trellis.bundler.watch import get_watch_paths

        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        static_file = tmp_path / "icon.png"
        static_file.write_bytes(b"PNG")

        module = Module(
            name="my-module",
            static_files={"icon.png": static_file},
        )
        collected = CollectedModules(modules=[module], packages={})

        paths = get_watch_paths(entry_point, collected)

        assert static_file in paths

    def test_excludes_snippets(self, tmp_path: Path) -> None:
        """Snippets are not included in watch paths (they're inline code)."""
        from trellis.bundler.watch import get_watch_paths

        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        module = Module(
            name="my-module",
            snippets={"helper.ts": "export const x = 1;"},
        )
        collected = CollectedModules(modules=[module], packages={})

        paths = get_watch_paths(entry_point, collected)

        # Only entry point should be in paths
        assert len(paths) == 1
        assert entry_point in paths

    def test_skips_module_without_base_path(self, tmp_path: Path) -> None:
        """Modules without _base_path are skipped for file watching."""
        from trellis.bundler.watch import get_watch_paths

        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        module = Module(
            name="my-module",
            files=["Widget.tsx"],  # Files without base path can't be resolved
            _base_path=None,
        )
        collected = CollectedModules(modules=[module], packages={})

        paths = get_watch_paths(entry_point, collected)

        # Should just have entry point, no module files
        assert len(paths) == 1

    def test_returns_set_of_paths(self, tmp_path: Path) -> None:
        """Watch paths are returned as a set (no duplicates)."""
        from trellis.bundler.watch import get_watch_paths

        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        collected = CollectedModules(modules=[], packages={})

        paths = get_watch_paths(entry_point, collected)

        assert isinstance(paths, set)


class TestGetWatchDirectories:
    """Tests for collecting directories to watch."""

    def test_returns_parent_directories(self, tmp_path: Path) -> None:
        """Watch directories are parent directories of watch paths."""
        from trellis.bundler.watch import get_watch_directories

        entry_point = tmp_path / "src" / "app.tsx"
        entry_point.parent.mkdir(parents=True)
        entry_point.write_text("// entry")

        module_dir = tmp_path / "modules" / "my-module"
        module_dir.mkdir(parents=True)
        (module_dir / "Widget.tsx").write_text("// widget")

        module = Module(
            name="my-module",
            files=["Widget.tsx"],
            _base_path=module_dir,
        )
        collected = CollectedModules(modules=[module], packages={})

        directories = get_watch_directories(entry_point, collected)

        assert entry_point.parent in directories
        assert module_dir in directories

    def test_deduplicates_directories(self, tmp_path: Path) -> None:
        """Multiple files in same directory result in one directory."""
        from trellis.bundler.watch import get_watch_directories

        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        module_dir = tmp_path / "my-module"
        module_dir.mkdir()
        (module_dir / "a.tsx").write_text("// a")
        (module_dir / "b.tsx").write_text("// b")

        module = Module(
            name="my-module",
            files=["a.tsx", "b.tsx"],
            _base_path=module_dir,
        )
        collected = CollectedModules(modules=[module], packages={})

        directories = get_watch_directories(entry_point, collected)

        # Should have entry_point parent and module_dir
        assert isinstance(directories, set)
        assert module_dir in directories
