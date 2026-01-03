"""Routing-specific exceptions."""


class RouteParamConflictError(Exception):
    """Raised when multiple routes set conflicting values for the same param.

    This error is raised when a route tries to set a parameter that already
    exists with a different value. This typically indicates a routing
    configuration issue where multiple patterns extract the same parameter
    name but with different semantics.

    Example conflict:
        Route("/users/:id/posts/:postId")  # Sets id="123"
        Route("/users/:userId/posts/:id")  # Tries to set id="456" - CONFLICT
    """

    pass
