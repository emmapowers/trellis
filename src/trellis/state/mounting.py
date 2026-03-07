"""Lifecycle-only mount helper built on Stateful hooks."""

from __future__ import annotations

import inspect
import logging
import typing as tp

from trellis.core.rendering.session import get_active_session
from trellis.core.state.stateful import Stateful

logger = logging.getLogger(__name__)

__all__ = ["mount"]


class _MountState(Stateful):
    """Private slot-local state backing mount()."""

    if tp.TYPE_CHECKING:
        _cleanup: tp.Any | None
        _fn: tp.Callable[[], object]
    _cleanup = None
    _fn = None

    def __init__(self, fn: tp.Callable[[], object]) -> None:
        self._fn = fn
        self._cleanup = None

    def on_mount(self) -> None | tp.Coroutine[tp.Any, tp.Any, None]:
        """Run the captured mount callable once for this element lifetime."""
        if inspect.isasyncgenfunction(self._fn):
            return self._run_async_generator_setup()
        if inspect.iscoroutinefunction(self._fn):
            return self._run_async_function()
        if inspect.isgeneratorfunction(self._fn):
            self._run_generator_setup()
            return None

        self._fn()
        return None

    def on_unmount(self) -> None | tp.Coroutine[tp.Any, tp.Any, None]:
        """Run generator cleanup if the mount callable provided one."""
        cleanup = self._cleanup
        self._cleanup = None

        if cleanup is None:
            return None

        if inspect.isasyncgen(cleanup):
            return self._run_async_generator_cleanup(cleanup)

        self._run_generator_cleanup(cleanup)
        return None

    async def _run_async_function(self) -> None:
        await tp.cast("tp.Callable[[], tp.Awaitable[None]]", self._fn)()

    def _run_generator_setup(self) -> None:
        generator = tp.cast("tp.Callable[[], tp.Generator[object]]", self._fn)()
        try:
            next(generator)
        except StopIteration:
            logger.error("mount() generator must yield exactly once")
            generator.close()
            return

        self._cleanup = generator

    def _run_generator_cleanup(self, generator: tp.Generator[object]) -> None:
        try:
            next(generator)
        except StopIteration:
            generator.close()
            return

        logger.error("mount() generator must yield exactly once")
        generator.close()

    async def _run_async_generator_setup(self) -> None:
        generator = tp.cast(
            "tp.Callable[[], tp.AsyncGenerator[object]]",
            self._fn,
        )()
        try:
            await anext(generator)
        except StopAsyncIteration:
            logger.error("mount() generator must yield exactly once")
            await generator.aclose()
            return

        self._cleanup = generator

    async def _run_async_generator_cleanup(
        self,
        generator: tp.AsyncGenerator[object],
    ) -> None:
        try:
            await anext(generator)
        except StopAsyncIteration:
            await generator.aclose()
            return

        logger.error("mount() generator must yield exactly once")
        await generator.aclose()


def mount(
    fn: tp.Callable[[], object],
) -> None:
    """Register setup/cleanup logic for the current element lifetime."""
    session = get_active_session()
    if session is None or not session.is_executing():
        raise RuntimeError(
            "mount() can only be called during component execution (render context)."
        )

    _MountState(fn)
