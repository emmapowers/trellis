"""Trellis - A reactive UI framework for Python.

Canonical import style for applications::

    from trellis import Trellis, async_main
    from trellis import widgets as w
    from trellis import html as h

The trellis package exports core rendering primitives (component, Stateful, etc.)
plus async_main and Trellis. Widgets and HTML elements are accessed via their
respective submodules.
"""

from trellis import core
from trellis.core import *
from trellis.utils import async_main

__version__ = "0.1.0"
__all__ = [*core.__all__, "async_main"]  # noqa: PLE0604

# Server imports are optional (they require uvicorn/fastapi which don't work in Pyodide)
try:
    from trellis.server import Trellis  # noqa: F401

    __all__.append("Trellis")
except ImportError:
    pass
