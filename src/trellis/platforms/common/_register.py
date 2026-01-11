"""Register trellis-core module with the bundler registry."""

from trellis.bundler import PACKAGES, registry

# Register the trellis-core module
# This provides all the common/shared TypeScript code
registry.register(
    "trellis-core",
    packages=PACKAGES,
    files=["client/src/**/*.{ts,tsx,css}"],
)
