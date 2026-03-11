from __future__ import annotations

import subprocess
import sys
import tarfile
import textwrap
import zipfile
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _build_distributions(output_dir: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--sdist",
            "--outdir",
            str(output_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=_repo_root(),
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_built_distributions_ship_html_typing_artifacts(tmp_path: Path) -> None:
    _build_distributions(tmp_path)

    wheel_path = next(tmp_path.glob("trellis-*.whl"))
    sdist_path = next(tmp_path.glob("trellis-*.tar.gz"))

    with zipfile.ZipFile(wheel_path) as wheel:
        wheel_names = set(wheel.namelist())

    assert "trellis/py.typed" in wheel_names
    assert "trellis/html/__init__.pyi" in wheel_names
    assert "trellis/html/links.pyi" in wheel_names
    assert "trellis/html/_generated_runtime.pyi" in wheel_names
    assert "trellis/html/_generated_style_types.pyi" in wheel_names

    with tarfile.open(sdist_path, "r:gz") as sdist:
        sdist_names = set(sdist.getnames())

    prefix = sdist_path.name.removesuffix(".tar.gz")
    assert f"{prefix}/src/trellis/py.typed" in sdist_names
    assert f"{prefix}/src/trellis/html/__init__.pyi" in sdist_names
    assert f"{prefix}/src/trellis/html/links.pyi" in sdist_names


def test_public_html_import_surface_from_fresh_interpreter(tmp_path: Path) -> None:
    snippet = textwrap.dedent(
        """
        from trellis import html as h

        assert callable(h.Div)
        assert callable(h.A)
        assert h.StyleInput is not None
        assert callable(h.media)
        assert h.MouseEventHandler is not None
        print("ok")
        """
    )
    snippet_path = tmp_path / "verify_html_public_imports.py"
    snippet_path.write_text(snippet)

    result = subprocess.run(
        [sys.executable, str(snippet_path)],
        check=False,
        capture_output=True,
        text=True,
        cwd=_repo_root(),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "ok"
