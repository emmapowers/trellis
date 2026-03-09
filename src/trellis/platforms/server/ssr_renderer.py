"""Bun sidecar process manager for server-side rendering."""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile
import threading
import time
import typing as tp
from pathlib import Path

import httpx

from trellis.bundler.bun import ensure_bun
from trellis.utils.subprocess import start_child_process, stop_child_process

logger = logging.getLogger(__name__)

_MAX_RESTART_ATTEMPTS = 3
_HEALTH_CHECK_TIMEOUT = 5.0
_HEALTH_CHECK_INTERVAL = 0.1
_RENDER_TIMEOUT = 10.0
_HTTP_OK = 200


class SSRRenderer:
    """Manages a Bun subprocess that renders React element trees to HTML."""

    def __init__(self, ssr_bundle_path: Path) -> None:
        self._bundle_path = ssr_bundle_path
        self._process: subprocess.Popen[bytes] | None = None
        self._socket_path: str | None = None
        self._socket_dir: str | None = None
        self._client: httpx.Client | None = None
        self._restart_count = 0
        self._lock = threading.Lock()

    @property
    def is_available(self) -> bool:
        """Whether the renderer is running and healthy."""
        return self._process is not None and self._process.poll() is None

    def start(self) -> None:
        """Start the Bun SSR subprocess."""
        with self._lock:
            self._start_locked()

    def _start_locked(self) -> None:
        """Start the renderer (must be called with _lock held)."""
        if self.is_available:
            return

        bun = ensure_bun()
        # Use mkdtemp to create the socket path securely (mktemp is racy)
        self._socket_dir = tempfile.mkdtemp(prefix="trellis-ssr-")
        self._socket_path = os.path.join(self._socket_dir, "ssr.sock")

        env = {**os.environ, "TRELLIS_SSR_SOCKET": self._socket_path}

        logger.debug("Starting SSR renderer: %s %s", bun, self._bundle_path)
        self._process = start_child_process(
            [str(bun), str(self._bundle_path)],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Create HTTP client connected via Unix socket
        transport = httpx.HTTPTransport(uds=self._socket_path)
        self._client = httpx.Client(transport=transport, base_url="http://localhost")

        # Wait for health check
        if not self._wait_for_health():
            self.stop()
            raise RuntimeError("SSR renderer failed health check")

        self._restart_count = 0
        logger.info("SSR renderer started (pid=%s)", self._process.pid)

    def _wait_for_health(self) -> bool:
        """Wait for the SSR renderer to become healthy."""
        deadline = time.monotonic() + _HEALTH_CHECK_TIMEOUT
        while time.monotonic() < deadline:
            # Fail fast if the process has exited
            if self._process is not None and self._process.poll() is not None:
                logger.warning("SSR renderer exited with code %d", self._process.returncode)
                return False
            try:
                if self._client is not None:
                    resp = self._client.get("/health", timeout=1.0)
                    if resp.status_code == _HTTP_OK:
                        return True
            except (httpx.ConnectError, httpx.TimeoutException, OSError):
                pass
            time.sleep(_HEALTH_CHECK_INTERVAL)
        return False

    def render(self, serialized_tree: dict[str, tp.Any]) -> str | None:
        """Render a serialized element tree to HTML.

        Returns HTML string or None on failure.
        """
        # Snapshot client under lock to avoid racing with stop/restart
        with self._lock:
            if not self.is_available or self._client is None:
                return None
            client = self._client

        try:
            resp = client.post(
                "/render",
                json=serialized_tree,
                timeout=_RENDER_TIMEOUT,
            )
            if resp.status_code == _HTTP_OK:
                return resp.text
            logger.warning("SSR render returned status %d", resp.status_code)
            return None
        except (httpx.ConnectError, httpx.TimeoutException, OSError) as e:
            logger.warning("SSR render failed: %s", e)
            self._try_restart()
            return None

    def _try_restart(self) -> None:
        """Attempt to restart the renderer after a crash."""
        with self._lock:
            self._restart_count += 1
            if self._restart_count > _MAX_RESTART_ATTEMPTS:
                logger.error("SSR renderer exceeded max restart attempts, disabling")
                self._stop_locked()
                return

            logger.info("Restarting SSR renderer (attempt %d)", self._restart_count)
            self._stop_locked()
            try:
                self._start_locked()
            except Exception:
                logger.exception("Failed to restart SSR renderer")

    def stop(self) -> None:
        """Terminate the SSR subprocess."""
        with self._lock:
            self._stop_locked()

    def _stop_locked(self) -> None:
        """Stop the renderer (must be called with _lock held)."""
        if self._client is not None:
            self._client.close()
            self._client = None

        if self._process is not None:
            stop_child_process(self._process)
            self._process = None
            logger.debug("SSR renderer stopped")

        # Clean up socket file and directory
        if self._socket_path is not None:
            socket_path = Path(self._socket_path)
            if socket_path.exists():
                socket_path.unlink()
            self._socket_path = None
        if self._socket_dir is not None:
            socket_dir = Path(self._socket_dir)
            if socket_dir.exists():
                socket_dir.rmdir()
            self._socket_dir = None
