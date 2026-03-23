"""Tests for SSRBundleBuildStep."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

from trellis.bundler.steps import SSRBundleBuildStep


class TestSSRBundleBuildStep:
    def test_step_name(self) -> None:
        step = SSRBundleBuildStep()
        assert step.name == "ssr-bundle-build"

    def test_uses_node_platform(self) -> None:
        step = SSRBundleBuildStep()
        ctx = MagicMock()
        ctx.workspace = MagicMock()
        ctx.dist_dir = MagicMock()
        ctx.collected = MagicMock()
        ctx.collected.modules = []
        ctx.esbuild_args = []
        ctx.manifest = MagicMock()
        ctx.manifest.steps = {}

        with (
            patch("trellis.bundler.steps.get_bin") as mock_get_bin,
            patch("trellis.bundler.steps.node_modules_path") as mock_nm,
            patch("trellis.bundler.steps.get_metafile_path") as mock_mf,
            patch("trellis.bundler.steps.read_metafile") as mock_read_mf,
        ):
            mock_get_bin.return_value = "/fake/esbuild"
            mock_nm.return_value = "/fake/node_modules"
            mock_mf.return_value = "/fake/meta.json"
            mock_read_mf.return_value = MagicMock(inputs=set(), outputs=set())

            asyncio.run(step.run(ctx))

            cmd = ctx.exec_in_build_env.call_args[0][0]
            assert "--platform=node" in cmd
            assert "--format=esm" in cmd
            assert "--target=esnext" in cmd
            # Should NOT have --platform=browser
            assert "--platform=browser" not in cmd

    def test_output_name_defaults_to_ssr(self) -> None:
        step = SSRBundleBuildStep()
        ctx = MagicMock()
        ctx.workspace = MagicMock()
        ctx.dist_dir = MagicMock()
        ctx.collected = MagicMock()
        ctx.collected.modules = []
        ctx.esbuild_args = []
        ctx.manifest = MagicMock()
        ctx.manifest.steps = {}

        with (
            patch("trellis.bundler.steps.get_bin") as mock_get_bin,
            patch("trellis.bundler.steps.node_modules_path") as mock_nm,
            patch("trellis.bundler.steps.get_metafile_path") as mock_mf,
            patch("trellis.bundler.steps.read_metafile") as mock_read_mf,
        ):
            mock_get_bin.return_value = "/fake/esbuild"
            mock_nm.return_value = "/fake/node_modules"
            mock_mf.return_value = "/fake/meta.json"
            mock_read_mf.return_value = MagicMock(inputs=set(), outputs=set())

            asyncio.run(step.run(ctx))

            cmd = ctx.exec_in_build_env.call_args[0][0]
            assert any("--entry-names=ssr" in arg for arg in cmd)
