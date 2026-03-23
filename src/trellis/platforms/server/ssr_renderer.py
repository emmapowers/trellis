"""Bun sidecar process manager for server-side rendering."""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import tempfile
import time
import typing as tp
from pathlib import Path

import httpx

from trellis.bundler.bun import ensure_bun
from trellis.utils.subprocess import stop_child_process_async

logger = logging.getLogger(__name__)

_MAX_RESTART_ATTEMPTS = 3
_HEALTH_CHECK_TIMEOUT = 5.0
_HEALTH_CHECK_INTERVAL = 0.1
_RENDER_TIMEOUT = 10.0
_HTTP_OK = 200


class SSRRenderer:
    """Manages a Bun subprocess that renders React element trees to HTML."""

    _process: asyncio.subprocess.Process | None
    _socket_path: str | None
    _socket_dir: str | None
    _client: httpx.AsyncClient | None
    _restart_count: int
    _lock: asyncio.Lock

    def __init__(self, ssr_bundle_path: Path) -> None:
        self._bundle_path = ssr_bundle_path
        self._process = None
        self._socket_path = None
        self._socket_dir = None
        self._client = None
        self._restart_count = 0
        self._lock = asyncio.Lock()

    @property
    def is_available(self) -> bool:
        """Whether the renderer is running and healthy."""
        return self._process is not None and self._process.returncode is None

    async def start(self) -> None:
        """Start the Bun SSR subprocess."""
        async with self._lock:
            await self._start_locked()

    async def _start_locked(self) -> None:
        """Start the renderer (must be called with _lock held)."""
        if self.is_available:
            return

        bun = ensure_bun()
        self._socket_dir = tempfile.mkdtemp(prefix="trellis-ssr-")
        self._socket_path = os.path.join(self._socket_dir, "ssr.sock")

        env = {**os.environ, "TRELLIS_SSR_SOCKET": self._socket_path}

        logger.debug("Starting SSR renderer: %s %s", bun, self._bundle_path)
        self._process = await asyncio.create_subprocess_exec(
            str(bun),
            str(self._bundle_path),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        transport = httpx.AsyncHTTPTransport(uds=self._socket_path)
        self._client = httpx.AsyncClient(transport=transport, base_url="http://localhost")

        if not await self._wait_for_health():
            await self._stop_locked()
            raise RuntimeError("SSR renderer failed health check")

        self._restart_count = 0
        logger.info("SSR renderer started (pid=%s)", self._process.pid)

    async def _wait_for_health(self) -> bool:
        """Wait for the SSR renderer to become healthy."""
        deadline = time.monotonic() + _HEALTH_CHECK_TIMEOUT
        while time.monotonic() < deadline:
            if self._process is not None and self._process.returncode is not None:
                logger.warning("SSR renderer exited with code %d", self._process.returncode)
                return False
            try:
                if self._client is not None:
                    resp = await self._client.get("/health", timeout=1.0)
                    if resp.status_code == _HTTP_OK:
                        return True
            except (httpx.ConnectError, httpx.TimeoutException, OSError):
                pass
            await asyncio.sleep(_HEALTH_CHECK_INTERVAL)
        return False

    async def render(self, serialized_tree: dict[str, tp.Any]) -> str | None:
        """Render a serialized element tree to HTML. Returns HTML or None on failure."""
        async with self._lock:
            if not self.is_available or self._client is None:
                return None
            client = self._client

        try:
            resp = await client.post(
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
            await self._try_restart()
            return None

    async def _try_restart(self) -> None:
        """Attempt to restart the renderer after a crash."""
        async with self._lock:
            self._restart_count += 1
            if self._restart_count > _MAX_RESTART_ATTEMPTS:
                logger.error("SSR renderer exceeded max restart attempts, disabling")
                await self._stop_locked()
                return

            logger.info("Restarting SSR renderer (attempt %d)", self._restart_count)
            await self._stop_locked()
            try:
                await self._start_locked()
            except Exception:
                logger.exception("Failed to restart SSR renderer")

    async def stop(self) -> None:
        """Terminate the SSR subprocess."""
        async with self._lock:
            await self._stop_locked()

    async def _stop_locked(self) -> None:
        """Stop the renderer (must be called with _lock held)."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

        if self._process is not None:
            await stop_child_process_async(self._process)
            self._process = None
            logger.debug("SSR renderer stopped")

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
