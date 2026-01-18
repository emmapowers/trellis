"""Browser platform build steps."""

from __future__ import annotations

import subprocess
from pathlib import Path

from trellis.bundler.packages import get_bin
from trellis.bundler.steps import BuildContext, BuildStep

# Path to pyodide worker source relative to this file
_PYODIDE_WORKER_PATH = Path(__file__).parent / "client" / "src" / "pyodide.worker.ts"


class PyodideWorkerBuildStep(BuildStep):
    """Build the Pyodide worker as an IIFE bundle inlined as text.

    Builds the pyodide.worker.ts file as an IIFE bundle and adds an alias
    so the main bundle can import it as text via:

        import WORKER_CODE from "@trellis/browser/pyodide.worker-bundle";
        new Worker(URL.createObjectURL(new Blob([WORKER_CODE])));
    """

    @property
    def name(self) -> str:
        return "pyodide-worker-build"

    def run(self, ctx: BuildContext) -> None:
        if ctx.node_modules is None:
            raise RuntimeError("PyodideWorkerBuildStep requires node_modules")

        esbuild = get_bin(ctx.node_modules, "esbuild")
        output_file = ctx.workspace / "pyodide.worker-bundle"

        cmd = [
            str(esbuild),
            str(_PYODIDE_WORKER_PATH),
            "--bundle",
            f"--outfile={output_file}",
            "--format=iife",
            "--platform=browser",
            "--target=es2022",
            "--loader:.ts=ts",
        ]

        subprocess.run(cmd, check=True, env={**ctx.env})

        # Add loader and alias so the main bundle can import the worker as text
        ctx.esbuild_args.append("--loader:.worker-bundle=text")
        ctx.esbuild_args.append(f"--alias:@trellis/browser/pyodide.worker-bundle={output_file}")
