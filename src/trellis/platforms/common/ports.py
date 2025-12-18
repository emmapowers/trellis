"""Port utilities for platforms that serve HTTP."""

from __future__ import annotations

import socket

__all__ = ["find_available_port"]

DEFAULT_PORT_START = 8000
DEFAULT_PORT_END = 8100


def find_available_port(
    start: int = DEFAULT_PORT_START,
    end: int = DEFAULT_PORT_END,
    host: str = "127.0.0.1",
) -> int:
    """Find an available port in the given range.

    Args:
        start: First port to try
        end: Last port to try (exclusive)
        host: Host to bind to for testing

    Returns:
        An available port number

    Raises:
        RuntimeError: If no port is available in the range

    Note:
        There is a small race condition window between when this function
        checks port availability and when the caller actually binds to it.
        Another process could claim the port in that window. Callers should
        handle OSError on bind and retry if needed. In practice, the window
        is very small and the port range provides natural fallback.
    """
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Allow binding to TIME_WAIT ports (matches uvicorn's behavior)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No available port found in range {start}-{end}")
