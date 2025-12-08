"""Trellis - A reactive UI framework for Python."""

from trellis import html

__all__ = ["html"]
__version__ = "0.1.0"

# Server imports are optional (they require uvicorn/fastapi which don't work in Pyodide)
try:
    from trellis.server import Trellis

    __all__.append("Trellis")
except ImportError:
    pass
