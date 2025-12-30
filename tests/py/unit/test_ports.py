"""Unit tests for trellis.platforms.common.ports module."""

from __future__ import annotations

import socket

import pytest


class TestFindAvailablePort:
    """Tests for find_available_port function."""

    def test_returns_port_in_range(self) -> None:
        """Returns a port within the specified range."""
        from trellis.platforms.common.ports import find_available_port

        port = find_available_port(start=9000, end=9010)

        assert 9000 <= port < 9010

    def test_returns_first_available(self) -> None:
        """Returns the first available port when others are busy."""
        from trellis.platforms.common.ports import find_available_port

        # Bind the first port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", 9100))
        sock.listen(1)

        try:
            # Should skip 9100 and return 9101
            port = find_available_port(start=9100, end=9110)
            assert port == 9101
        finally:
            sock.close()

    def test_raises_when_all_ports_busy(self) -> None:
        """Raises RuntimeError when all ports in range are busy."""
        from trellis.platforms.common.ports import find_available_port

        # Bind all ports in a small range
        sockets = []
        for p in range(9200, 9203):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("127.0.0.1", p))
            s.listen(1)
            sockets.append(s)

        try:
            with pytest.raises(RuntimeError, match="No available port found"):
                find_available_port(start=9200, end=9203)
        finally:
            for s in sockets:
                s.close()

    def test_respects_host_parameter(self) -> None:
        """Binds to the specified host address."""
        from trellis.platforms.common.ports import find_available_port

        # Default host is 127.0.0.1, should work
        port = find_available_port(start=9300, end=9310, host="127.0.0.1")
        assert 9300 <= port < 9310

    def test_uses_default_range(self) -> None:
        """Uses default range when not specified."""
        from trellis.platforms.common.ports import (
            DEFAULT_PORT_END,
            DEFAULT_PORT_START,
            find_available_port,
        )

        port = find_available_port()

        assert DEFAULT_PORT_START <= port < DEFAULT_PORT_END
