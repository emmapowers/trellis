"""Tests for Tauri packaging pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image

from trellis.app.config import Config
from trellis.packaging.tauri import (
    build_desktop_app_bundle,
    generate_tauri_scaffold,
    install_app_into_portable_python,
    run_tauri_build,
)
from trellis.platforms.common.base import PlatformType
from trellis.toolchain.rustup import RustToolchain


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
        assert "myapp.main" in main_rs

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
        assert "icons/icon.icns" in icon_list
        assert "icons/icon.ico" in icon_list
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
        python_bin = tmp_path / "python" / "install" / "bin" / "python3"
        python_bin.parent.mkdir(parents=True)
        python_bin.write_text("fake")
        app_root = tmp_path / "app"
        app_root.mkdir()
        pyembed_dir = tmp_path / "pyembed"

        with (
            patch("subprocess.run") as mock_run,
            patch("trellis.packaging.tauri.shutil.copytree"),
        ):
            install_app_into_portable_python(
                python_bin=python_bin, app_root=app_root, pyembed_dir=pyembed_dir
            )

        cmd = mock_run.call_args[0][0]
        assert str(python_bin) in cmd
        assert "-m" in cmd
        assert "pip" in cmd
        assert "install" in cmd
        assert str(app_root) in cmd


class TestRunTauriBuild:
    """Tests for run_tauri_build function."""

    def test_calls_tauri_build_with_correct_args(self, tmp_path: Path) -> None:
        tauri_cli = tmp_path / "cargo-tauri"
        tauri_cli.write_text("fake")
        rust = _make_rust_toolchain(tmp_path)
        scaffold_dir = tmp_path / "scaffold"
        scaffold_dir.mkdir()
        pyembed_dir = tmp_path / "pyembed"
        pyembed_dir.mkdir()
        (pyembed_dir / "lib").mkdir()

        with patch("subprocess.run") as mock_run:
            run_tauri_build(
                tauri_cli=tauri_cli,
                rust=rust,
                scaffold_dir=scaffold_dir,
                pyembed_dir=pyembed_dir,
            )

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert str(tauri_cli) in cmd
        assert "build" in cmd
        assert "--bundles" in cmd
        assert "app" in cmd

        kwargs = mock_run.call_args[1]
        assert kwargs["cwd"] == scaffold_dir
        assert "PYTAURI_STANDALONE" in kwargs["env"]
        assert kwargs["env"]["PYTAURI_STANDALONE"] == "1"
        assert "CARGO_HOME" in kwargs["env"]
        assert "RUSTUP_HOME" in kwargs["env"]

    def test_bundles_parameter_changes_subprocess_args(self, tmp_path: Path) -> None:
        tauri_cli = tmp_path / "cargo-tauri"
        tauri_cli.write_text("fake")
        rust = _make_rust_toolchain(tmp_path)
        scaffold_dir = tmp_path / "scaffold"
        scaffold_dir.mkdir()
        pyembed_dir = tmp_path / "pyembed"
        pyembed_dir.mkdir()
        (pyembed_dir / "lib").mkdir()

        with patch("subprocess.run") as mock_run:
            run_tauri_build(
                tauri_cli=tauri_cli,
                rust=rust,
                scaffold_dir=scaffold_dir,
                pyembed_dir=pyembed_dir,
                bundles=["app", "dmg"],
            )

        cmd = mock_run.call_args[0][0]
        assert cmd == [str(tauri_cli), "build", "--bundles", "app", "dmg"]


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
            patch("trellis.packaging.tauri.ensure_rustup", side_effect=track_rustup),
            patch("trellis.packaging.tauri.ensure_tauri_cli", side_effect=track_tauri_cli),
            patch("trellis.packaging.tauri.ensure_python_standalone", side_effect=track_python),
            patch("trellis.packaging.tauri.generate_tauri_scaffold"),
            patch("trellis.packaging.tauri.install_app_into_portable_python"),
            patch("trellis.packaging.tauri.run_tauri_build", return_value=tmp_path / "output"),
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
            patch("trellis.packaging.tauri.ensure_rustup", return_value=mock_rust),
            patch("trellis.packaging.tauri.ensure_tauri_cli", return_value=tmp_path / "cli"),
            patch("trellis.packaging.tauri.ensure_python_standalone", return_value=mock_python),
            patch("trellis.packaging.tauri.generate_tauri_scaffold"),
            patch("trellis.packaging.tauri.install_app_into_portable_python"),
            patch("trellis.packaging.tauri.run_tauri_build", return_value=bundle_dir),
        ):
            result = build_desktop_app_bundle(config=config, app_root=app_root, output_dir=None)

        assert result == app_root / "dist"


class TestOutputCopying:
    """Tests for copying build output to the destination directory."""

    def _setup_bundle(self, tmp_path: Path) -> tuple[Config, Path, MagicMock]:
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

    def test_copies_app_to_default_dist(self, tmp_path: Path) -> None:
        config, app_root, mock_rust, mock_python = self._setup_bundle(tmp_path)

        # Create fake bundle output
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
            patch("sys.platform", "darwin"),
        ):
            result = build_desktop_app_bundle(config=config, app_root=app_root, output_dir=None)

        assert result == app_root / "dist"
        assert (result / "myapp.app" / "Contents" / "Info.plist").exists()

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
            patch("sys.platform", "darwin"),
        ):
            result = build_desktop_app_bundle(
                config=config, app_root=app_root, output_dir=custom_dest
            )

        assert result == custom_dest
        assert (custom_dest / "myapp.app").exists()

    def test_copies_dmg_when_present(self, tmp_path: Path) -> None:
        config, app_root, mock_rust, mock_python = self._setup_bundle(tmp_path)

        bundle_dir = tmp_path / "scaffold" / "target" / "release" / "bundle"
        macos_dir = bundle_dir / "macos"
        macos_dir.mkdir(parents=True)
        app_bundle = macos_dir / "myapp.app"
        app_bundle.mkdir()
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
            patch("sys.platform", "darwin"),
        ):
            result = build_desktop_app_bundle(
                config=config,
                app_root=app_root,
                output_dir=None,
                bundles=["app", "dmg"],
            )

        assert (result / "myapp_1.0.0_aarch64.dmg").exists()
