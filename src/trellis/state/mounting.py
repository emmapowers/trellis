"""Lifecycle-only mount helper built on Stateful hooks."""

from __future__ import annotations

import inspect
import typing as tp

from trellis.core.rendering.session import get_active_session
from trellis.core.state.stateful import Stateful

type OnMountFn = (
    tp.Callable[[], None]
    | tp.Callable[[], tp.Awaitable[None]]
    | tp.Callable[[], tp.Generator[None]]
    | tp.Callable[[], tp.AsyncGenerator[None]]
)

__all__ = ["on_mount"]


class _MountState(Stateful):
    """Private slot-local state backing on_mount()."""

    _cleanup: tp.Generator[None] | tp.AsyncGenerator[None] | None
    _fn: OnMountFn

    def __init__(self, fn: OnMountFn) -> None:
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
            return self._run_async_generator_cleanup(tp.cast("tp.AsyncGenerator[None]", cleanup))

        self._run_generator_cleanup(tp.cast("tp.Generator[None]", cleanup))
        return None

    async def _run_async_function(self) -> None:
        await tp.cast("tp.Callable[[], tp.Awaitable[None]]", self._fn)()

    def _run_generator_setup(self) -> None:
        generator = tp.cast("tp.Callable[[], tp.Generator[None]]", self._fn)()
        try:
            next(generator)
        except StopIteration:
            generator.close()
            raise RuntimeError(self._yield_contract_error()) from None

        self._cleanup = generator

    def _run_generator_cleanup(self, generator: tp.Generator[None]) -> None:
        try:
            next(generator)
        except StopIteration:
            generator.close()
            return

        generator.close()
        raise RuntimeError(self._yield_contract_error())

    async def _run_async_generator_setup(self) -> None:
        generator = tp.cast(
            "tp.Callable[[], tp.AsyncGenerator[None]]",
            self._fn,
        )()
        try:
            await anext(generator)
        except StopAsyncIteration:
            await generator.aclose()
            raise RuntimeError(self._yield_contract_error()) from None

        self._cleanup = generator

    async def _run_async_generator_cleanup(
        self,
        generator: tp.AsyncGenerator[None],
    ) -> None:
        try:
            await anext(generator)
        except StopAsyncIteration:
            await generator.aclose()
            return

        await generator.aclose()
        raise RuntimeError(self._yield_contract_error())

    def _yield_contract_error(self) -> str:
        fn_name = getattr(self._fn, "__qualname__", repr(self._fn))
        return f"on_mount() generator {fn_name} must yield exactly once"


def on_mount(
    fn: OnMountFn,
) -> None:
    """Register setup and cleanup logic for the current element lifetime.

    Supported callback forms:
    - Sync function: runs setup immediately after mount.
    - Async function: runs setup in a session-managed background task.
    - Sync generator: runs setup until `yield`, then resumes on unmount for cleanup.
    - Async generator: awaits setup until `yield`, then awaits cleanup on unmount.

    Examples:
        ```python
        @component
        def ConnectedBadge() -> None:
            connected = state_var(False)

            async def connect() -> None:
                connected.set(True)

            on_mount(connect)
            w.Badge(text="Connected" if connected.value else "Connecting")
        ```

        ```python
        async def subscribe() -> tp.AsyncGenerator[None]:
            connection = await connect()
            yield
            await connection.close()

        @component
        def ConnectedPanel() -> None:
            on_mount(subscribe)
            w.Label(text="Streaming updates")
        ```
    """
    session = get_active_session()
    if session is None or not session.is_executing():
        raise RuntimeError(
            "on_mount() can only be called during component execution (render context)."
        )

    _MountState(fn)
