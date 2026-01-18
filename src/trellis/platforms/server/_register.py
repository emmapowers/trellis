"""Register trellis-server module with the bundler registry."""

from trellis.bundler import registry

# Register the trellis-server module
registry.register(
    "trellis-server",
    files=["client/src/**/*.{ts,tsx,css}"],
)
