"""Register trellis-desktop module with the bundler registry."""

from pathlib import Path

from trellis.bundler import DESKTOP_PACKAGES, registry

_CLIENT_SRC = Path(__file__).parent / "client" / "src"

# Register the trellis-desktop module
# Desktop adds Tauri packages on top of common packages
# Also includes index.html as a static file for the dist output
registry.register(
    "trellis-desktop",
    packages=DESKTOP_PACKAGES,
    files=["client/src/**/*.{ts,tsx,css}"],
    static_files={"index.html": _CLIENT_SRC / "index.html"},
)
