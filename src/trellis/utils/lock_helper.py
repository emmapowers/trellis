from __future__ import annotations

import contextlib
import functools
import typing as tp


class ClassWithLock(tp.Protocol):
    lock: LockLike


T = tp.TypeVar("T", bound=ClassWithLock)  # the instance type (i.e., the class of `self`)
P = tp.ParamSpec("P")  # the parameters of the wrapped method
R = tp.TypeVar("R")  # the return type
# Anything usable in a `with` statement.
LockLike = contextlib.AbstractContextManager[object]


def with_lock(fn: tp.Callable[tp.Concatenate[T, P], R]) -> tp.Callable[tp.Concatenate[T, P], R]:
    @functools.wraps(fn)
    def wrapper(self: T, /, *args: P.args, **kwargs: P.kwargs) -> R:
        with self.lock:
            return fn(self, *args, **kwargs)

    return wrapper
