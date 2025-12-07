"""Decorator for async main entry points."""

from __future__ import annotations

import asyncio
import inspect
import typing as tp

F = tp.TypeVar("F", bound=tp.Callable[[], tp.Coroutine[tp.Any, tp.Any, None]])


def async_main(fn: F) -> F:
    """Decorator that runs an async function as the main entry point.

    Checks if the calling module is __main__. If so, creates an event loop
    and runs the decorated function. Otherwise, returns the function unmodified.

    Usage:
        @async_main
        async def main() -> None:
            ...
    """
    frame = inspect.currentframe()
    if frame is None:
        return fn

    caller_frame = frame.f_back
    if caller_frame is None:
        return fn

    caller_globals = caller_frame.f_globals
    if caller_globals.get("__name__") == "__main__":
        asyncio.run(fn())

    return fn
