"""Unit tests for trellis.bundler module."""

from __future__ import annotations

import io
import json
import tarfile
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from trellis.bundler.build import _collect_input_files, is_rebuild_needed
from trellis.bundler.metafile import get_metafile_path, read_metafile
from trellis.bundler.steps import BuildContext, IndexHtmlRenderStep
from trellis.bundler.utils import safe_extract as _safe_extract
from trellis.bundler.watch import get_watch_paths


class TestSafeExtract:
    """Tests for _safe_extract tarball security."""

    def test_safe_extract_normal_paths(self, tmp_path: Path) -> None:
        """Normal paths extract successfully."""
        # Create a tarball with normal paths
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
            # Add a file
            data = b"hello world"
            info = tarfile.TarInfo(name="package/index.js")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

            # Add a subdirectory file
            data2 = b"nested content"
            info2 = tarfile.TarInfo(name="package/lib/utils.js")
            info2.size = len(data2)
            tar.addfile(info2, io.BytesIO(data2))

        tar_buffer.seek(0)
        with tarfile.open(fileobj=tar_buffer, mode="r:gz") as tar:
            _safe_extract(tar, tmp_path)

        assert (tmp_path / "package" / "index.js").read_bytes() == b"hello world"
        assert (tmp_path / "package" / "lib" / "utils.js").read_bytes() == b"nested content"

    def test_safe_extract_rejects_parent_traversal(self, tmp_path: Path) -> None:
        """Rejects paths with parent directory traversal."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
            data = b"malicious"
            info = tarfile.TarInfo(name="../../../etc/passwd")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

        tar_buffer.seek(0)
        with tarfile.open(fileobj=tar_buffer, mode="r:gz") as tar:
            with pytest.raises(ValueError, match="path traversal"):
                _safe_extract(tar, tmp_path)

    def test_safe_extract_rejects_hidden_traversal(self, tmp_path: Path) -> None:
        """Rejects paths with hidden traversal in middle of path."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
            data = b"malicious"
            info = tarfile.TarInfo(name="package/../../../etc/passwd")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

        tar_buffer.seek(0)
        with tarfile.open(fileobj=tar_buffer, mode="r:gz") as tar:
            with pytest.raises(ValueError, match="path traversal"):
                _safe_extract(tar, tmp_path)

    def test_safe_extract_rejects_absolute_paths(self, tmp_path: Path) -> None:
        """Rejects absolute paths that escape destination."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
            data = b"malicious"
            info = tarfile.TarInfo(name="/etc/passwd")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

        tar_buffer.seek(0)
        with tarfile.open(fileobj=tar_buffer, mode="r:gz") as tar:
            with pytest.raises(ValueError, match="path traversal"):
                _safe_extract(tar, tmp_path)

    def test_safe_extract_rejects_symlinks(self, tmp_path: Path) -> None:
        """Rejects symlink entries to prevent link-based escapes."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
            # Add a symlink pointing outside destination
            info = tarfile.TarInfo(name="package/link")
            info.type = tarfile.SYMTYPE
            info.linkname = "/etc/passwd"
            tar.addfile(info)

        tar_buffer.seek(0)
        with tarfile.open(fileobj=tar_buffer, mode="r:gz") as tar:
            with pytest.raises(ValueError, match="link entry"):
                _safe_extract(tar, tmp_path)

    def test_safe_extract_rejects_hardlinks(self, tmp_path: Path) -> None:
        """Rejects hardlink entries to prevent link-based escapes."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
            # Add a hardlink
            info = tarfile.TarInfo(name="package/hardlink")
            info.type = tarfile.LNKTYPE
            info.linkname = "package/original"
            tar.addfile(info)

        tar_buffer.seek(0)
        with tarfile.open(fileobj=tar_buffer, mode="r:gz") as tar:
            with pytest.raises(ValueError, match="link entry"):
                _safe_extract(tar, tmp_path)


class TestIsRebuildNeeded:
    """Tests for incremental build checking."""

    def test_rebuild_needed_when_output_missing(self, tmp_path: Path) -> None:
        """Rebuild is needed when output files don't exist."""
        input_file = tmp_path / "input.ts"
        input_file.write_text("const x = 1;")
        output_file = tmp_path / "bundle.js"
        # output doesn't exist

        assert is_rebuild_needed([input_file], [output_file]) is True

    def test_rebuild_not_needed_when_output_newer(self, tmp_path: Path) -> None:
        """Rebuild not needed when output is newer than all inputs."""
        input_file = tmp_path / "input.ts"
        input_file.write_text("const x = 1;")

        time.sleep(0.01)  # Ensure different mtime

        output_file = tmp_path / "bundle.js"
        output_file.write_text("bundled")

        assert is_rebuild_needed([input_file], [output_file]) is False

    def test_rebuild_needed_when_input_newer(self, tmp_path: Path) -> None:
        """Rebuild is needed when any input is newer than output."""
        output_file = tmp_path / "bundle.js"
        output_file.write_text("bundled")

        time.sleep(0.01)  # Ensure different mtime

        input_file = tmp_path / "input.ts"
        input_file.write_text("const x = 1;")

        assert is_rebuild_needed([input_file], [output_file]) is True

    def test_rebuild_needed_when_any_input_newer(self, tmp_path: Path) -> None:
        """Rebuild is needed when any one input is newer than output."""
        # Create inputs first
        input1 = tmp_path / "input1.ts"
        input1.write_text("const x = 1;")

        time.sleep(0.01)

        # Create output
        output_file = tmp_path / "bundle.js"
        output_file.write_text("bundled")

        time.sleep(0.01)

        # Create second input after output
        input2 = tmp_path / "input2.ts"
        input2.write_text("const y = 2;")

        assert is_rebuild_needed([input1, input2], [output_file]) is True

    def test_rebuild_checks_all_outputs(self, tmp_path: Path) -> None:
        """Rebuild is needed if any output is missing."""
        input_file = tmp_path / "input.ts"
        input_file.write_text("const x = 1;")

        time.sleep(0.01)

        output_js = tmp_path / "bundle.js"
        output_js.write_text("bundled")
        output_css = tmp_path / "bundle.css"
        # css doesn't exist

        assert is_rebuild_needed([input_file], [output_js, output_css]) is True

    def test_rebuild_not_needed_with_empty_inputs(self, tmp_path: Path) -> None:
        """No rebuild needed if no inputs (edge case)."""
        output_file = tmp_path / "bundle.js"
        output_file.write_text("bundled")

        assert is_rebuild_needed([], [output_file]) is False


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


class TestCollectInputFiles:
    """Tests for _collect_input_files function."""

    def test_returns_metafile_inputs(self, tmp_path: Path) -> None:
        """_collect_input_files returns inputs from metafile."""
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

        inputs = _collect_input_files(workspace)

        assert len(inputs) == 2
        assert any(p.name == "main.tsx" for p in inputs)
        assert any(p.name == "Button.tsx" for p in inputs)

    def test_raises_when_metafile_missing(self, tmp_path: Path) -> None:
        """_collect_input_files raises FileNotFoundError when metafile doesn't exist."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        # No metafile.json

        with pytest.raises(FileNotFoundError):
            _collect_input_files(workspace)


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
            template_context={"source_json": '{"type": "code"}'},
        )

        assert ctx.template_context["source_json"] == '{"type": "code"}'

    def test_has_python_entry_point_default_none(self, tmp_path: Path) -> None:
        """BuildContext has python_entry_point field defaulting to None."""
        mock_registry = MagicMock()
        mock_collected = MagicMock()

        ctx = BuildContext(
            registry=mock_registry,
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=mock_collected,
            dist_dir=tmp_path / "dist",
        )

        assert ctx.python_entry_point is None

    def test_python_entry_point_can_be_set(self, tmp_path: Path) -> None:
        """BuildContext python_entry_point can be set to a Path."""
        mock_registry = MagicMock()
        mock_collected = MagicMock()
        app_path = tmp_path / "app.py"

        ctx = BuildContext(
            registry=mock_registry,
            entry_point=tmp_path / "main.tsx",
            workspace=tmp_path / "workspace",
            collected=mock_collected,
            dist_dir=tmp_path / "dist",
            python_entry_point=app_path,
        )

        assert ctx.python_entry_point == app_path


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
