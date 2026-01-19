"""Register trellis-browser module with the bundler registry."""

from pathlib import Path

from trellis.bundler import registry

_CLIENT_SRC = Path(__file__).parent / "client" / "src"

# Register the trellis-browser module
registry.register(
    "trellis-browser",
    static_files={"index.html": _CLIENT_SRC / "index.html"},
)
