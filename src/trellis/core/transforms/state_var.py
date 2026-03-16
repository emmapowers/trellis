"""AST transform for state_var() — eliminates .value boilerplate.

Every Name("x") node where x was assigned from state_var(...) gets replaced with
Attribute(Name("x"), "value"), EXCEPT the initial binding target. This single rule
handles reads, writes, augmented assignments, attribute chains, f-strings, and
closures uniformly.
"""

from __future__ import annotations

import typing as tp
from collections.abc import Callable

import libcst as cst

from trellis.core.transforms.base import _find_function_def


class StateVarTransform:
    """Rewrites state_var() bindings so reads/writes go through .value."""

    def applies_to(self, func: Callable[..., tp.Any]) -> bool:
        return "state_var" in func.__code__.co_names

    def transform(self, func_def: cst.FunctionDef) -> cst.FunctionDef:
        names = _collect_state_var_names(func_def)
        if not names:
            return func_def
        transformer = _StateVarTransformer(names)
        return func_def.with_changes(body=func_def.body.visit(transformer))


def transform_source(source: str) -> tuple[str, bool]:
    """Transform raw source text. Useful for testing without a real function object.

    Returns (transformed_source, changed).
    """
    module = cst.parse_module(source)
    func_def = _find_function_def(module)
    if func_def is None:
        return (source, False)

    t = StateVarTransform()
    new_func_def = t.transform(func_def)
    if new_func_def is func_def:
        return (source, False)

    new_func_def = new_func_def.with_changes(decorators=[])
    new_module = module.with_changes(body=[new_func_def])
    return (new_module.code, True)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _is_state_var_call(node: cst.BaseExpression) -> bool:
    """Check if an expression is a call to state_var(...)."""
    if not isinstance(node, cst.Call):
        return False
    func = node.func
    return isinstance(func, cst.Name) and func.value == "state_var"


def _collect_name_ids(node: cst.CSTNode, target: set[int]) -> None:
    """Recursively find all Name nodes inside *node* and add their ids to *target*."""
    if isinstance(node, cst.Name):
        target.add(id(node))
    for child in node.children:
        if isinstance(child, cst.CSTNode):
            _collect_name_ids(child, target)


def _collect_state_var_names(func_def: cst.FunctionDef) -> set[str]:
    """Collect names assigned from state_var() in the function body."""
    collector = _StateVarNameCollector()
    func_def.body.visit(collector)
    return collector.names


class _StateVarNameCollector(cst.CSTVisitor):
    """Visits the function body to find x = state_var(...) bindings."""

    names: set[str]

    def __init__(self) -> None:
        self.names = set()

    def visit_SimpleStatementLine(self, node: cst.SimpleStatementLine) -> bool | None:
        for stmt in node.body:
            if isinstance(stmt, cst.Assign):
                # x = state_var(...)
                if _is_state_var_call(stmt.value):
                    for target in stmt.targets:
                        if isinstance(target.target, cst.Name):
                            self.names.add(target.target.value)
            elif isinstance(stmt, cst.AnnAssign) and stmt.value is not None:
                # x: T = state_var(...)
                if _is_state_var_call(stmt.value):
                    if isinstance(stmt.target, cst.Name):
                        self.names.add(stmt.target.value)
        return False  # Don't recurse into nested statements


class _StateVarTransformer(cst.CSTTransformer):
    """Replaces Name("x") with Attribute(Name("x"), "value") for state var names.

    The initial binding target (x = state_var(...)) is skipped.
    """

    _state_var_names: set[str]
    _skip_targets: set[int]

    def __init__(self, state_var_names: set[str]) -> None:
        self._state_var_names = state_var_names
        self._skip_targets = set()

    def visit_Assign(self, node: cst.Assign) -> bool | None:
        # Mark the initial binding targets so we don't transform them
        if _is_state_var_call(node.value):
            for target in node.targets:
                if isinstance(target.target, cst.Name):
                    self._skip_targets.add(id(target.target))
            # Also skip Name nodes inside the state_var() call arguments
            # to handle self-referential cases like count = state_var(count)
            _collect_name_ids(node.value, self._skip_targets)
        return True

    def visit_AnnAssign(self, node: cst.AnnAssign) -> bool | None:
        if node.value is not None and _is_state_var_call(node.value):
            if isinstance(node.target, cst.Name):
                self._skip_targets.add(id(node.target))
            # Also skip Name nodes inside the state_var() call arguments
            _collect_name_ids(node.value, self._skip_targets)
        return True

    def visit_Arg(self, node: cst.Arg) -> bool | None:
        # Keyword argument names (f(count=expr)) must not be transformed
        if node.keyword is not None:
            self._skip_targets.add(id(node.keyword))
        return True

    def visit_Nonlocal(self, node: cst.Nonlocal) -> bool | None:
        for item in node.names:
            self._skip_targets.add(id(item.name))
        return True

    def visit_Global(self, node: cst.Global) -> bool | None:
        for item in node.names:
            self._skip_targets.add(id(item.name))
        return True

    def leave_Assign(
        self, original_node: cst.Assign, updated_node: cst.Assign
    ) -> cst.Assign | cst.AugAssign:
        """Transform x = expr to x.value = expr when x is a state var.

        Skips x = state_var(...) bindings.
        """
        if _is_state_var_call(original_node.value):
            return updated_node

        # Only handle single-target assignments to state var names
        if len(updated_node.targets) != 1:
            return updated_node

        target = updated_node.targets[0].target
        if not isinstance(target, cst.Name):
            return updated_node
        if target.value not in self._state_var_names:
            return updated_node

        # x = expr → x.value = expr
        new_target = cst.Attribute(value=target, attr=cst.Name("value"))
        return updated_node.with_changes(
            targets=[updated_node.targets[0].with_changes(target=new_target)]
        )

    def leave_AugAssign(
        self, original_node: cst.AugAssign, updated_node: cst.AugAssign
    ) -> cst.AugAssign:
        """Transform x += expr to x.value += expr."""
        target = updated_node.target
        if isinstance(target, cst.Name) and target.value in self._state_var_names:
            new_target = cst.Attribute(value=target, attr=cst.Name("value"))
            return updated_node.with_changes(target=new_target)
        return updated_node

    def leave_Name(
        self, original_node: cst.Name, updated_node: cst.Name
    ) -> cst.Name | cst.Attribute:
        """Replace x with x.value for state var names, except binding targets."""
        if updated_node.value not in self._state_var_names:
            return updated_node
        if id(original_node) in self._skip_targets:
            return updated_node
        return cst.Attribute(value=updated_node, attr=cst.Name("value"))
