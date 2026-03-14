"""Unit tests for trellis.toolchain.rustup module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from trellis.toolchain import MINIMUM_RUST_VERSION
from trellis.toolchain.platform import get_rust_target
from trellis.toolchain.rustup import RustToolchain, _check_rustc_version, ensure_rustup


class TestGetRustTarget:
    """Tests for get_rust_target function."""

    def test_darwin_arm64(self) -> None:
        with patch("platform.system", return_value="Darwin"):
            with patch("platform.machine", return_value="arm64"):
                assert get_rust_target() == "aarch64-apple-darwin"

    def test_darwin_x86_64(self) -> None:
        with patch("platform.system", return_value="Darwin"):
            with patch("platform.machine", return_value="x86_64"):
                assert get_rust_target() == "x86_64-apple-darwin"

    def test_linux_x86_64(self) -> None:
        with patch("platform.system", return_value="Linux"):
            with patch("platform.machine", return_value="x86_64"):
                assert get_rust_target() == "x86_64-unknown-linux-gnu"

    def test_linux_aarch64(self) -> None:
        with patch("platform.system", return_value="Linux"):
            with patch("platform.machine", return_value="aarch64"):
                assert get_rust_target() == "aarch64-unknown-linux-gnu"

    def test_linux_arm64(self) -> None:
        with patch("platform.system", return_value="Linux"):
            with patch("platform.machine", return_value="arm64"):
                assert get_rust_target() == "aarch64-unknown-linux-gnu"

    def test_windows_x86_64(self) -> None:
        with patch("platform.system", return_value="Windows"):
            with patch("platform.machine", return_value="AMD64"):
                assert get_rust_target() == "x86_64-pc-windows-msvc"

    def test_windows_aarch64(self) -> None:
        with patch("platform.system", return_value="Windows"):
            with patch("platform.machine", return_value="ARM64"):
                assert get_rust_target() == "aarch64-pc-windows-msvc"

    def test_unsupported_os(self) -> None:
        with patch("platform.system", return_value="FreeBSD"):
            with patch("platform.machine", return_value="x86_64"):
                with pytest.raises(RuntimeError, match="Unsupported platform"):
                    get_rust_target()

    def test_unsupported_arch(self) -> None:
        with patch("platform.system", return_value="Linux"):
            with patch("platform.machine", return_value="riscv64"):
                with pytest.raises(RuntimeError, match="Unsupported platform"):
                    get_rust_target()


class TestCheckRustcVersion:
    """Tests for _check_rustc_version function."""

    def test_parses_standard_version(self) -> None:
        output = "rustc 1.93.1 (05f9846f8 2025-03-31)"
        assert _check_rustc_version(output) is True

    def test_rejects_old_version(self) -> None:
        output = "rustc 1.70.0 (some-hash 2023-01-01)"
        assert _check_rustc_version(output) is False

    def test_accepts_exact_minimum(self) -> None:
        output = f"rustc {MINIMUM_RUST_VERSION} (hash 2025-01-01)"
        assert _check_rustc_version(output) is True

    def test_rejects_unparseable_output(self) -> None:
        output = "not rustc at all"
        assert _check_rustc_version(output) is False


class TestRustToolchainEnv:
    """Tests for RustToolchain.env() method."""

    def test_includes_rustup_toolchain(self, tmp_path: Path) -> None:
        """env() includes RUSTUP_TOOLCHAIN so rustup proxy knows which toolchain to use."""
        toolchain = RustToolchain(
            cargo_home=tmp_path / "cargo",
            rustup_home=tmp_path / "rustup",
            cargo_bin=tmp_path / "cargo" / "bin" / "cargo",
            rustc_bin=tmp_path / "cargo" / "bin" / "rustc",
            rustc_version="1.86.0",
        )
        env = toolchain.env()
        assert env["RUSTUP_TOOLCHAIN"] == "1.86.0"

    def test_defaults_to_minimum_version(self, tmp_path: Path) -> None:
        """Without explicit rustc_version, defaults to MINIMUM_RUST_VERSION."""
        toolchain = RustToolchain(
            cargo_home=tmp_path / "cargo",
            rustup_home=tmp_path / "rustup",
            cargo_bin=tmp_path / "cargo" / "bin" / "cargo",
            rustc_bin=tmp_path / "cargo" / "bin" / "rustc",
        )
        env = toolchain.env()
        assert env["RUSTUP_TOOLCHAIN"] == MINIMUM_RUST_VERSION


class TestEnsureRustup:
    """Tests for ensure_rustup function."""

    def test_detects_system_rustc(self, tmp_path: Path) -> None:
        """Uses system rustc when version is sufficient."""
        rustc_path = tmp_path / "rustc"
        rustc_path.write_text("fake")
        cargo_path = tmp_path / "cargo"
        cargo_path.write_text("fake")

        mock_run = MagicMock()
        mock_run.return_value.stdout = f"rustc {MINIMUM_RUST_VERSION} (hash 2025-01-01)"

        which_map = {
            "rustc": str(rustc_path),
            "cargo": str(cargo_path),
        }

        with (
            patch(
                "trellis.toolchain.rustup.shutil.which",
                side_effect=which_map.get,
            ),
            patch("subprocess.run", mock_run),
            patch.dict("os.environ", {}, clear=True),
        ):
            result = ensure_rustup()

        assert result.rustc_bin == rustc_path
        assert result.cargo_bin == cargo_path

    def test_uses_rustup_when_version_too_old(self, tmp_path: Path) -> None:
        """Falls back to rustup install when system rustc version is too old."""
        rustc_path = tmp_path / "rustc"
        rustc_path.write_text("fake")
        rustup_path = tmp_path / "rustup"
        rustup_path.write_text("fake")

        mock_run = MagicMock()
        mock_run.return_value.stdout = "rustc 1.50.0 (hash 2021-01-01)"

        which_map = {
            "rustc": str(rustc_path),
            "rustup": str(rustup_path),
            "cargo": None,
        }

        with (
            patch(
                "trellis.toolchain.rustup.shutil.which",
                side_effect=which_map.get,
            ),
            patch("subprocess.run", mock_run),
            patch.dict("os.environ", {}, clear=True),
            patch("trellis.toolchain.rustup.CACHE_DIR", tmp_path / "cache"),
        ):
            ensure_rustup()

        # Should have called rustup toolchain install
        install_call = [
            c for c in mock_run.call_args_list if len(c[0]) > 0 and "toolchain" in str(c[0][0])
        ]
        assert len(install_call) > 0

    def test_uses_rustup_creates_cache_homes(self, tmp_path: Path) -> None:
        """Creates cache cargo/rustup homes before invoking rustup install."""
        rustc_path = tmp_path / "rustc"
        rustc_path.write_text("fake")
        rustup_path = tmp_path / "rustup"
        rustup_path.write_text("fake")
        cache_dir = tmp_path / "cache"

        mock_run = MagicMock()
        mock_run.return_value.stdout = "rustc 1.50.0 (hash 2021-01-01)"

        which_map = {
            "rustc": str(rustc_path),
            "rustup": str(rustup_path),
            "cargo": None,
        }

        with (
            patch(
                "trellis.toolchain.rustup.shutil.which",
                side_effect=which_map.get,
            ),
            patch("subprocess.run", mock_run),
            patch.dict("os.environ", {}, clear=True),
            patch("trellis.toolchain.rustup.CACHE_DIR", cache_dir),
        ):
            ensure_rustup()

        assert (cache_dir / "rust" / "cargo").is_dir()
        assert (cache_dir / "rust" / "rustup").is_dir()

    def test_uses_existing_rustup_homes_when_rustup_is_in_dot_cargo(self, tmp_path: Path) -> None:
        """Uses the existing ~/.cargo and ~/.rustup homes for a system rustup install."""
        rustc_path = tmp_path / "rustc"
        rustc_path.write_text("fake")
        cargo_home = tmp_path / ".cargo"
        rustup_home = tmp_path / ".rustup"
        rustup_bin = cargo_home / "bin"
        rustup_bin.mkdir(parents=True)
        rustup_path = rustup_bin / "rustup"
        rustup_path.write_text("fake")

        mock_run = MagicMock()
        mock_run.return_value.stdout = "rustc 1.50.0 (hash 2021-01-01)"

        which_map = {
            "rustc": str(rustc_path),
            "rustup": str(rustup_path),
            "cargo": None,
        }

        with (
            patch(
                "trellis.toolchain.rustup.shutil.which",
                side_effect=which_map.get,
            ),
            patch("subprocess.run", mock_run),
            patch.dict("os.environ", {}, clear=True),
        ):
            ensure_rustup()

        rustup_install_env = mock_run.call_args_list[1].kwargs["env"]
        assert rustup_install_env["CARGO_HOME"] == str(cargo_home)
        assert rustup_install_env["RUSTUP_HOME"] == str(rustup_home)

    def test_downloads_rustup_when_nothing_found(self, tmp_path: Path) -> None:
        """Downloads rustup-init when no Rust toolchain found."""
        cache_dir = tmp_path / "cache"

        mock_response = MagicMock()
        mock_response.iter_bytes.return_value = [b"fake rustup-init binary"]
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        mock_run = MagicMock()
        mock_run.return_value.stdout = f"rustc {MINIMUM_RUST_VERSION} (hash 2025-01-01)"

        with (
            patch("trellis.toolchain.rustup.shutil.which", return_value=None),
            patch("subprocess.run", mock_run),
            patch("httpx.stream", return_value=mock_response) as mock_stream,
            patch("trellis.toolchain.rustup.CACHE_DIR", cache_dir),
            patch.dict("os.environ", {}, clear=True),
        ):
            result = ensure_rustup()

        # Verify it attempted a download
        mock_stream.assert_called_once()
        url = mock_stream.call_args[0][1]
        assert "rustup" in url

        assert result.cargo_home == cache_dir / "rust" / "cargo"
        assert result.rustup_home == cache_dir / "rust" / "rustup"

    def test_uses_env_var_paths(self, tmp_path: Path) -> None:
        """Uses CARGO_HOME/RUSTUP_HOME env vars when set."""
        cargo_home = tmp_path / "cargo"
        rustup_home = tmp_path / "rustup"
        cargo_bin = cargo_home / "bin"
        cargo_bin.mkdir(parents=True)
        rustc = cargo_bin / "rustc"
        rustc.write_text("fake")
        cargo = cargo_bin / "cargo"
        cargo.write_text("fake")

        mock_run = MagicMock()
        mock_run.return_value.stdout = f"rustc {MINIMUM_RUST_VERSION} (hash 2025-01-01)"

        with (
            patch("subprocess.run", mock_run),
            patch.dict(
                "os.environ",
                {
                    "CARGO_HOME": str(cargo_home),
                    "RUSTUP_HOME": str(rustup_home),
                },
            ),
        ):
            result = ensure_rustup()

        assert result.cargo_home == cargo_home
        assert result.rustup_home == rustup_home
