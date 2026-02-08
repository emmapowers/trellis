"""Unit tests for wheel building, dependency resolution, and bundle creation."""

from __future__ import annotations

import logging
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
from packaging.requirements import Requirement

from trellis.bundler.wheels import (
    build_emscripten_env,
    build_wheel,
    create_site_packages_zip,
    filter_requirements,
    get_pyodide_package_names,
    get_pyodide_python_version,
    read_wheel_record,
    read_wheel_requirements,
    resolve_dependencies,
)


def _make_wheel(tmp_path: Path, name: str, version: str, requires: list[str] | None = None) -> Path:
    """Create a minimal .whl file (zip with METADATA and RECORD) in tmp_path."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    dist_info = f"{name}-{version}.dist-info"
    metadata_lines = [
        "Metadata-Version: 2.1",
        f"Name: {name}",
        f"Version: {version}",
    ]
    if requires:
        metadata_lines.extend(f"Requires-Dist: {req}" for req in requires)
    metadata_content = "\n".join(metadata_lines) + "\n"

    pkg_init = f"{name}/__init__.py"
    record_entries = [
        f"{pkg_init},sha256=abc123,42",
        f"{dist_info}/METADATA,sha256=def456,100",
        f"{dist_info}/RECORD,,",
    ]
    record_content = "\n".join(record_entries) + "\n"

    wheel_path = tmp_path / f"{name}-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel_path, "w") as zf:
        zf.writestr(f"{dist_info}/METADATA", metadata_content)
        zf.writestr(f"{dist_info}/RECORD", record_content)
        zf.writestr(pkg_init, f"# {name} package\n")
    return wheel_path


class TestReadWheelRecord:
    """Tests for read_wheel_record."""

    def test_returns_package_file_paths(self, tmp_path: Path) -> None:
        """Returns paths from RECORD excluding .dist-info entries."""
        wheel = _make_wheel(tmp_path, "mypkg", "1.0.0")

        result = read_wheel_record(wheel)

        assert result == ["mypkg/__init__.py"]

    def test_excludes_dist_info_entries(self, tmp_path: Path) -> None:
        """Entries under .dist-info/ are filtered out."""
        wheel = _make_wheel(tmp_path, "mypkg", "1.0.0")

        result = read_wheel_record(wheel)

        assert not any(".dist-info/" in p for p in result)

    def test_returns_empty_for_empty_record(self, tmp_path: Path) -> None:
        """Returns empty list when RECORD file is empty."""
        tmp_path.mkdir(parents=True, exist_ok=True)
        dist_info = "mypkg-1.0.0.dist-info"
        wheel_path = tmp_path / "mypkg-1.0.0-py3-none-any.whl"
        with zipfile.ZipFile(wheel_path, "w") as zf:
            zf.writestr(f"{dist_info}/METADATA", "Name: mypkg\nVersion: 1.0.0\n")
            zf.writestr(f"{dist_info}/RECORD", "")

        result = read_wheel_record(wheel_path)

        assert result == []

    def test_returns_empty_for_missing_record(self, tmp_path: Path) -> None:
        """Returns empty list when RECORD file is absent."""
        tmp_path.mkdir(parents=True, exist_ok=True)
        dist_info = "mypkg-1.0.0.dist-info"
        wheel_path = tmp_path / "mypkg-1.0.0-py3-none-any.whl"
        with zipfile.ZipFile(wheel_path, "w") as zf:
            zf.writestr(f"{dist_info}/METADATA", "Name: mypkg\nVersion: 1.0.0\n")

        result = read_wheel_record(wheel_path)

        assert result == []

    def test_multiple_package_files(self, tmp_path: Path) -> None:
        """Returns all non-dist-info paths from RECORD."""
        tmp_path.mkdir(parents=True, exist_ok=True)
        dist_info = "mypkg-1.0.0.dist-info"
        record_content = (
            "\n".join(
                [
                    "mypkg/__init__.py,sha256=abc,10",
                    "mypkg/core.py,sha256=def,200",
                    "mypkg/utils/__init__.py,sha256=ghi,15",
                    f"{dist_info}/METADATA,sha256=jkl,100",
                    f"{dist_info}/RECORD,,",
                ]
            )
            + "\n"
        )
        wheel_path = tmp_path / "mypkg-1.0.0-py3-none-any.whl"
        with zipfile.ZipFile(wheel_path, "w") as zf:
            zf.writestr(f"{dist_info}/METADATA", "Name: mypkg\nVersion: 1.0.0\n")
            zf.writestr(f"{dist_info}/RECORD", record_content)
            zf.writestr("mypkg/__init__.py", "")
            zf.writestr("mypkg/core.py", "")
            zf.writestr("mypkg/utils/__init__.py", "")

        result = read_wheel_record(wheel_path)

        assert sorted(result) == [
            "mypkg/__init__.py",
            "mypkg/core.py",
            "mypkg/utils/__init__.py",
        ]


class TestFilterRequirements:
    """Tests for filter_requirements."""

    def test_excludes_server_only(self) -> None:
        """Requirements with sys_platform != 'emscripten' are filtered out."""
        reqs = [Requirement("fastapi>=0.128; sys_platform != 'emscripten'")]
        env = build_emscripten_env("3.12.7")

        result = filter_requirements(reqs, env)

        assert len(result) == 0

    def test_includes_unconditional(self) -> None:
        """Requirements with no marker pass through."""
        reqs = [Requirement("rich>=13.9")]
        env = build_emscripten_env("3.12.7")

        result = filter_requirements(reqs, env)

        assert len(result) == 1
        assert result[0].name == "rich"

    def test_includes_emscripten_specific(self) -> None:
        """Requirements targeting emscripten are included."""
        reqs = [Requirement("special-pkg>=1.0; sys_platform == 'emscripten'")]
        env = build_emscripten_env("3.12.7")

        result = filter_requirements(reqs, env)

        assert len(result) == 1
        assert result[0].name == "special-pkg"

    def test_excludes_non_emscripten_platform(self) -> None:
        """Requirements targeting non-emscripten platforms are excluded."""
        reqs = [Requirement("win-only>=1.0; sys_platform == 'win32'")]
        env = build_emscripten_env("3.12.7")

        result = filter_requirements(reqs, env)

        assert len(result) == 0


class TestReadWheelRequirements:
    """Tests for read_wheel_requirements."""

    def test_reads_requirements(self, tmp_path: Path) -> None:
        """Reads Requires-Dist from wheel METADATA."""
        wheel = _make_wheel(tmp_path, "mypkg", "1.0.0", requires=["dep-a>=1.0", "dep-b"])

        result = read_wheel_requirements(wheel)

        assert len(result) == 2
        assert "dep-a>=1.0" in result
        assert "dep-b" in result

    def test_empty_requirements(self, tmp_path: Path) -> None:
        """Wheel with no Requires-Dist returns empty list."""
        wheel = _make_wheel(tmp_path, "mypkg", "1.0.0")

        result = read_wheel_requirements(wheel)

        assert result == []


class TestGetPyodidePackageNames:
    """Tests for get_pyodide_package_names."""

    def test_extracts_package_names(self) -> None:
        """Extracts package names from lockfile packages key."""
        lockfile = {
            "info": {"python": "3.12.7", "version": "0.29.0"},
            "packages": {
                "numpy": {"version": "1.26.4"},
                "micropip": {"version": "0.5.0"},
                "scipy": {"version": "1.12.0"},
            },
        }

        result = get_pyodide_package_names(lockfile)

        assert result == {"numpy", "micropip", "scipy"}

    def test_empty_packages(self) -> None:
        """Empty packages dict returns empty set."""
        lockfile = {"info": {"python": "3.12.7", "version": "0.29.0"}, "packages": {}}

        result = get_pyodide_package_names(lockfile)

        assert result == set()


class TestGetPyodidePythonVersion:
    """Tests for get_pyodide_python_version."""

    def test_extracts_version(self) -> None:
        """Extracts Python version from lockfile info.python field."""
        lockfile = {"info": {"python": "3.12.7", "version": "0.29.0"}}

        result = get_pyodide_python_version(lockfile)

        assert result == "3.12.7"


class TestBuildEmscriptenEnv:
    """Tests for build_emscripten_env."""

    def test_uses_lockfile_version(self) -> None:
        """Environment dict uses the provided Python version."""
        env = build_emscripten_env("3.12.7")

        assert env["python_version"] == "3.12"
        assert env["python_full_version"] == "3.12.7"
        assert env["sys_platform"] == "emscripten"
        assert env["platform_system"] == "Emscripten"
        assert env["platform_machine"] == "wasm32"
        assert env["implementation_name"] == "cpython"
        assert env["os_name"] == "posix"

    def test_different_version(self) -> None:
        """Works with different Python versions."""
        env = build_emscripten_env("3.13.1")

        assert env["python_version"] == "3.13"
        assert env["python_full_version"] == "3.13.1"


class TestResolve:
    """Tests for resolve_dependencies."""

    def _make_lockfile(self, packages: dict[str, dict[str, str]] | None = None) -> dict:
        return {
            "info": {"python": "3.12.7", "version": "0.29.0"},
            "packages": packages or {},
        }

    def test_classifies_pyodide_builtin(self, tmp_path: Path) -> None:
        """Package in Pyodide lockfile goes to pyodide_packages."""
        lockfile = self._make_lockfile({"numpy": {"version": "1.26.4"}})
        app_wheel = _make_wheel(tmp_path, "myapp", "0.1.0", requires=["numpy>=1.0"])

        with (patch("trellis.bundler.wheels.fetch_pyodide_lockfile", return_value=lockfile),):
            result = resolve_dependencies(app_wheel, tmp_path / "cache")

        assert "numpy" in result.pyodide_packages
        assert not any("numpy" in str(p) for p in result.wheel_paths)

    def test_downloads_pure_python_dep(self, tmp_path: Path) -> None:
        """Pure Python dep not in Pyodide gets downloaded as wheel."""
        lockfile = self._make_lockfile()
        app_wheel = _make_wheel(tmp_path, "myapp", "0.1.0", requires=["click>=8.0"])
        downloaded_wheel = _make_wheel(tmp_path / "downloads", "click", "8.1.0")

        def fake_download(req, python_version, cache_dir):
            return downloaded_wheel

        with (
            patch("trellis.bundler.wheels.fetch_pyodide_lockfile", return_value=lockfile),
            patch("trellis.bundler.wheels._download_wheel", side_effect=fake_download),
        ):
            result = resolve_dependencies(app_wheel, tmp_path / "cache")

        assert downloaded_wheel in result.wheel_paths
        assert "click" not in result.pyodide_packages

    def test_handles_direct_reference(self, tmp_path: Path) -> None:
        """Package with @ file:// URL triggers build_wheel."""
        lockfile = self._make_lockfile()
        lib_dir = tmp_path / "mylib"
        lib_dir.mkdir()
        built_wheel = _make_wheel(tmp_path / "built", "mylib", "0.1.0")

        app_wheel = _make_wheel(
            tmp_path,
            "myapp",
            "0.1.0",
            requires=[f"mylib @ file://{lib_dir}"],
        )

        with (
            patch("trellis.bundler.wheels.fetch_pyodide_lockfile", return_value=lockfile),
            patch("trellis.bundler.wheels.build_wheel", return_value=built_wheel),
        ):
            result = resolve_dependencies(app_wheel, tmp_path / "cache")

        assert built_wheel in result.wheel_paths

    def test_raises_for_unavailable(self, tmp_path: Path) -> None:
        """Package not in Pyodide and pip fails raises clear error."""
        lockfile = self._make_lockfile()
        app_wheel = _make_wheel(tmp_path, "myapp", "0.1.0", requires=["native-pkg>=1.0"])

        def fail_download(req, python_version, cache_dir):
            raise RuntimeError("No matching distribution found for native-pkg")

        with (
            patch("trellis.bundler.wheels.fetch_pyodide_lockfile", return_value=lockfile),
            patch("trellis.bundler.wheels._download_wheel", side_effect=fail_download),
        ):
            with pytest.raises(RuntimeError, match="native-pkg"):
                resolve_dependencies(app_wheel, tmp_path / "cache")

    def test_app_wheel_included_in_result(self, tmp_path: Path) -> None:
        """The app wheel itself is included in wheel_paths."""
        lockfile = self._make_lockfile()
        app_wheel = _make_wheel(tmp_path, "myapp", "0.1.0")

        with patch("trellis.bundler.wheels.fetch_pyodide_lockfile", return_value=lockfile):
            result = resolve_dependencies(app_wheel, tmp_path / "cache")

        assert app_wheel in result.wheel_paths


class TestCreateSitePackagesZip:
    """Tests for create_site_packages_zip."""

    def test_creates_zip_with_extracted_contents(self, tmp_path: Path) -> None:
        """Wheel files are pre-extracted into flat zip for unpackArchive."""
        wheel1 = _make_wheel(tmp_path / "wheels", "pkg_a", "1.0.0")
        wheel2 = _make_wheel(tmp_path / "wheels", "pkg_b", "2.0.0")

        output = tmp_path / "site-packages.zip"
        create_site_packages_zip([wheel1, wheel2], output)

        assert output.exists()

        with zipfile.ZipFile(output) as zf:
            names = zf.namelist()
            # Should contain pre-extracted package dirs and dist-info
            assert "pkg_a/__init__.py" in names
            assert "pkg_b/__init__.py" in names
            assert "pkg_a-1.0.0.dist-info/METADATA" in names
            assert "pkg_b-2.0.0.dist-info/METADATA" in names

    def test_empty_wheel_list(self, tmp_path: Path) -> None:
        """Empty wheel list creates empty zip."""
        output = tmp_path / "site-packages.zip"
        create_site_packages_zip([], output)

        assert output.exists()
        with zipfile.ZipFile(output) as zf:
            assert zf.namelist() == []


class TestBuildWheel:
    """Tests for build_wheel."""

    def test_raises_for_missing_pyproject(self, tmp_path: Path) -> None:
        """Raises FileNotFoundError when pyproject.toml is missing."""
        project_dir = tmp_path / "no-project"
        project_dir.mkdir()
        output_dir = tmp_path / "output"

        with pytest.raises(FileNotFoundError, match=r"No pyproject\.toml found"):
            build_wheel(project_dir, output_dir)


class TestVersionWarning:
    """Tests for Python version mismatch warnings."""

    def test_minor_version_mismatch_warns(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Minor version mismatch between host and Pyodide triggers warning."""
        lockfile = {
            "info": {"python": "3.12.7", "version": "0.29.0"},
            "packages": {},
        }
        app_wheel = _make_wheel(tmp_path, "myapp", "0.1.0")

        with (
            patch("trellis.bundler.wheels.fetch_pyodide_lockfile", return_value=lockfile),
            patch("trellis.bundler.wheels._get_host_python_version", return_value="3.13.1"),
            caplog.at_level(logging.WARNING),
        ):
            resolve_dependencies(app_wheel, tmp_path / "cache")

        assert any(
            "3.12" in record.message and "3.13" in record.message for record in caplog.records
        )

    def test_patch_version_mismatch_no_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Patch version mismatch does not trigger warning."""
        lockfile = {
            "info": {"python": "3.12.7", "version": "0.29.0"},
            "packages": {},
        }
        app_wheel = _make_wheel(tmp_path, "myapp", "0.1.0")

        with (
            patch("trellis.bundler.wheels.fetch_pyodide_lockfile", return_value=lockfile),
            patch("trellis.bundler.wheels._get_host_python_version", return_value="3.12.1"),
            caplog.at_level(logging.WARNING),
        ):
            resolve_dependencies(app_wheel, tmp_path / "cache")

        warning_records = [r for r in caplog.records if r.levelno >= logging.WARNING]
        assert not any("version" in r.message.lower() for r in warning_records)
