"""Application state for the widget showcase."""

from collections.abc import Callable
from dataclasses import dataclass

from trellis import Stateful


@dataclass
class ShowcaseState(Stateful):
    """State for the showcase app navigation."""

    active_tab: str = "layout"
