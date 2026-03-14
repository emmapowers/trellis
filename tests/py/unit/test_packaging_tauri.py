"""Tests for Tauri packaging pipeline."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from trellis.app.config import Config
from trellis.packaging.tauri import (
    _LINUX_REQUIRED_LIBS,
    _check_linux_system_deps,
    _check_macos_dev_tools,
    _generate_cargo_config,
    _parse_window_size,
    _tauri_bundles,
    build_desktop_app_bundle,
    generate_tauri_scaffold,
    install_app_into_portable_python,
    run_tauri_build,
)
from trellis.packaging.toolchain.rustup import RustToolchain
from trellis.platforms.common.base import PlatformType


def _make_rust_toolchain(tmp_path: Path) -> RustToolchain:
    """Create a minimal RustToolchain for testing."""
    cargo_home = tmp_path / "cargo"
    rustup_home = tmp_path / "rustup"
    cargo_bin = cargo_home / "bin"
    cargo_bin.mkdir(parents=True)
    rustc = cargo_bin / "rustc"
    rustc.write_text("fake")
    cargo = cargo_bin / "cargo"
    cargo.write_text("fake")
    return RustToolchain(
        cargo_home=cargo_home,
        rustup_home=rustup_home,
        cargo_bin=cargo,
        rustc_bin=rustc,
    )


class TestGenerateTauriScaffold:
    """Tests for generate_tauri_scaffold function."""

    def test_creates_expected_directory_structure(self, tmp_path: Path) -> None:
        config = Config(
            name="myapp",
            module="myapp.main",
            platform=PlatformType.DESKTOP,
            identifier="com.example.myapp",
            version="1.0.0",
        )
        scaffold_dir = tmp_path / "src-tauri"
        dist_path = tmp_path / "dist"
        dist_path.mkdir()

        generate_tauri_scaffold(scaffold_dir=scaffold_dir, config=config, dist_path=dist_path)

        assert (scaffold_dir / "Cargo.toml").exists()
        assert (scaffold_dir / "tauri.conf.json").exists()
        assert (scaffold_dir / "src" / "main.rs").exists()
        assert (scaffold_dir / "src" / "lib.rs").exists()
        assert (scaffold_dir / "build.rs").exists()
        assert (scaffold_dir / "capabilities" / "default.json").exists()

    def test_config_values_interpolated(self, tmp_path: Path) -> None:
        config = Config(
            name="myapp",
            module="myapp.main",
            platform=PlatformType.DESKTOP,
            identifier="com.example.myapp",
            version="2.0.0",
        )
        scaffold_dir = tmp_path / "src-tauri"
        dist_path = tmp_path / "dist"
        dist_path.mkdir()

        generate_tauri_scaffold(scaffold_dir=scaffold_dir, config=config, dist_path=dist_path)

        cargo_toml = (scaffold_dir / "Cargo.toml").read_text()
        assert 'name = "myapp"' in cargo_toml
        assert 'version = "2.0.0"' in cargo_toml

        tauri_conf = json.loads((scaffold_dir / "tauri.conf.json").read_text())
        assert tauri_conf["productName"] == "myapp"
        assert tauri_conf["version"] == "2.0.0"
        assert tauri_conf["identifier"] == "com.example.myapp"

        main_rs = (scaffold_dir / "src" / "main.rs").read_text()
        assert "TRELLIS_APP_ROOT" in main_rs
        assert "standalone_entry" in main_rs

    def test_updater_config_included_when_update_url_set(self, tmp_path: Path) -> None:
        config = Config(
            name="myapp",
            module="main",
            platform=PlatformType.DESKTOP,
            identifier="com.example.myapp",
            version="1.0.0",
            update_url="https://updates.example.com",
            update_pubkey="pubkey123",
        )
        scaffold_dir = tmp_path / "src-tauri"
        dist_path = tmp_path / "dist"
        dist_path.mkdir()

        generate_tauri_scaffold(scaffold_dir=scaffold_dir, config=config, dist_path=dist_path)

        tauri_conf = json.loads((scaffold_dir / "tauri.conf.json").read_text())
        assert "plugins" in tauri_conf
        assert tauri_conf["plugins"]["updater"]["endpoints"] == ["https://updates.example.com"]
        assert tauri_conf["plugins"]["updater"]["pubkey"] == "pubkey123"

        cargo_toml = (scaffold_dir / "Cargo.toml").read_text()
        assert "tauri-plugin-updater" in cargo_toml

    def test_updater_config_omitted_when_no_update_url(self, tmp_path: Path) -> None:
        config = Config(
            name="myapp",
            module="main",
            platform=PlatformType.DESKTOP,
            identifier="com.example.myapp",
            version="1.0.0",
        )
        scaffold_dir = tmp_path / "src-tauri"
        dist_path = tmp_path / "dist"
        dist_path.mkdir()

        generate_tauri_scaffold(scaffold_dir=scaffold_dir, config=config, dist_path=dist_path)

        tauri_conf = json.loads((scaffold_dir / "tauri.conf.json").read_text())
        assert "plugins" not in tauri_conf

        cargo_toml = (scaffold_dir / "Cargo.toml").read_text()
        assert "tauri-plugin-updater" not in cargo_toml

    def test_bundle_resources_includes_pyembed(self, tmp_path: Path) -> None:
        config = Config(
            name="myapp",
            module="main",
            platform=PlatformType.DESKTOP,
            identifier="com.example.myapp",
            version="1.0.0",
        )
        scaffold_dir = tmp_path / "src-tauri"
        dist_path = tmp_path / "dist"
        dist_path.mkdir()

        generate_tauri_scaffold(scaffold_dir=scaffold_dir, config=config, dist_path=dist_path)

        tauri_conf = json.loads((scaffold_dir / "tauri.conf.json").read_text())
        assert "bundle" in tauri_conf
        assert "resources" in tauri_conf["bundle"]
        assert "pyembed/" in tauri_conf["bundle"]["resources"]

    def test_bundle_icon_paths_configured(self, tmp_path: Path) -> None:
        config = Config(
            name="myapp",
            module="main",
            platform=PlatformType.DESKTOP,
        )
        scaffold_dir = tmp_path / "src-tauri"
        dist_path = tmp_path / "dist"
        dist_path.mkdir()

        generate_tauri_scaffold(scaffold_dir=scaffold_dir, config=config, dist_path=dist_path)

        tauri_conf = json.loads((scaffold_dir / "tauri.conf.json").read_text())
        assert "icon" in tauri_conf["bundle"]
        icon_list = tauri_conf["bundle"]["icon"]
        # Only icons that actually exist should be listed
        assert "icons/icon.png" in icon_list
        for icon in icon_list:
            assert (scaffold_dir / icon).exists()
        assert "icons/icon.png" in icon_list

    def test_defaults_identifier_and_version(self, tmp_path: Path) -> None:
        config = Config(
            name="myapp",
            module="main",
            platform=PlatformType.DESKTOP,
        )
        scaffold_dir = tmp_path / "src-tauri"
        dist_path = tmp_path / "dist"
        dist_path.mkdir()

        generate_tauri_scaffold(scaffold_dir=scaffold_dir, config=config, dist_path=dist_path)

        tauri_conf = json.loads((scaffold_dir / "tauri.conf.json").read_text())
        assert tauri_conf["identifier"] == "com.trellis.myapp"
        assert tauri_conf["version"] == "0.1.0"


class TestScaffoldIcons:
    """Tests for icon handling in generate_tauri_scaffold."""

    def test_copies_bundler_icons_from_dist_path(self, tmp_path: Path) -> None:
        config = Config(
            name="myapp",
            module="main",
            platform=PlatformType.DESKTOP,
        )
        scaffold_dir = tmp_path / "src-tauri"
        dist_path = tmp_path / "dist"
        dist_path.mkdir()

        # Simulate bundler output
        Image.new("RGBA", (32, 32), "red").save(str(dist_path / "favicon.ico"), "ICO")
        Image.new("RGBA", (32, 32), "red").save(str(dist_path / "favicon.png"), "PNG")

        generate_tauri_scaffold(scaffold_dir=scaffold_dir, config=config, dist_path=dist_path)

        icons_dir = scaffold_dir / "icons"
        assert (icons_dir / "icon.ico").exists()
        assert (icons_dir / "icon.png").exists()

    def test_copies_icns_when_present(self, tmp_path: Path) -> None:
        config = Config(
            name="myapp",
            module="main",
            platform=PlatformType.DESKTOP,
        )
        scaffold_dir = tmp_path / "src-tauri"
        dist_path = tmp_path / "dist"
        dist_path.mkdir()

        # favicon.icns is just a binary file for Tauri's purposes
        (dist_path / "favicon.icns").write_bytes(b"fake icns data")

        generate_tauri_scaffold(scaffold_dir=scaffold_dir, config=config, dist_path=dist_path)

        assert (scaffold_dir / "icons" / "icon.icns").exists()
        assert (scaffold_dir / "icons" / "icon.icns").read_bytes() == b"fake icns data"

    def test_generates_full_size_png_from_source_icon(self, tmp_path: Path) -> None:
        icon_src = tmp_path / "my-icon.png"
        Image.new("RGBA", (1024, 1024), "blue").save(str(icon_src), "PNG")

        config = Config(
            name="myapp",
            module="main",
            platform=PlatformType.DESKTOP,
            icon=icon_src,
        )
        scaffold_dir = tmp_path / "src-tauri"
        dist_path = tmp_path / "dist"
        dist_path.mkdir()

        generate_tauri_scaffold(scaffold_dir=scaffold_dir, config=config, dist_path=dist_path)

        icon_png = scaffold_dir / "icons" / "icon.png"
        assert icon_png.exists()
        img = Image.open(icon_png)
        assert img.size == (512, 512)

    def test_falls_back_to_default_icon_when_no_icons(self, tmp_path: Path) -> None:
        config = Config(
            name="myapp",
            module="main",
            platform=PlatformType.DESKTOP,
        )
        scaffold_dir = tmp_path / "src-tauri"
        dist_path = tmp_path / "dist"
        dist_path.mkdir()
        # No bundler icons in dist_path, no config.icon

        generate_tauri_scaffold(scaffold_dir=scaffold_dir, config=config, dist_path=dist_path)

        icon_png = scaffold_dir / "icons" / "icon.png"
        assert icon_png.exists()
        img = Image.open(icon_png)
        assert img.size == (512, 512)


class TestInstallAppIntoPortablePython:
    """Tests for install_app_into_portable_python function."""

    def test_calls_pip_install(self, tmp_path: Path) -> None:
        standalone_base = tmp_path / "python-install"
        standalone_base.mkdir()
        bin_dir = standalone_base / "bin"
        bin_dir.mkdir()
        (bin_dir / "python3").write_text("fake")
        app_root = tmp_path / "app"
        app_root.mkdir()
        pyembed_dir = tmp_path / "pyembed"

        with (
            patch("subprocess.run") as mock_run,
            patch("trellis.packaging.tauri.sys") as mock_sys,
        ):
            mock_sys.platform = "darwin"
            install_app_into_portable_python(
                standalone_base=standalone_base, app_root=app_root, pyembed_dir=pyembed_dir
            )

        cmd = mock_run.call_args_list[0][0][0]
        # pip runs against the copy in pyembed_dir, not the original
        assert str(pyembed_dir / "bin" / "python3") in cmd
        assert "-m" in cmd
        assert "pip" in cmd
        assert "install" in cmd
        assert str(app_root) in cmd

    def test_only_runs_pip_install(self, tmp_path: Path) -> None:
        standalone_base = tmp_path / "python-install"
        standalone_base.mkdir()
        bin_dir = standalone_base / "bin"
        bin_dir.mkdir()
        (bin_dir / "python3").write_text("fake")
        app_root = tmp_path / "app"
        app_root.mkdir()
        pyembed_dir = tmp_path / "pyembed"

        with (
            patch("subprocess.run") as mock_run,
            patch("trellis.packaging.tauri.sys") as mock_sys,
        ):
            mock_sys.platform = "darwin"
            install_app_into_portable_python(
                standalone_base=standalone_base, app_root=app_root, pyembed_dir=pyembed_dir
            )

        assert mock_run.call_count == 1
        install_cmd = mock_run.call_args_list[0][0][0]
        assert install_cmd[:5] == [
            str(pyembed_dir / "bin" / "python3"),
            "-m",
            "pip",
            "install",
            "--no-warn-script-location",
        ]

    def test_copies_trellis_config_to_pyembed(self, tmp_path: Path) -> None:
        standalone_base = tmp_path / "python-install"
        standalone_base.mkdir()
        bin_dir = standalone_base / "bin"
        bin_dir.mkdir()
        (bin_dir / "python3").write_text("fake")
        app_root = tmp_path / "app"
        app_root.mkdir()
        (app_root / "trellis_config.py").write_text("config = 'test'")
        pyembed_dir = tmp_path / "pyembed"

        with (
            patch("subprocess.run"),
            patch("trellis.packaging.tauri.sys") as mock_sys,
        ):
            mock_sys.platform = "darwin"
            install_app_into_portable_python(
                standalone_base=standalone_base, app_root=app_root, pyembed_dir=pyembed_dir
            )

        assert (pyembed_dir / "trellis_config.py").exists()
        assert (pyembed_dir / "trellis_config.py").read_text() == "config = 'test'"


class TestParseWindowSize:
    """Tests for _parse_window_size."""

    def test_explicit_dimensions(self) -> None:
        assert _parse_window_size("800x600") == (800, 600, False)

    def test_maximized(self) -> None:
        width, height, maximized = _parse_window_size("maximized")
        assert maximized is True
        assert width == 1024
        assert height == 768


class TestTauriBundles:
    """Tests for _tauri_bundles bundle type resolution."""

    @pytest.mark.parametrize(
        ("platform", "installer", "expected"),
        [
            ("darwin", False, ["app"]),
            ("darwin", True, ["dmg"]),
            ("linux", False, ["appimage"]),
            ("linux", True, ["deb"]),
            ("win32", False, []),
            ("win32", True, []),
        ],
    )
    def test_bundle_types(self, platform: str, installer: bool, expected: list[str]) -> None:
        assert _tauri_bundles(installer=installer, platform=platform) == expected

    def test_explicit_bundles_override_defaults(self) -> None:
        assert _tauri_bundles(installer=False, platform="linux", bundles=["rpm"]) == ["rpm"]


class TestRunTauriBuild:
    """Tests for run_tauri_build function."""

    def test_passes_env_and_cwd(self, tmp_path: Path) -> None:
        tauri_cli = tmp_path / "cargo-tauri"
        tauri_cli.write_text("fake")
        rust = _make_rust_toolchain(tmp_path)
        scaffold_dir = tmp_path / "scaffold"
        scaffold_dir.mkdir()
        pyembed_dir = tmp_path / "pyembed"
        pyembed_dir.mkdir()
        (pyembed_dir / "lib").mkdir()

        with (
            patch("subprocess.run") as mock_run,
            patch("trellis.packaging.tauri.sys") as mock_sys,
        ):
            mock_sys.platform = "darwin"
            run_tauri_build(
                tauri_cli=tauri_cli,
                rust=rust,
                scaffold_dir=scaffold_dir,
                pyembed_dir=pyembed_dir,
                product_name="myapp",
            )

        kwargs = mock_run.call_args[1]
        assert kwargs["cwd"] == scaffold_dir
        assert kwargs["env"]["PYTAURI_STANDALONE"] == "1"
        assert "CARGO_HOME" in kwargs["env"]
        assert "RUSTUP_HOME" in kwargs["env"]

    def test_win32_uses_no_bundle(self, tmp_path: Path) -> None:
        tauri_cli = tmp_path / "cargo-tauri"
        tauri_cli.write_text("fake")
        rust = _make_rust_toolchain(tmp_path)
        scaffold_dir = tmp_path / "scaffold"
        scaffold_dir.mkdir()
        pyembed_dir = tmp_path / "pyembed"
        pyembed_dir.mkdir()
        (pyembed_dir / "lib").mkdir()

        with (
            patch("subprocess.run") as mock_run,
            patch("trellis.packaging.tauri.sys") as mock_sys,
        ):
            mock_sys.platform = "win32"
            run_tauri_build(
                tauri_cli=tauri_cli,
                rust=rust,
                scaffold_dir=scaffold_dir,
                pyembed_dir=pyembed_dir,
                product_name="myapp",
            )

        cmd = mock_run.call_args[0][0]
        assert cmd == [str(tauri_cli), "build", "--no-bundle"]

    @pytest.mark.parametrize(
        ("platform", "installer", "expected_bundle"),
        [
            ("darwin", False, "app"),
            ("darwin", True, "dmg"),
            ("linux", False, "appimage"),
            ("linux", True, "deb"),
        ],
    )
    def test_passes_correct_bundle_to_tauri(
        self, tmp_path: Path, platform: str, installer: bool, expected_bundle: str
    ) -> None:
        tauri_cli = tmp_path / "cargo-tauri"
        tauri_cli.write_text("fake")
        rust = _make_rust_toolchain(tmp_path)
        scaffold_dir = tmp_path / "scaffold"
        scaffold_dir.mkdir()
        pyembed_dir = tmp_path / "pyembed"
        pyembed_dir.mkdir()
        (pyembed_dir / "lib").mkdir()

        with (
            patch("subprocess.run") as mock_run,
            patch("trellis.packaging.tauri.sys") as mock_sys,
        ):
            mock_sys.platform = platform
            run_tauri_build(
                tauri_cli=tauri_cli,
                rust=rust,
                scaffold_dir=scaffold_dir,
                pyembed_dir=pyembed_dir,
                product_name="myapp",
                installer=installer,
            )

        cmd = mock_run.call_args[0][0]
        assert cmd == [str(tauri_cli), "build", "--bundles", expected_bundle]


class TestBuildDesktopAppBundle:
    """Tests for the full build_desktop_app_bundle orchestration."""

    def test_calls_toolchain_functions_in_order(self, tmp_path: Path) -> None:
        config = Config(
            name="myapp",
            module="main",
            platform=PlatformType.DESKTOP,
            identifier="com.example.myapp",
            version="1.0.0",
        )
        app_root = tmp_path / "app"
        app_root.mkdir()
        dist_dir = app_root / ".dist"
        dist_dir.mkdir()

        mock_rust = _make_rust_toolchain(tmp_path)
        mock_python = MagicMock()
        mock_python.python_bin = tmp_path / "python3"
        mock_python.base_dir = tmp_path / "python-install"

        call_order: list[str] = []

        def track_rustup() -> RustToolchain:
            call_order.append("ensure_rustup")
            return mock_rust

        def track_tauri_cli(rust: RustToolchain) -> Path:
            call_order.append("ensure_tauri_cli")
            return tmp_path / "cargo-tauri"

        def track_python() -> object:
            call_order.append("ensure_python_standalone")
            return mock_python

        with (
            patch("trellis.packaging.tauri._check_macos_dev_tools"),
            patch("trellis.packaging.tauri._check_linux_system_deps"),
            patch("trellis.packaging.tauri.ensure_rustup", side_effect=track_rustup),
            patch("trellis.packaging.tauri.ensure_tauri_cli", side_effect=track_tauri_cli),
            patch("trellis.packaging.tauri.ensure_python_standalone", side_effect=track_python),
            patch("trellis.packaging.tauri.generate_tauri_scaffold"),
            patch("trellis.packaging.tauri.install_app_into_portable_python"),
            patch(
                "trellis.packaging.tauri.run_tauri_build",
                return_value=tmp_path / "output",
            ),
            # Skip Windows self-extracting exe build in unit tests
            patch("trellis.packaging.tauri.build_windows_exe", return_value=tmp_path / "out.exe"),
        ):
            build_desktop_app_bundle(config=config, app_root=app_root, output_dir=None)

        assert call_order == ["ensure_rustup", "ensure_tauri_cli", "ensure_python_standalone"]

    def test_returns_default_dist_dir(self, tmp_path: Path) -> None:
        config = Config(
            name="myapp",
            module="main",
            platform=PlatformType.DESKTOP,
            identifier="com.example.myapp",
            version="1.0.0",
        )
        app_root = tmp_path / "app"
        app_root.mkdir()
        dist_dir = app_root / ".dist"
        dist_dir.mkdir()

        bundle_dir = tmp_path / "bundle"
        bundle_dir.mkdir()
        mock_rust = _make_rust_toolchain(tmp_path)
        mock_python = MagicMock()
        mock_python.python_bin = tmp_path / "python3"
        mock_python.base_dir = tmp_path / "python-install"

        with (
            patch("trellis.packaging.tauri._check_macos_dev_tools"),
            patch("trellis.packaging.tauri._check_linux_system_deps"),
            patch("trellis.packaging.tauri.ensure_rustup", return_value=mock_rust),
            patch("trellis.packaging.tauri.ensure_tauri_cli", return_value=tmp_path / "cli"),
            patch("trellis.packaging.tauri.ensure_python_standalone", return_value=mock_python),
            patch("trellis.packaging.tauri.generate_tauri_scaffold"),
            patch("trellis.packaging.tauri.install_app_into_portable_python"),
            patch("trellis.packaging.tauri.run_tauri_build", return_value=bundle_dir),
            patch("trellis.packaging.tauri.build_windows_exe", return_value=tmp_path / "out.exe"),
        ):
            result = build_desktop_app_bundle(config=config, app_root=app_root, output_dir=None)

        assert result == app_root / "dist"


class TestOutputCopying:
    """Tests for copying build output to the destination directory."""

    def _setup_bundle(self, tmp_path: Path) -> tuple[Config, Path, MagicMock, MagicMock]:
        config = Config(
            name="myapp",
            module="main",
            platform=PlatformType.DESKTOP,
            identifier="com.example.myapp",
            version="1.0.0",
        )
        app_root = tmp_path / "app"
        app_root.mkdir()
        (app_root / ".dist").mkdir()

        mock_rust = _make_rust_toolchain(tmp_path)
        mock_python = MagicMock()
        mock_python.python_bin = tmp_path / "python3"
        mock_python.base_dir = tmp_path / "python-install"

        return config, app_root, mock_rust, mock_python

    def test_renames_app_bundle(self, tmp_path: Path) -> None:
        config, app_root, mock_rust, mock_python = self._setup_bundle(tmp_path)

        bundle_dir = tmp_path / "scaffold" / "target" / "release" / "bundle"
        macos_dir = bundle_dir / "macos"
        macos_dir.mkdir(parents=True)
        app_bundle = macos_dir / "myapp.app"
        app_bundle.mkdir()
        (app_bundle / "Contents").mkdir()
        (app_bundle / "Contents" / "Info.plist").write_text("fake")

        with (
            patch("trellis.packaging.tauri.ensure_rustup", return_value=mock_rust),
            patch("trellis.packaging.tauri.ensure_tauri_cli", return_value=tmp_path / "cli"),
            patch(
                "trellis.packaging.tauri.ensure_python_standalone",
                return_value=mock_python,
            ),
            patch("trellis.packaging.tauri.generate_tauri_scaffold"),
            patch("trellis.packaging.tauri.install_app_into_portable_python"),
            patch("trellis.packaging.tauri.run_tauri_build", return_value=bundle_dir),
            patch("trellis.packaging.tauri.sys") as mock_sys,
        ):
            mock_sys.platform = "darwin"
            result = build_desktop_app_bundle(config=config, app_root=app_root, output_dir=None)

        assert result == app_root / "dist"
        assert (result / "myapp-1.0.0.app" / "Contents" / "Info.plist").exists()

    def test_copies_app_to_custom_output_dir(self, tmp_path: Path) -> None:
        config, app_root, mock_rust, mock_python = self._setup_bundle(tmp_path)
        custom_dest = tmp_path / "custom-out"

        bundle_dir = tmp_path / "scaffold" / "target" / "release" / "bundle"
        macos_dir = bundle_dir / "macos"
        macos_dir.mkdir(parents=True)
        app_bundle = macos_dir / "myapp.app"
        app_bundle.mkdir()
        (app_bundle / "Contents").mkdir()

        with (
            patch("trellis.packaging.tauri.ensure_rustup", return_value=mock_rust),
            patch("trellis.packaging.tauri.ensure_tauri_cli", return_value=tmp_path / "cli"),
            patch(
                "trellis.packaging.tauri.ensure_python_standalone",
                return_value=mock_python,
            ),
            patch("trellis.packaging.tauri.generate_tauri_scaffold"),
            patch("trellis.packaging.tauri.install_app_into_portable_python"),
            patch("trellis.packaging.tauri.run_tauri_build", return_value=bundle_dir),
            patch("trellis.packaging.tauri.sys") as mock_sys,
        ):
            mock_sys.platform = "darwin"
            result = build_desktop_app_bundle(
                config=config, app_root=app_root, output_dir=custom_dest
            )

        assert result == custom_dest
        assert (custom_dest / "myapp-1.0.0.app").exists()

    def test_renames_dmg(self, tmp_path: Path) -> None:
        config, app_root, mock_rust, mock_python = self._setup_bundle(tmp_path)

        bundle_dir = tmp_path / "scaffold" / "target" / "release" / "bundle"
        dmg_dir = bundle_dir / "dmg"
        dmg_dir.mkdir(parents=True)
        (dmg_dir / "myapp_1.0.0_aarch64.dmg").write_text("fake dmg")

        with (
            patch("trellis.packaging.tauri.ensure_rustup", return_value=mock_rust),
            patch("trellis.packaging.tauri.ensure_tauri_cli", return_value=tmp_path / "cli"),
            patch(
                "trellis.packaging.tauri.ensure_python_standalone",
                return_value=mock_python,
            ),
            patch("trellis.packaging.tauri.generate_tauri_scaffold"),
            patch("trellis.packaging.tauri.install_app_into_portable_python"),
            patch("trellis.packaging.tauri.run_tauri_build", return_value=bundle_dir),
            patch("trellis.packaging.tauri.sys") as mock_sys,
        ):
            mock_sys.platform = "darwin"
            result = build_desktop_app_bundle(
                config=config,
                app_root=app_root,
                output_dir=None,
                installer=True,
            )

        assert (result / "myapp-1.0.0.dmg").exists()


class TestCheckMacosDevTools:
    """Tests for _check_macos_dev_tools preflight check."""

    def test_skipped_on_non_macos(self) -> None:
        with patch("trellis.packaging.tauri.sys") as mock_sys:
            mock_sys.platform = "linux"
            _check_macos_dev_tools()  # Should not raise

    def test_passes_when_xcode_tools_installed(self) -> None:
        with (
            patch("trellis.packaging.tauri.sys") as mock_sys,
            patch("trellis.packaging.tauri.subprocess.run") as mock_run,
        ):
            mock_sys.platform = "darwin"
            mock_run.return_value = MagicMock(returncode=0)
            _check_macos_dev_tools()  # Should not raise

    def test_raises_when_xcode_tools_missing(self) -> None:
        with (
            patch("trellis.packaging.tauri.sys") as mock_sys,
            patch(
                "trellis.packaging.tauri.subprocess.run",
                return_value=MagicMock(returncode=2),
            ),
        ):
            mock_sys.platform = "darwin"
            with pytest.raises(RuntimeError, match="Xcode Command Line Tools") as exc_info:
                _check_macos_dev_tools()

        assert "xcode-select --install" in str(exc_info.value)


class TestCheckLinuxSystemDeps:
    """Tests for _check_linux_system_deps preflight check."""

    def test_skipped_on_non_linux(self) -> None:
        with patch("trellis.packaging.tauri.sys") as mock_sys:
            mock_sys.platform = "darwin"
            _check_linux_system_deps()  # Should not raise

    def test_passes_when_all_libs_present(self) -> None:
        with (
            patch("trellis.packaging.tauri.sys") as mock_sys,
            patch("trellis.packaging.tauri.subprocess.run") as mock_run,
        ):
            mock_sys.platform = "linux"
            mock_run.return_value = MagicMock(returncode=0)
            _check_linux_system_deps()  # Should not raise

        assert mock_run.call_count == len(_LINUX_REQUIRED_LIBS)

    def test_raises_with_install_instructions_when_libs_missing(self) -> None:
        def fake_pkg_config(cmd: list[str], **kwargs: object) -> MagicMock:
            # Simulate libsoup-3.0 and javascriptcoregtk-4.1 missing
            pkg = cmd[2]
            missing = {"libsoup-3.0", "javascriptcoregtk-4.1"}
            return MagicMock(returncode=1 if pkg in missing else 0)

        with (
            patch("trellis.packaging.tauri.sys") as mock_sys,
            patch("trellis.packaging.tauri.subprocess.run", side_effect=fake_pkg_config),
        ):
            mock_sys.platform = "linux"
            with pytest.raises(RuntimeError, match="Missing system libraries") as exc_info:
                _check_linux_system_deps()

        msg = str(exc_info.value)
        assert "libsoup-3.0" in msg
        assert "javascriptcoregtk-4.1" in msg
        assert "sudo apt-get install" in msg
        assert "libsoup-3.0-dev" in msg
        assert "libjavascriptcoregtk-4.1-dev" in msg
        # Libraries that are present should NOT appear in the error
        assert "libgtk-3-dev" not in msg

    def test_error_includes_tauri_docs_link(self) -> None:
        with (
            patch("trellis.packaging.tauri.sys") as mock_sys,
            patch(
                "trellis.packaging.tauri.subprocess.run",
                return_value=MagicMock(returncode=1),
            ),
        ):
            mock_sys.platform = "linux"
            with pytest.raises(RuntimeError, match=r"tauri\.app") as exc_info:
                _check_linux_system_deps()

        assert "https://v2.tauri.app/start/prerequisites/#linux" in str(exc_info.value)


class TestGenerateCargoConfig:
    """Tests for _generate_cargo_config."""

    @pytest.mark.skipif(
        sys.platform == "win32" or shutil.which("pkg-config") is None,
        reason="Requires pkg-config (Linux/macOS)",
    )
    def test_generates_config_on_linux(self, tmp_path: Path) -> None:
        scaffold_dir = tmp_path / "src-tauri"
        scaffold_dir.mkdir()
        pyembed_dir = tmp_path / "pyembed"
        pyembed_dir.mkdir()
        (pyembed_dir / "lib").mkdir()

        with patch("trellis.packaging.tauri.sys") as mock_sys:
            mock_sys.platform = "linux"
            _generate_cargo_config(
                scaffold_dir=scaffold_dir,
                pyembed_dir=pyembed_dir,
                product_name="My App",
            )

        config_path = scaffold_dir / ".cargo" / "config.toml"
        assert config_path.exists()
        content = config_path.read_text()
        assert "My App" in content
        assert "$ORIGIN/../lib/My App/pyembed/lib" in content
        assert "x86_64-unknown-linux-gnu" in content
        assert "aarch64-unknown-linux-gnu" in content

    def test_generates_config_on_macos(self, tmp_path: Path) -> None:
        scaffold_dir = tmp_path / "src-tauri"
        scaffold_dir.mkdir()
        pyembed_dir = tmp_path / "pyembed"
        pyembed_dir.mkdir()
        (pyembed_dir / "lib").mkdir()

        with patch("trellis.packaging.tauri.sys") as mock_sys:
            mock_sys.platform = "darwin"
            _generate_cargo_config(
                scaffold_dir=scaffold_dir,
                pyembed_dir=pyembed_dir,
                product_name="My App",
            )

        config_path = scaffold_dir / ".cargo" / "config.toml"
        assert config_path.exists()
        content = config_path.read_text()
        assert "aarch64-apple-darwin" in content
        assert "x86_64-apple-darwin" in content
        assert "@executable_path/../Resources/pyembed/lib" in content
