"""Trellis - A reactive UI framework for Python.

Canonical import style for applications::

    from trellis import Trellis, async_main
    from trellis import widgets as w
    from trellis import html as h
    from trellis.widgets import IconName

The trellis package exports core rendering primitives (component, Stateful, etc.)
plus async_main and Trellis. Widgets and HTML elements are accessed via their
respective submodules. Icons are available via ``trellis.widgets.IconName``.
"""

from trellis import core
from trellis.core import *
from trellis.core.trellis import Trellis
from trellis.utils import async_main

__version__ = "0.1.0"
__all__ = [*core.__all__, "async_main", "Trellis"]  # noqa: PLE0604
