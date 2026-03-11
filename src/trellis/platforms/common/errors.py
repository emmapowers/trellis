"""Platform-level transport errors."""


class SessionDisconnected(Exception):
    """Raised when the client transport disconnects during handler work."""
