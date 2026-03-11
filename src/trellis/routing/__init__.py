"""Router module for client-side routing in Trellis."""

from trellis.routing.components import Route, Routes
from trellis.routing.enums import RoutingMode
from trellis.routing.errors import RouteParamConflictError
from trellis.routing.messages import HistoryBack, HistoryForward, HistoryPush, UrlChanged
from trellis.routing.state import RouterState, router

__all__ = [
    "HistoryBack",
    "HistoryForward",
    "HistoryPush",
    "Route",
    "RouteParamConflictError",
    "RouterState",
    "Routes",
    "RoutingMode",
    "UrlChanged",
    "router",
]
