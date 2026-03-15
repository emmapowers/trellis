from __future__ import annotations

import tomllib
from pathlib import Path


def _load_pyproject() -> dict[str, object]:
    repo_root = Path(__file__).resolve().parents[3]
    with (repo_root / "pyproject.toml").open("rb") as f:
        return tomllib.load(f)


def test_desktop_runtime_is_in_base_dependencies() -> None:
    pyproject = _load_pyproject()
    project = pyproject["project"]
    dependencies = project["dependencies"]

    assert "pytauri>=0.8.0; sys_platform != 'emscripten'" in dependencies
    assert "pytauri-wheel>=0.8.0; sys_platform != 'emscripten'" not in dependencies
    assert "pydantic>=2.12; sys_platform != 'emscripten'" in dependencies
    assert "optional-dependencies" not in project


def test_dev_dependencies_do_not_reference_desktop_extra() -> None:
    pyproject = _load_pyproject()
    dev_dependencies = pyproject["dependency-groups"]["dev"]

    assert "trellis[desktop]" not in dev_dependencies
    assert "trellis" not in dev_dependencies
