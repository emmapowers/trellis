"""Application state for the widget showcase."""

from dataclasses import dataclass

from trellis import Stateful


@dataclass
class ShowcaseState(Stateful):
    """State for interactive widgets in the showcase."""

    # Current tab
    active_tab: str = "layout"

    # Form inputs section
    text_value: str = ""
    number_value: float = 50
    slider_value: float = 50
    checkbox_value: bool = False
    select_value: str = "option1"

    # Navigation section
    selected_tab: str = "overview"
    selected_tree_node: str = ""

    # Feedback section
    collapsible_expanded: bool = True
    experimental_features: bool = False
