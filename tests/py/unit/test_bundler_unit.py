"""Unit tests for trellis.bundler module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from trellis.bundler.manifest import BuildManifest
from trellis.bundler.metafile import get_metafile_path, read_metafile
from trellis.bundler.steps import BuildContext, IndexHtmlRenderStep
from trellis.bundler.watch import get_watch_paths


class TestMetafile:
    """Tests for metafile parsing utilities."""

    def test_get_metafile_path_returns_workspace_path(self, tmp_path: Path) -> None:
        """get_metafile_path returns metafile.json in workspace."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        result = get_metafile_path(workspace)
        assert result == workspace / "metafile.json"

    def test_read_metafile_parses_inputs(self, tmp_path: Path) -> None:
        """read_metafile extracts input paths from metafile."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Create source files that the metafile references
        src_dir = workspace / "src"
        src_dir.mkdir()
        (src_dir / "main.tsx").write_text("// main")
        (src_dir / "Button.tsx").write_text("// button")

        # Create metafile with paths relative to workspace
        metafile_content = {
            "inputs": {
                "src/main.tsx": {"bytes": 1234, "imports": []},
                "src/Button.tsx": {"bytes": 567, "imports": []},
            },
            "outputs": {
                "dist/bundle.js": {"bytes": 5000, "inputs": {}},
            },
        }
        (workspace / "metafile.json").write_text(json.dumps(metafile_content))

        result = read_metafile(workspace)
        assert len(result.inputs) == 2
        # Paths should be absolute
        assert all(p.is_absolute() for p in result.inputs)
        assert any(p.name == "main.tsx" for p in result.inputs)
        assert any(p.name == "Button.tsx" for p in result.inputs)

    def test_read_metafile_parses_outputs(self, tmp_path: Path) -> None:
        """read_metafile extracts output paths from metafile."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        metafile_content = {
            "inputs": {"src/main.tsx": {"bytes": 1234, "imports": []}},
            "outputs": {
                "dist/bundle.js": {"bytes": 5000, "inputs": {}},
                "dist/bundle.css": {"bytes": 1000, "inputs": {}},
            },
        }
        (workspace / "metafile.json").write_text(json.dumps(metafile_content))

        result = read_metafile(workspace)
        assert len(result.outputs) == 2
        assert all(p.is_absolute() for p in result.outputs)
        assert any(p.name == "bundle.js" for p in result.outputs)
        assert any(p.name == "bundle.css" for p in result.outputs)

    def test_read_metafile_raises_on_missing(self, tmp_path: Path) -> None:
        """read_metafile raises FileNotFoundError when metafile doesn't exist."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        # No metafile.json created

        with pytest.raises(FileNotFoundError):
            read_metafile(workspace)

    def test_read_metafile_raises_on_invalid_json(self, tmp_path: Path) -> None:
        """read_metafile raises ValueError when metafile is invalid JSON."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / "metafile.json").write_text("not valid json")

        with pytest.raises(ValueError, match="Invalid JSON"):
            read_metafile(workspace)

    def test_read_metafile_filters_node_modules(self, tmp_path: Path) -> None:
        """read_metafile excludes node_modules from inputs."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        metafile_content = {
            "inputs": {
                "src/main.tsx": {"bytes": 1234, "imports": []},
                "node_modules/react/index.js": {"bytes": 9999, "imports": []},
                "../node_modules/lodash/lodash.js": {"bytes": 8888, "imports": []},
            },
            "outputs": {"dist/bundle.js": {"bytes": 5000, "inputs": {}}},
        }
        (workspace / "metafile.json").write_text(json.dumps(metafile_content))

        result = read_metafile(workspace)
        # Only source file, not node_modules
        assert len(result.inputs) == 1
        assert result.inputs[0].name == "main.tsx"


class TestGetWatchPaths:
    """Tests for get_watch_paths function."""

    def test_returns_metafile_inputs(self, tmp_path: Path) -> None:
        """get_watch_paths returns inputs from metafile as resolved paths."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Create metafile with specific inputs
        metafile_content = {
            "inputs": {
                "src/main.tsx": {"bytes": 100, "imports": []},
                "src/Button.tsx": {"bytes": 200, "imports": []},
            },
            "outputs": {"dist/bundle.js": {"bytes": 5000, "inputs": {}}},
        }
        (workspace / "metafile.json").write_text(json.dumps(metafile_content))

        paths = get_watch_paths(workspace)

        assert len(paths) == 2
        # Paths should be resolved (absolute)
        assert all(p.is_absolute() for p in paths)
        assert any(p.name == "main.tsx" for p in paths)
        assert any(p.name == "Button.tsx" for p in paths)

    def test_raises_when_metafile_missing(self, tmp_path: Path) -> None:
        """get_watch_paths raises FileNotFoundError when metafile doesn't exist."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        # No metafile.json

        with pytest.raises(FileNotFoundError):
            get_watch_paths(workspace)


class TestBuildContext:
    """Tests for BuildContext dataclass."""

    def test_has_template_context_default(self, tmp_path: Path) -> None:
        """BuildContext has template_context field with empty dict default."""
        mock_registry = MagicMock()
        mock_collected = MagicMock()

        ctx = BuildContext(
            registry=mock_registry,
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=mock_collected,
            dist_dir=tmp_path / "dist",
            manifest=BuildManifest(),
        )

        assert ctx.template_context == {}

    def test_template_context_can_be_set(self, tmp_path: Path) -> None:
        """BuildContext template_context can be set with custom values."""
        mock_registry = MagicMock()
        mock_collected = MagicMock()

        ctx = BuildContext(
            registry=mock_registry,
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=mock_collected,
            dist_dir=tmp_path / "dist",
            manifest=BuildManifest(),
            template_context={"source_json": '{"type": "code"}'},
        )

        assert ctx.template_context["source_json"] == '{"type": "code"}'

    def test_has_build_data_default_empty(self, tmp_path: Path) -> None:
        """BuildContext has build_data field defaulting to empty dict."""
        mock_registry = MagicMock()
        mock_collected = MagicMock()

        ctx = BuildContext(
            registry=mock_registry,
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=mock_collected,
            dist_dir=tmp_path / "dist",
            manifest=BuildManifest(),
        )

        assert ctx.build_data == {}

    def test_build_data_can_be_populated(self, tmp_path: Path) -> None:
        """BuildContext build_data can store arbitrary data between steps."""
        mock_registry = MagicMock()
        mock_collected = MagicMock()

        ctx = BuildContext(
            registry=mock_registry,
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=mock_collected,
            dist_dir=tmp_path / "dist",
            manifest=BuildManifest(),
        )

        ctx.build_data["resolved_deps"] = {"wheels": ["a.whl"]}
        assert ctx.build_data["resolved_deps"] == {"wheels": ["a.whl"]}


class TestIndexHtmlRenderStep:
    """Tests for IndexHtmlRenderStep template context handling."""

    def _make_context(self, tmp_path: Path, **kwargs) -> BuildContext:
        """Create a BuildContext for testing."""
        mock_registry = MagicMock()
        mock_collected = MagicMock()
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir(parents=True, exist_ok=True)
        return BuildContext(
            registry=mock_registry,
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=mock_collected,
            dist_dir=dist_dir,
            manifest=BuildManifest(),
            **kwargs,
        )

    def test_merges_template_context(self, tmp_path: Path) -> None:
        """Step merges BuildContext.template_context with constructor context."""
        # Create template (use |safe for JSON since it's embedded in JS, not displayed as HTML)
        template = tmp_path / "index.html.j2"
        template.write_text("source={{ source_json|safe }}, custom={{ custom_var }}")

        # Set up context with template_context containing source_json
        ctx = self._make_context(
            tmp_path,
            template_context={"source_json": '{"type": "code"}'},
        )

        step = IndexHtmlRenderStep(template, context={"custom_var": "hello"})
        step.run(ctx)

        output = (ctx.dist_dir / "index.html").read_text()
        assert 'source={"type": "code"}' in output
        assert "custom=hello" in output

    def test_constructor_context_overrides_template_context(self, tmp_path: Path) -> None:
        """Constructor context takes precedence over BuildContext.template_context."""
        template = tmp_path / "index.html.j2"
        template.write_text("value={{ shared_key }}")

        ctx = self._make_context(
            tmp_path,
            template_context={"shared_key": "from_build_context"},
        )

        # Constructor context should override
        step = IndexHtmlRenderStep(template, context={"shared_key": "from_constructor"})
        step.run(ctx)

        output = (ctx.dist_dir / "index.html").read_text()
        assert "value=from_constructor" in output

    def test_works_with_empty_contexts(self, tmp_path: Path) -> None:
        """Step works when both contexts are empty."""
        template = tmp_path / "index.html.j2"
        template.write_text("<html>static content</html>")

        ctx = self._make_context(tmp_path)
        step = IndexHtmlRenderStep(template)
        step.run(ctx)

        output = (ctx.dist_dir / "index.html").read_text()
        assert "static content" in output
