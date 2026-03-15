"""Source transform infrastructure for decorator-driven AST rewriting.

Decorators like @component pass an ordered list of transforms to apply_transforms().
Each transform decides whether it applies (via bytecode inspection), then rewrites
the function's CST. Source is parsed once and compiled once regardless of how many
transforms run.
"""

from __future__ import annotations

import inspect
import textwrap
import typing as tp
from collections.abc import Callable

import libcst as cst

__all__ = ["SourceTransform", "apply_transforms"]


class SourceTransform(tp.Protocol):
    """A source-level rewrite that a decorator can apply to a function."""

    def applies_to(self, func: Callable[..., tp.Any]) -> bool:
        """Return True if this transform should run on the given function."""
        ...

    def transform(self, func_def: cst.FunctionDef) -> cst.FunctionDef:
        """Rewrite the function's CST. Return the modified FunctionDef."""
        ...


def apply_transforms(
    func: Callable[..., tp.Any],
    transforms: list[SourceTransform],
) -> Callable[..., tp.Any]:
    """Apply a sequence of source transforms to a function.

    Parses source once, runs each applicable transform in order, strips
    decorators, and compiles once. Returns the original function unchanged
    if no transforms apply or source is unavailable.
    """
    applicable = [t for t in transforms if t.applies_to(func)]
    if not applicable:
        return func

    try:
        source = textwrap.dedent(inspect.getsource(func))
    except OSError:
        return func

    module = cst.parse_module(source)
    func_def = _find_function_def(module)
    if func_def is None:
        return func

    changed = False
    for transform in applicable:
        new_func_def = transform.transform(func_def)
        if new_func_def is not func_def:
            func_def = new_func_def
            changed = True

    if not changed:
        return func

    # Strip decorators from the bare def for recompilation
    func_def = func_def.with_changes(decorators=[])
    new_module = module.with_changes(body=[func_def])
    return _compile_transformed(func, new_module.code)


def _find_function_def(module: cst.Module) -> cst.FunctionDef | None:
    """Find the first FunctionDef in a module."""
    for stmt in module.body:
        if isinstance(stmt, cst.FunctionDef):
            return stmt
    return None


def _compile_transformed(func: Callable[..., tp.Any], source: str) -> Callable[..., tp.Any]:
    """Compile transformed source and extract the new function object.

    Pads with newlines to preserve original line numbers for tracebacks.
    Injects closure variables into globals so the recompiled function can
    access the same imports, module-level names, and enclosing-scope variables.
    """
    padded = "\n" * (func.__code__.co_firstlineno - 1) + source
    code = compile(padded, func.__code__.co_filename, "exec")

    run_globals: dict[str, tp.Any]
    if func.__closure__ and func.__code__.co_freevars:
        run_globals = {**func.__globals__}
        for name, cell in zip(func.__code__.co_freevars, func.__closure__, strict=True):
            try:
                run_globals[name] = cell.cell_contents
            except ValueError:
                pass  # Unbound cell — variable not yet assigned
    else:
        run_globals = func.__globals__

    # Safe: source comes from inspect.getsource() on the user's own function,
    # transformed only by our deterministic CST rewriter.
    exec(code, run_globals)
    new_func = run_globals[func.__name__]
    new_func.__module__ = func.__module__
    new_func.__qualname__ = func.__qualname__
    new_func.__doc__ = func.__doc__
    return new_func
