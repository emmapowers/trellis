"""Integration tests for incremental builds across platforms.

Tests the full build() function with real builds to verify that each
build step correctly detects when it needs to rebuild.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum, auto
from pathlib import Path
from typing import Any

import pytest

from trellis.bundler.build import build
from trellis.bundler.manifest import load_manifest
from trellis.bundler.registry import ModuleRegistry
from trellis.bundler.steps import (
    BuildStep,
    BundleBuildStep,
    DeclarationStep,
    IndexHtmlRenderStep,
    PackageInstallStep,
    RegistryGenerationStep,
    StaticFileCopyStep,
    TsconfigStep,
)
from trellis.platforms.browser.build_steps import (
    PyodideWorkerBuildStep,
    PythonSourceBundleStep,
    WheelCopyStep,
)

# =============================================================================
# Test Data Structures
# =============================================================================


class ActionType(StrEnum):
    """Actions that can trigger rebuilds."""

    NONE = auto()
    TOUCH_ENTRY_POINT = auto()
    TOUCH_TEMPLATE = auto()
    TOUCH_STATIC_FILE = auto()
    TOUCH_PYTHON_SOURCE = auto()
    TOUCH_WHEEL = auto()
    REGISTER_MODULE = auto()


@dataclass(frozen=True)
class IncrementalTestCase:
    """A single incremental build test case."""

    id: str
    action: ActionType
    rebuilds: frozenset[str]  # Step names expected to run


@dataclass
class ServerBuildSetup:
    """Everything needed to call build() for server platform."""

    registry: ModuleRegistry
    entry_point: Path
    workspace: Path
    steps: list[BuildStep]
    template_path: Path
    static_file: Path
    app_static_dir: Path


@dataclass
class BrowserBuildSetup:
    """Everything needed to call build() for browser platform."""

    registry: ModuleRegistry
    entry_point: Path
    workspace: Path
    steps: list[BuildStep]
    template_path: Path
    static_file: Path
    app_static_dir: Path
    python_entry_point: Path
    wheel_path: Path
    wheel_dir: Path


# =============================================================================
# Step Detection Infrastructure
# =============================================================================


@dataclass
class StepStates:
    """Recorded state for detecting which steps ran."""

    file_mtimes: dict[str, float] = field(default_factory=dict)  # step -> output mtime
    metadata: dict[str, dict[str, Any]] = field(default_factory=dict)  # step -> manifest metadata


@dataclass
class StepDetector:
    """How to detect if a step ran."""

    get_output: Callable[[Path, Path], Path | None] | None = None  # (workspace, dist) -> path
    metadata_changed: Callable[[dict[str, Any] | None, dict[str, Any] | None], bool] | None = None


# Detectors for each step type
STEP_DETECTORS: dict[str, StepDetector] = {
    "package-install": StepDetector(
        get_output=lambda ws, dist: ws / "node_modules" if (ws / "node_modules").exists() else None
    ),
    "registry-generation": StepDetector(
        get_output=lambda ws, dist: ws / "_registry.ts" if (ws / "_registry.ts").exists() else None
    ),
    "pyodide-worker-build": StepDetector(
        get_output=lambda ws, dist: (
            ws / "pyodide.worker-bundle" if (ws / "pyodide.worker-bundle").exists() else None
        )
    ),
    "bundle-build": StepDetector(
        get_output=lambda ws, dist: dist / "bundle.js" if (dist / "bundle.js").exists() else None
    ),
    "static-file-copy": StepDetector(
        get_output=lambda ws, dist: dist / "test.txt" if (dist / "test.txt").exists() else None
    ),
    "index-html-render": StepDetector(
        get_output=lambda ws, dist: dist / "index.html" if (dist / "index.html").exists() else None
    ),
    "declaration": StepDetector(
        get_output=lambda ws, dist: dist / "main.d.ts" if (dist / "main.d.ts").exists() else None
    ),
    # Steps that use metadata comparison instead of file output
    "python-source-bundle": StepDetector(metadata_changed=lambda old, new: old != new),
    "wheel-copy": StepDetector(metadata_changed=lambda old, new: old != new),
}


def record_step_states(steps: list[BuildStep], workspace: Path, dist_dir: Path) -> StepStates:
    """Record current state for all steps.

    Args:
        steps: List of build steps
        workspace: Workspace directory
        dist_dir: Distribution directory

    Returns:
        StepStates with file mtimes and manifest metadata
    """
    states = StepStates()

    # Record file mtimes for steps with file outputs
    for step in steps:
        detector = STEP_DETECTORS.get(step.name)
        if detector and detector.get_output:
            path = detector.get_output(workspace, dist_dir)
            if path:
                states.file_mtimes[step.name] = path.stat().st_mtime

    # Record manifest metadata for all steps
    manifest = load_manifest(workspace)
    if manifest:
        for step_name, step_manifest in manifest.steps.items():
            states.metadata[step_name] = step_manifest.metadata.copy()

    return states


def detect_steps_that_ran(before: StepStates, after: StepStates) -> set[str]:
    """Compare states to detect which steps ran.

    Args:
        before: States from before the build
        after: States from after the build

    Returns:
        Set of step names that ran
    """
    ran = set()

    for step_name, detector in STEP_DETECTORS.items():
        # Check file mtime changes
        if detector.get_output:
            current_mtime = after.file_mtimes.get(step_name, 0)
            prev_mtime = before.file_mtimes.get(step_name, 0)
            if current_mtime > prev_mtime:
                ran.add(step_name)

        # Check metadata changes
        if detector.metadata_changed:
            old_metadata = before.metadata.get(step_name)
            new_metadata = after.metadata.get(step_name)
            if detector.metadata_changed(old_metadata, new_metadata):
                ran.add(step_name)

    return ran


def apply_action(action: ActionType, setup: ServerBuildSetup | BrowserBuildSetup) -> None:
    """Apply an action to trigger rebuilds.

    Args:
        action: The action type to apply
        setup: Build setup to modify
    """
    time.sleep(0.01)  # Ensure mtime difference
    match action:
        case ActionType.NONE:
            pass
        case ActionType.TOUCH_ENTRY_POINT:
            setup.entry_point.touch()
        case ActionType.TOUCH_TEMPLATE:
            setup.template_path.touch()
        case ActionType.TOUCH_STATIC_FILE:
            setup.static_file.touch()
        case ActionType.TOUCH_PYTHON_SOURCE:
            if isinstance(setup, BrowserBuildSetup):
                # Modify content, not just mtime - otherwise source_json is unchanged
                # and IndexHtmlRenderStep won't detect a context change
                current = setup.python_entry_point.read_text()
                setup.python_entry_point.write_text(current + f"\n# {uuid.uuid4().hex}")
        case ActionType.TOUCH_WHEEL:
            if isinstance(setup, BrowserBuildSetup):
                # Create a new wheel file with updated mtime
                new_wheel = setup.wheel_dir / f"trellis-{uuid.uuid4().hex[:8]}-py3-none-any.whl"
                new_wheel.write_bytes(b"new wheel content")
        case ActionType.REGISTER_MODULE:
            setup.registry.register(f"new-module-{uuid.uuid4().hex[:8]}")


# =============================================================================
# Test Cases
# =============================================================================


SERVER_CASES = [
    IncrementalTestCase("no_changes", ActionType.NONE, frozenset()),
    IncrementalTestCase(
        "touch_template", ActionType.TOUCH_TEMPLATE, frozenset({"index-html-render"})
    ),
    IncrementalTestCase(
        "touch_static", ActionType.TOUCH_STATIC_FILE, frozenset({"static-file-copy"})
    ),
    IncrementalTestCase(
        "touch_entry_point", ActionType.TOUCH_ENTRY_POINT, frozenset({"bundle-build"})
    ),
    IncrementalTestCase(
        "register_module",
        ActionType.REGISTER_MODULE,
        frozenset({"registry-generation", "bundle-build"}),
    ),
]


BROWSER_APP_CASES = [
    IncrementalTestCase("no_changes", ActionType.NONE, frozenset()),
    IncrementalTestCase(
        "touch_template", ActionType.TOUCH_TEMPLATE, frozenset({"index-html-render"})
    ),
    IncrementalTestCase(
        "touch_python_source",
        ActionType.TOUCH_PYTHON_SOURCE,
        frozenset({"python-source-bundle", "index-html-render"}),
    ),
    IncrementalTestCase("touch_wheel", ActionType.TOUCH_WHEEL, frozenset({"wheel-copy"})),
    IncrementalTestCase(
        "touch_static", ActionType.TOUCH_STATIC_FILE, frozenset({"static-file-copy"})
    ),
    IncrementalTestCase(
        "touch_entry_point", ActionType.TOUCH_ENTRY_POINT, frozenset({"bundle-build"})
    ),
    IncrementalTestCase(
        "register_module",
        ActionType.REGISTER_MODULE,
        frozenset({"registry-generation", "bundle-build"}),
    ),
]


# =============================================================================
# Server Platform Tests
# =============================================================================


@pytest.mark.network
@pytest.mark.slow
class TestServerIncrementalBuilds:
    """Incremental build tests for server platform."""

    @pytest.fixture
    def server_build_setup(self, tmp_path: Path) -> ServerBuildSetup:
        """Set up files for server platform build."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Create minimal entry point that imports registry (so registry changes trigger rebuild)
        entry_point = tmp_path / "main.tsx"
        entry_point.write_text(
            """\
import React from "react";
import "@trellis/_registry";
export const App = () => <div>Hello</div>;
"""
        )

        # Create minimal template
        template_path = tmp_path / "index.html.j2"
        template_path.write_text(
            """\
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body><script src="{{ static_path }}/bundle.js" type="module"></script></body>
</html>
"""
        )

        # Create static dir with test file
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        static_file = static_dir / "test.txt"
        static_file.write_text("test content")

        # Registry with packages
        registry = ModuleRegistry()
        registry.register(
            "core", packages={"react": "18.2.0", "react-dom": "18.2.0", "typescript": "5.3.3"}
        )

        # Steps matching ServerPlatform
        steps: list[BuildStep] = [
            PackageInstallStep(),
            RegistryGenerationStep(),
            BundleBuildStep(output_name="bundle"),
            StaticFileCopyStep(),
            IndexHtmlRenderStep(template_path, {"static_path": "/static"}),
        ]

        return ServerBuildSetup(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=steps,
            template_path=template_path,
            static_file=static_file,
            app_static_dir=static_dir,
        )

    @pytest.mark.parametrize("case", SERVER_CASES, ids=lambda c: c.id)
    def test_incremental_build(
        self, case: IncrementalTestCase, server_build_setup: ServerBuildSetup
    ) -> None:
        """Test that the correct steps rebuild for each action."""
        setup = server_build_setup
        dist_dir = setup.workspace / "dist"

        # Initial force build
        build(
            registry=setup.registry,
            entry_point=setup.entry_point,
            workspace=setup.workspace,
            steps=setup.steps,
            app_static_dir=setup.app_static_dir,
            force=True,
        )

        # Record state
        before = record_step_states(setup.steps, setup.workspace, dist_dir)

        # Apply action
        apply_action(case.action, setup)

        # Incremental build
        build(
            registry=setup.registry,
            entry_point=setup.entry_point,
            workspace=setup.workspace,
            steps=setup.steps,
            app_static_dir=setup.app_static_dir,
            force=False,
        )

        # Record state after build and detect which steps ran
        after = record_step_states(setup.steps, setup.workspace, dist_dir)
        ran = detect_steps_that_ran(before, after)
        assert ran == case.rebuilds, f"Expected {case.rebuilds}, got {ran}"


# =============================================================================
# Browser Platform Tests
# =============================================================================


@pytest.mark.network
@pytest.mark.slow
class TestBrowserAppIncrementalBuilds:
    """Incremental build tests for browser app platform."""

    @pytest.fixture
    def browser_build_setup(self, tmp_path: Path) -> BrowserBuildSetup:
        """Set up files for browser platform build."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Create minimal entry point that imports registry (so registry changes trigger rebuild)
        entry_point = tmp_path / "main.tsx"
        entry_point.write_text(
            """\
import React from "react";
import "@trellis/_registry";
export const App = () => <div>Hello Browser</div>;
"""
        )

        # Create minimal template
        template_path = tmp_path / "index.html.j2"
        template_path.write_text(
            """\
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
{% if source_json %}<script id="source">{{ source_json }}</script>{% endif %}
<script src="{{ static_path }}/bundle.js" type="module"></script>
</body>
</html>
"""
        )

        # Create static dir with test file
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        static_file = static_dir / "test.txt"
        static_file.write_text("test content")

        # Create Python entry point
        python_dir = tmp_path / "app"
        python_dir.mkdir()
        python_entry = python_dir / "main.py"
        python_entry.write_text("print('hello')")

        # Create wheel directory and wheel file
        wheel_dir = tmp_path / "wheels"
        wheel_dir.mkdir()
        wheel_path = wheel_dir / "trellis-0.1.0-py3-none-any.whl"
        wheel_path.write_bytes(b"fake wheel content")

        # Registry with packages
        registry = ModuleRegistry()
        registry.register(
            "core", packages={"react": "18.2.0", "react-dom": "18.2.0", "typescript": "5.3.3"}
        )

        # Steps matching BrowserAppPlatform
        steps: list[BuildStep] = [
            PackageInstallStep(),
            RegistryGenerationStep(),
            PyodideWorkerBuildStep(),
            PythonSourceBundleStep(),
            BundleBuildStep(output_name="bundle"),
            WheelCopyStep(wheel_dir),
            StaticFileCopyStep(),
            IndexHtmlRenderStep(template_path, {"static_path": "/static"}),
        ]

        return BrowserBuildSetup(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=steps,
            template_path=template_path,
            static_file=static_file,
            app_static_dir=static_dir,
            python_entry_point=python_entry,
            wheel_path=wheel_path,
            wheel_dir=wheel_dir,
        )

    @pytest.mark.parametrize("case", BROWSER_APP_CASES, ids=lambda c: c.id)
    def test_incremental_build(
        self, case: IncrementalTestCase, browser_build_setup: BrowserBuildSetup
    ) -> None:
        """Test that the correct steps rebuild for each action."""
        setup = browser_build_setup
        dist_dir = setup.workspace / "dist"

        # Initial force build
        build(
            registry=setup.registry,
            entry_point=setup.entry_point,
            workspace=setup.workspace,
            steps=setup.steps,
            app_static_dir=setup.app_static_dir,
            python_entry_point=setup.python_entry_point,
            force=True,
        )

        # Record state
        before = record_step_states(setup.steps, setup.workspace, dist_dir)

        # Apply action
        apply_action(case.action, setup)

        # Incremental build
        build(
            registry=setup.registry,
            entry_point=setup.entry_point,
            workspace=setup.workspace,
            steps=setup.steps,
            app_static_dir=setup.app_static_dir,
            python_entry_point=setup.python_entry_point,
            force=False,
        )

        # Record state after build and detect which steps ran
        after = record_step_states(setup.steps, setup.workspace, dist_dir)
        ran = detect_steps_that_ran(before, after)
        assert ran == case.rebuilds, f"Expected {case.rebuilds}, got {ran}"


# =============================================================================
# DeclarationStep Tests (non-library mode)
# =============================================================================


@pytest.mark.network
@pytest.mark.slow
class TestDeclarationStepIncrementalBuilds:
    """Incremental build tests for DeclarationStep in non-library mode.

    DeclarationStep generates .d.ts files and should work regardless of
    whether we're building a library or an app.
    """

    @pytest.fixture
    def declaration_build_setup(self, tmp_path: Path) -> ServerBuildSetup:
        """Set up files for testing DeclarationStep."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Create entry point with exported types (for declaration generation)
        entry_point = tmp_path / "main.tsx"
        entry_point.write_text(
            """\
import React from "react";
import "@trellis/_registry";
export interface AppProps { title: string; }
export const App = (props: AppProps) => <div>{props.title}</div>;
"""
        )

        # Create minimal template
        template_path = tmp_path / "index.html.j2"
        template_path.write_text(
            """\
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body><script src="{{ static_path }}/bundle.js" type="module"></script></body>
</html>
"""
        )

        # Create static dir with test file
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        static_file = static_dir / "test.txt"
        static_file.write_text("test content")

        # Registry with packages (including dts-bundle-generator for DeclarationStep)
        # Note: @types/react and @types/react-dom are required for dts-bundle-generator
        # to produce type declarations for TSX files that import React
        registry = ModuleRegistry()
        registry.register(
            "core",
            packages={
                "react": "18.2.0",
                "react-dom": "18.2.0",
                "@types/react": "18.3.23",
                "@types/react-dom": "18.3.7",
                "typescript": "5.3.3",
                "dts-bundle-generator": "9.5.1",
            },
        )

        # Steps including DeclarationStep (requires TsconfigStep)
        steps: list[BuildStep] = [
            PackageInstallStep(),
            RegistryGenerationStep(),
            TsconfigStep(),
            BundleBuildStep(output_name="bundle"),
            DeclarationStep(),
            StaticFileCopyStep(),
            IndexHtmlRenderStep(template_path, {"static_path": "/static"}),
        ]

        return ServerBuildSetup(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=steps,
            template_path=template_path,
            static_file=static_file,
            app_static_dir=static_dir,
        )

    def test_declaration_step_runs_on_initial_build(
        self, declaration_build_setup: ServerBuildSetup
    ) -> None:
        """DeclarationStep generates .d.ts file on initial build."""
        setup = declaration_build_setup
        dist_dir = setup.workspace / "dist"

        build(
            registry=setup.registry,
            entry_point=setup.entry_point,
            workspace=setup.workspace,
            steps=setup.steps,
            app_static_dir=setup.app_static_dir,
            force=True,
        )

        # Verify declaration file was created
        dts_file = dist_dir / "main.d.ts"
        assert dts_file.exists(), "DeclarationStep should generate main.d.ts"

    def test_declaration_step_skips_when_unchanged(
        self, declaration_build_setup: ServerBuildSetup
    ) -> None:
        """DeclarationStep skips when source files are unchanged."""
        setup = declaration_build_setup
        dist_dir = setup.workspace / "dist"

        # Initial build
        build(
            registry=setup.registry,
            entry_point=setup.entry_point,
            workspace=setup.workspace,
            steps=setup.steps,
            app_static_dir=setup.app_static_dir,
            force=True,
        )

        before = record_step_states(setup.steps, setup.workspace, dist_dir)

        # Second build with no changes
        build(
            registry=setup.registry,
            entry_point=setup.entry_point,
            workspace=setup.workspace,
            steps=setup.steps,
            app_static_dir=setup.app_static_dir,
            force=False,
        )

        after = record_step_states(setup.steps, setup.workspace, dist_dir)
        ran = detect_steps_that_ran(before, after)

        assert "declaration" not in ran, "DeclarationStep should skip when unchanged"

    def test_declaration_step_rebuilds_when_source_touched(
        self, declaration_build_setup: ServerBuildSetup
    ) -> None:
        """DeclarationStep rebuilds when source file is modified."""
        setup = declaration_build_setup
        dist_dir = setup.workspace / "dist"

        # Initial build
        build(
            registry=setup.registry,
            entry_point=setup.entry_point,
            workspace=setup.workspace,
            steps=setup.steps,
            app_static_dir=setup.app_static_dir,
            force=True,
        )

        before = record_step_states(setup.steps, setup.workspace, dist_dir)

        # Touch entry point (a TypeScript source file)
        time.sleep(0.01)
        setup.entry_point.touch()

        # Incremental build
        build(
            registry=setup.registry,
            entry_point=setup.entry_point,
            workspace=setup.workspace,
            steps=setup.steps,
            app_static_dir=setup.app_static_dir,
            force=False,
        )

        after = record_step_states(setup.steps, setup.workspace, dist_dir)
        ran = detect_steps_that_ran(before, after)

        assert "declaration" in ran, "DeclarationStep should rebuild when source touched"
