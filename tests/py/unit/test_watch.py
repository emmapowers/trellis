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

    def test_includes_module_base_directory(self, tmp_path: Path) -> None:
        """Watch paths include module base directories."""
        from trellis.bundler.watch import get_watch_paths

        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        module_dir = tmp_path / "my-module"
        module_dir.mkdir()
        (module_dir / "Widget.tsx").write_text("// widget")
        (module_dir / "utils.ts").write_text("// utils")

        module = Module(
            name="my-module",
            _base_path=module_dir,
        )
        collected = CollectedModules(modules=[module], packages={})

        paths = get_watch_paths(entry_point, collected)

        # Should watch the module directory, not individual files
        assert module_dir in paths

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

    def test_skips_module_without_base_path(self, tmp_path: Path) -> None:
        """Modules without _base_path are skipped for directory watching."""
        from trellis.bundler.watch import get_watch_paths

        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        module = Module(
            name="my-module",
            _base_path=None,
        )
        collected = CollectedModules(modules=[module], packages={})

        paths = get_watch_paths(entry_point, collected)

        # Should just have entry point, no module directory
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

    def test_returns_directories_directly_for_module_paths(self, tmp_path: Path) -> None:
        """Watch directories include module base paths directly."""
        from trellis.bundler.watch import get_watch_directories

        entry_point = tmp_path / "src" / "app.tsx"
        entry_point.parent.mkdir(parents=True)
        entry_point.write_text("// entry")

        module_dir = tmp_path / "modules" / "my-module"
        module_dir.mkdir(parents=True)
        (module_dir / "Widget.tsx").write_text("// widget")

        module = Module(
            name="my-module",
            _base_path=module_dir,
        )
        collected = CollectedModules(modules=[module], packages={})

        directories = get_watch_directories(entry_point, collected)

        # Entry point's parent (it's a file) and module_dir (it's a directory)
        assert entry_point.parent in directories
        assert module_dir in directories

    def test_deduplicates_directories(self, tmp_path: Path) -> None:
        """Multiple modules with same base result in one directory."""
        from trellis.bundler.watch import get_watch_directories

        entry_point = tmp_path / "app.tsx"
        entry_point.write_text("// entry")

        module_dir = tmp_path / "my-module"
        module_dir.mkdir()
        (module_dir / "a.tsx").write_text("// a")
        (module_dir / "b.tsx").write_text("// b")

        # Two modules pointing to the same directory
        module1 = Module(name="module-a", _base_path=module_dir)
        module2 = Module(name="module-b", _base_path=module_dir)
        collected = CollectedModules(modules=[module1, module2], packages={})

        directories = get_watch_directories(entry_point, collected)

        # Should deduplicate directories
        assert isinstance(directories, set)
        assert module_dir in directories


class TestWatchAndRebuildSignature:
    """Tests for watch_and_rebuild function signature."""

    def test_accepts_steps_parameter(self) -> None:
        """watch_and_rebuild accepts a steps parameter."""
        import inspect

        from trellis.bundler.watch import watch_and_rebuild

        sig = inspect.signature(watch_and_rebuild)
        params = list(sig.parameters.keys())

        assert "steps" in params

    def test_on_rebuild_signature(self) -> None:
        """watch_and_rebuild accepts an on_rebuild callback parameter."""
        import inspect

        from trellis.bundler.watch import watch_and_rebuild

        sig = inspect.signature(watch_and_rebuild)
        params = list(sig.parameters.keys())

        assert "on_rebuild" in params

    def test_on_rebuild_default_is_none(self) -> None:
        """on_rebuild parameter defaults to None."""
        import inspect

        from trellis.bundler.watch import watch_and_rebuild

        sig = inspect.signature(watch_and_rebuild)
        param = sig.parameters["on_rebuild"]

        assert param.default is None
