"""Rust toolchain management via rustup."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import httpx
from packaging.version import Version

from trellis.bundler.utils import CACHE_DIR
from trellis.toolchain.platform import get_rust_target

# Imported from __init__ at runtime; defined here to avoid circular import
# during testing. Tests patch the constant via the module where it's used.
MINIMUM_RUST_VERSION = "1.93.1"


@dataclass
class RustToolchain:
    """Paths to a Rust toolchain installation."""

    cargo_home: Path
    rustup_home: Path
    cargo_bin: Path
    rustc_bin: Path
    rustc_version: str = MINIMUM_RUST_VERSION

    def env(self) -> dict[str, str]:
        """Return environment variables for this toolchain.

        Includes RUSTUP_TOOLCHAIN so that rustup proxy binaries (e.g.
        ~/.cargo/bin/cargo) know which toolchain to invoke even when
        no default toolchain is configured.
        """
        return {
            "CARGO_HOME": str(self.cargo_home),
            "RUSTUP_HOME": str(self.rustup_home),
            "RUSTUP_TOOLCHAIN": self.rustc_version,
            "PATH": str(self.cargo_home / "bin") + os.pathsep + os.environ.get("PATH", ""),
        }


def _parse_rustc_version(output: str) -> str | None:
    """Extract the version string from ``rustc --version`` output.

    Returns:
        The version string (e.g. ``"1.86.0"``) or ``None`` if unparseable.
    """
    match = re.search(r"rustc (\d+\.\d+\.\d+)", output)
    if match is None:
        return None
    return match.group(1)


def _check_rustc_version(output: str) -> bool:
    """Check if rustc version output meets the minimum version requirement.

    Args:
        output: stdout from `rustc --version`

    Returns:
        True if the version is >= MINIMUM_RUST_VERSION
    """
    version = _parse_rustc_version(output)
    if version is None:
        return False
    return Version(version) >= Version(MINIMUM_RUST_VERSION)


def _try_system_rustc() -> RustToolchain | None:
    """Check for a system-installed rustc with sufficient version."""
    rustc_path = shutil.which("rustc")
    if rustc_path is None:
        return None

    result = subprocess.run(
        [rustc_path, "--version"],
        check=False,
        capture_output=True,
        text=True,
    )
    version = _parse_rustc_version(result.stdout)
    if version is None or Version(version) < Version(MINIMUM_RUST_VERSION):
        return None

    cargo_path = shutil.which("cargo")
    if cargo_path is None:
        return None

    rustc = Path(rustc_path)
    cargo = Path(cargo_path)
    # Infer homes from binary locations, but only if the binary is in a
    # standard ~/.cargo/bin/ layout. System installs (e.g. /usr/bin/cargo)
    # would incorrectly infer /usr as cargo_home.
    bin_dir = cargo.parent
    potential_cargo_home = bin_dir.parent
    if bin_dir.name == "bin" and potential_cargo_home.name == ".cargo":
        cargo_home = potential_cargo_home
        default_rustup = potential_cargo_home.parent / ".rustup"
    else:
        cargo_home = Path(os.environ.get("CARGO_HOME", Path.home() / ".cargo"))
        default_rustup = Path.home() / ".rustup"
    rustup_home = Path(os.environ.get("RUSTUP_HOME", default_rustup))

    return RustToolchain(
        cargo_home=cargo_home,
        rustup_home=rustup_home,
        cargo_bin=cargo,
        rustc_bin=rustc,
        rustc_version=version,
    )


def _try_rustup_install() -> RustToolchain | None:
    """Use existing rustup to install the required toolchain version."""
    rustup_path = shutil.which("rustup")
    if rustup_path is None:
        return None

    cargo_home = Path(os.environ.get("CARGO_HOME", CACHE_DIR / "rust" / "cargo"))
    rustup_home = Path(os.environ.get("RUSTUP_HOME", CACHE_DIR / "rust" / "rustup"))

    subprocess.run(
        [rustup_path, "toolchain", "install", MINIMUM_RUST_VERSION, "--profile", "minimal"],
        check=True,
        env={
            **os.environ,
            "CARGO_HOME": str(cargo_home),
            "RUSTUP_HOME": str(rustup_home),
        },
    )

    ext = ".exe" if sys.platform == "win32" else ""
    cargo_bin = cargo_home / "bin" / f"cargo{ext}"
    rustc_bin = cargo_home / "bin" / f"rustc{ext}"

    return RustToolchain(
        cargo_home=cargo_home,
        rustup_home=rustup_home,
        cargo_bin=cargo_bin,
        rustc_bin=rustc_bin,
    )


def _download_rustup() -> RustToolchain:
    """Download rustup-init and install Rust from scratch."""
    cargo_home = CACHE_DIR / "rust" / "cargo"
    rustup_home = CACHE_DIR / "rust" / "rustup"
    cargo_home.mkdir(parents=True, exist_ok=True)
    rustup_home.mkdir(parents=True, exist_ok=True)

    target = get_rust_target()

    if target.endswith("-msvc"):
        binary_name = "rustup-init.exe"
    else:
        binary_name = "rustup-init"

    url = f"https://static.rust-lang.org/rustup/dist/{target}/{binary_name}"

    init_path = cargo_home / binary_name
    timeout = httpx.Timeout(60.0, connect=10.0)
    with httpx.stream("GET", url, follow_redirects=True, timeout=timeout) as r:
        r.raise_for_status()
        with open(init_path, "wb") as f:
            f.writelines(r.iter_bytes())

    init_path.chmod(0o755)

    env = {
        **os.environ,
        "CARGO_HOME": str(cargo_home),
        "RUSTUP_HOME": str(rustup_home),
    }

    subprocess.run(
        [
            str(init_path),
            "--no-modify-path",
            f"--default-toolchain={MINIMUM_RUST_VERSION}",
            "--profile=minimal",
            "-y",
        ],
        check=True,
        env=env,
    )

    init_path.unlink(missing_ok=True)

    ext = ".exe" if sys.platform == "win32" else ""
    return RustToolchain(
        cargo_home=cargo_home,
        rustup_home=rustup_home,
        cargo_bin=cargo_home / "bin" / f"cargo{ext}",
        rustc_bin=cargo_home / "bin" / f"rustc{ext}",
    )


def ensure_rustup() -> RustToolchain:
    """Ensure a Rust toolchain is available, downloading if necessary.

    Detection order:
    1. CARGO_HOME/RUSTUP_HOME env vars -> check rustc version there
    2. System rustc (shutil.which) -> check version >= MSRV
    3. System rustup exists -> `rustup toolchain install`
    4. Nothing found -> download rustup-init and install

    Returns:
        RustToolchain with paths to cargo and rustc binaries
    """
    # 1. Check env vars for existing installation
    env_cargo = os.environ.get("CARGO_HOME")
    env_rustup = os.environ.get("RUSTUP_HOME")
    if env_cargo and env_rustup:
        cargo_home = Path(env_cargo)
        rustup_home = Path(env_rustup)
        ext = ".exe" if sys.platform == "win32" else ""
        rustc = cargo_home / "bin" / f"rustc{ext}"
        cargo = cargo_home / "bin" / f"cargo{ext}"
        if rustc.exists() and cargo.exists():
            result = subprocess.run(
                [str(rustc), "--version"],
                check=False,
                capture_output=True,
                text=True,
            )
            version = _parse_rustc_version(result.stdout)
            if version is not None and Version(version) >= Version(MINIMUM_RUST_VERSION):
                return RustToolchain(
                    cargo_home=cargo_home,
                    rustup_home=rustup_home,
                    cargo_bin=cargo,
                    rustc_bin=rustc,
                    rustc_version=version,
                )

    # 2. Check system rustc
    toolchain = _try_system_rustc()
    if toolchain is not None:
        return toolchain

    # 3. Try existing rustup
    toolchain = _try_rustup_install()
    if toolchain is not None:
        return toolchain

    # 4. Download rustup from scratch
    return _download_rustup()
