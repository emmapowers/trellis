"""Async resource helper built on slot-local controller state."""

from __future__ import annotations

import asyncio
import typing as tp
import weakref

from trellis.core.callback_context import callback_context
from trellis.core.rendering.session import get_active_session
from trellis.core.state.stateful import Stateful

T = tp.TypeVar("T")
U = tp.TypeVar("U")

_STATUS_LOADING = "loading"
_STATUS_READY = "ready"
_STATUS_FAILED = "failed"


class _NoKey:
    """Sentinel for a missing load key."""

    pass


_NO_KEY = _NoKey()

__all__ = ["Failed", "Load", "Loading", "Ready", "load"]


class Load[T]:
    """Base wrapper around a private load controller."""

    __slots__ = ("_controller",)

    def __init__(self, controller: _LoadState) -> None:
        self._controller = controller

    @property
    def loading(self) -> bool:
        return self._controller.status == _STATUS_LOADING

    @property
    def ready(self) -> bool:
        return self._controller.status == _STATUS_READY

    @property
    def failed(self) -> bool:
        return self._controller.status == _STATUS_FAILED

    def get(self, default: U) -> T | U:
        if self.ready:
            return tp.cast("T", self._controller.value)
        return default

    def reload(self) -> None:
        self._controller.reload()


class Loading[T](Load[T]):
    """Wrapper for an in-flight resource."""


class Ready[T](Load[T]):
    """Wrapper for a successfully loaded resource."""

    @property
    def value(self) -> T:
        return tp.cast("T", self._controller.value)


class Failed[T](Load[T]):
    """Wrapper for a failed resource."""

    @property
    def error(self) -> Exception:
        return tp.cast("Exception", self._controller.error)


class _LoadState(Stateful):
    """Private element-local controller backing load()."""

    status: str
    value: object | None
    error: Exception | None

    if tp.TYPE_CHECKING:
        _active_task: asyncio.Task[object] | None
        _args: tuple[object, ...]
        _element_id: str | None
        _fn: tp.Callable[..., tp.Awaitable[object]]
        _request_generation: int
        _has_request: bool
        _key: object | _NoKey
        _kwargs: dict[str, object]
        _session_ref: weakref.ref[tp.Any] | None
    _active_task = None
    _args = ()
    _element_id = None
    _fn = None
    _request_generation = 0
    _has_request = False
    _key = _NO_KEY
    _kwargs = None
    _session_ref = None

    def __init__(self) -> None:
        self.status = _STATUS_LOADING
        self.value = None
        self.error = None
        self._active_task = None
        self._args = ()
        self._element_id = None
        self._request_generation = 0
        self._has_request = False
        self._key = _NO_KEY
        self._kwargs = {}
        self._session_ref = None

    def use(
        self,
        fn: tp.Callable[..., tp.Awaitable[T]],
        args: tuple[object, ...],
        kwargs: dict[str, object],
        key: object | _NoKey,
    ) -> None:
        """Update the semantic inputs for this slot and restart if needed."""
        session = get_active_session()
        if session is None or not session.is_executing():
            raise RuntimeError(
                "load() can only be called during component execution (render context)."
            )

        self._session_ref = weakref.ref(session)
        self._element_id = session.current_element_id

        should_restart = not self._has_request or self._inputs_changed(args, kwargs, key)

        self._fn = tp.cast("tp.Callable[..., tp.Awaitable[object]]", fn)
        self._args = args
        self._kwargs = kwargs
        self._key = key

        if should_restart:
            self._restart(from_render=True)
            self._has_request = True

    def reload(self) -> None:
        """Force a fresh request for the current slot inputs."""
        if not self._has_request:
            return
        self._restart(from_render=False)

    def on_unmount(self) -> None:
        """Cancel any in-flight request when the element unmounts."""
        self._request_generation += 1
        task = self._active_task
        self._active_task = None
        if task is not None:
            task.cancel()

    def _inputs_changed(
        self,
        args: tuple[object, ...],
        kwargs: dict[str, object],
        key: object | _NoKey,
    ) -> bool:
        if self._key is not _NO_KEY or key is not _NO_KEY:
            if self._key is _NO_KEY or key is _NO_KEY:
                return True
            return self._key != key

        try:
            return self._args != args or self._kwargs != kwargs
        except Exception as exc:  # pragma: no cover - exercised via integration test
            raise TypeError(
                "load() could not compare args/kwargs for equality; provide key=... "
                "to define reload semantics explicitly."
            ) from exc

    def _restart(self, *, from_render: bool) -> None:
        session = self._session()
        element_id = self._element_id
        if session is None or element_id is None:
            raise RuntimeError("load() is not attached to an active render session.")

        self._request_generation += 1
        request_generation = self._request_generation

        task = self._active_task
        if task is not None:
            task.cancel()

        if from_render:
            # Internal controller state needs to show Loading in the same render pass.
            object.__setattr__(self, "status", _STATUS_LOADING)
            object.__setattr__(self, "value", None)
            object.__setattr__(self, "error", None)
        else:
            self.status = _STATUS_LOADING
            self.value = None
            self.error = None

        fn = self._fn
        args = self._args
        kwargs = dict(self._kwargs)
        self._active_task = session.track_background_task(
            asyncio.create_task(
                self._run_request(
                    fn,
                    args,
                    kwargs,
                    request_generation,
                    session,
                    element_id,
                )
            )
        )

    async def _run_request(
        self,
        fn: tp.Callable[..., tp.Awaitable[object]],
        args: tuple[object, ...],
        kwargs: dict[str, object],
        request_generation: int,
        session: tp.Any,
        element_id: str,
    ) -> None:
        try:
            with callback_context(session, element_id):
                value = await fn(*args, **kwargs)
        except asyncio.CancelledError:
            return
        except Exception as exc:
            if request_generation != self._request_generation:
                return
            self.status = _STATUS_FAILED
            self.value = None
            self.error = exc
            return

        if request_generation != self._request_generation:
            return

        self.status = _STATUS_READY
        self.value = value
        self.error = None

    def _session(self) -> tp.Any:
        if self._session_ref is None:
            return None
        return self._session_ref()


def load(
    fn: tp.Callable[..., tp.Awaitable[T]],
    *args: object,
    key: object | _NoKey = _NO_KEY,
    **kwargs: object,
) -> Load[T]:
    """Load async data for the current element slot.

    Examples:
        ```python
        async def fetch_message(name: str) -> str:
            await asyncio.sleep(0.1)
            return f"Hello, {name}"

        def Greeting(name: str) -> None:
            result = load(fetch_message, name)

            if isinstance(result, Loading):
                w.Label(text="Loading...")
            elif isinstance(result, Failed):
                w.Label(text=str(result.error))
            else:
                assert isinstance(result, Ready)
                w.Label(text=result.value)
        ```

        ```python
        async def fetch_count() -> int:
            return 3

        result = load(fetch_count)
        value: int = result.get(0)
        ```
    """
    controller = _LoadState()
    controller.use(fn, args, kwargs, key)

    if controller.status == _STATUS_READY:
        return Ready(controller)
    if controller.status == _STATUS_FAILED:
        return Failed(controller)
    return Loading(controller)
