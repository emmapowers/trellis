"""Register trellis-core module with the bundler registry."""

from trellis.bundler import registry

# Register the trellis-core module
# This provides all the common/shared TypeScript code
registry.register(
    "trellis-core",
    packages={
        "react": "18.3.1",
        "react-dom": "18.3.1",
        "@types/react": "18.3.23",
        "@types/react-dom": "18.3.7",
        "@msgpack/msgpack": "3.0.0",
        "lucide-react": "0.468.0",
        "uplot": "1.6.31",
        "recharts": "3.6.0",
        "react-aria": "3.35.0",
        "react-stately": "3.33.0",
        "@internationalized/date": "3.5.6",
    },
    files=["client/src/**/*.{ts,tsx,css}"],
)
