"""Router module for client-side routing in Trellis."""

from trellis.routing.components import Link, Route
from trellis.routing.path_matching import match_path
from trellis.routing.state import RouterState, router

__all__ = ["Link", "Route", "RouterState", "match_path", "router"]
