"""CLI options decorator generated from ConfigVar definitions.

This module provides a decorator that generates click.option decorators
from ConfigVar metadata, making ConfigVars the single source of truth
for CLI option definitions.
"""

from __future__ import annotations

import types
import typing
from collections.abc import Callable
from enum import StrEnum
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar, get_args, get_origin

import click
from click_option_group import OptionGroup

from trellis.app.configvars import ConfigVar

F = TypeVar("F", bound=Callable[..., Any])


def _unwrap_optional_union(target_type: type) -> type:
    """Unwrap Optional[T] or T | None to T.

    Handles both typing.Union (Optional[T]) and types.UnionType (T | None).
    Returns target_type unchanged if not a union.
    """
    origin = get_origin(target_type)
    if origin in (types.UnionType, typing.Union):
        args = [a for a in get_args(target_type) if a is not type(None)]
        if args:
            inner: type = args[0]
            return inner
    return target_type


def get_click_type(var: ConfigVar[Any]) -> click.ParamType | type | None:
    """Derive a Click type from a ConfigVar's type information.

    Args:
        var: The ConfigVar to derive a type from

    Returns:
        A Click type appropriate for the ConfigVar, or None for flags/booleans
    """
    target_type = var._get_target_type()

    if target_type is None:
        return str

    target_type = _unwrap_optional_union(target_type)

    # Bool types are handled specially (flags or --option/--no-option)
    if target_type is bool:
        return None

    # StrEnum -> Choice
    if isinstance(target_type, type) and issubclass(target_type, StrEnum):
        return click.Choice([m.value for m in target_type])

    # Path -> click.Path
    if target_type is Path or (isinstance(target_type, type) and issubclass(target_type, Path)):
        return click.Path()

    # Basic types map directly
    basic_types: dict[type, type] = {int: int, str: str, float: float}
    return basic_types.get(target_type, str)


def _build_option_kwargs(var: ConfigVar[Any]) -> dict[str, Any]:
    """Build kwargs dict for click.option from a ConfigVar.

    Args:
        var: The ConfigVar to build option kwargs from

    Returns:
        Dictionary of keyword arguments for click.option
    """
    kwargs: dict[str, Any] = {}

    # Help text
    if var.help:
        kwargs["help"] = var.help

    # Default is always None for CLI (let ConfigVar resolution handle defaults)
    kwargs["default"] = None

    # Get the target type to determine how to handle this option
    target_type = var._get_target_type()
    if target_type is not None:
        target_type = _unwrap_optional_union(target_type)

    # Boolean handling
    if target_type is bool:
        if var.is_flag:
            # Simple flag: --watch
            kwargs["is_flag"] = True
        else:
            # Boolean option: --hot-reload/--no-hot-reload
            # This is handled by the option name format, not kwargs
            pass
    else:
        # Non-boolean: add type
        click_type = get_click_type(var)
        if click_type is not None:
            kwargs["type"] = click_type

    return kwargs


def _build_option_names(var: ConfigVar[Any]) -> list[str]:
    """Build the option names list for click.option.

    Args:
        var: The ConfigVar to build option names from

    Returns:
        List of option names (e.g., ['-d', '--debug'] or ['--hot-reload/--no-hot-reload'])
    """
    names: list[str] = []

    # Add short name if present
    short_name = var.get_cli_short_name()
    if short_name:
        names.append(short_name)

    # Get target type for boolean handling
    target_type = var._get_target_type()
    if target_type is not None:
        target_type = _unwrap_optional_union(target_type)

    # Boolean non-flag options use --option/--no-option format
    if target_type is bool and not var.is_flag:
        cli_name = var.name.replace("_", "-")
        names.append(f"--{cli_name}/--no-{cli_name}")
    else:
        names.append(var.get_cli_name())

    return names


def _get_group_display_name(category: str) -> str:
    """Convert a category to a display name for option groups.

    Args:
        category: The ConfigVar category (e.g., "", "server", "desktop")

    Returns:
        Display name (e.g., "General Options", "Server Options")
    """
    if not category or category.lower() == "general":
        return "General Options"
    return f"{category.capitalize()} Options"


def configvar_options(configvars: list[ConfigVar[Any]]) -> Callable[[F], F]:
    """Decorator to add click options for each ConfigVar to a command.

    This decorator generates click.option decorators from ConfigVar metadata,
    making ConfigVars the single source of truth for CLI option definitions.

    Options are grouped by category using click-option-group. Categories
    are displayed with "General Options" first, then other categories
    alphabetically.

    The decorator:
    1. Groups ConfigVars by category
    2. Creates OptionGroup per category
    3. Iterates groups in order (General first, then alphabetical)
    4. Builds click.option kwargs from ConfigVar metadata
    5. Derives Click type from ConfigVar type (StrEnum -> Choice, etc.)
    6. Wraps function to filter None values from kwargs before passing

    Args:
        configvars: List of ConfigVar instances to generate options for

    Returns:
        A decorator that adds click options for the ConfigVars

    Example:
        @click.command()
        @configvar_options([_PORT, _HOST, _DEBUG])
        def run(**cli_kwargs):
            with cli_context(cli_kwargs):
                ...
    """
    # Build set of configvar names for filtering
    configvar_names = {var.name for var in configvars}

    # Group vars by category
    groups: dict[str, list[ConfigVar[Any]]] = {}
    for var in configvars:
        category = var.category or ""
        groups.setdefault(category, []).append(var)

    # Sort categories: "" (General) first, then alphabetical
    sorted_categories = sorted(groups.keys(), key=lambda c: ("" if c == "" else c, c))

    def decorator(func: F) -> F:
        # Wrap function to filter None values from configvar options only
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Filter out None values only for configvar options
            # Keep other kwargs (like app_path) even if None
            filtered = {
                k: v for k, v in kwargs.items() if k not in configvar_names or v is not None
            }
            return func(*args, **filtered)

        # Apply options in reverse order (decorators apply bottom-up)
        # So we iterate categories in reverse, and vars in each category in reverse
        decorated = wrapper
        for category in reversed(sorted_categories):
            vars_in_category = groups[category]
            group_name = _get_group_display_name(category)
            option_group = OptionGroup(group_name)

            for var in reversed(vars_in_category):
                option_names = _build_option_names(var)
                option_kwargs = _build_option_kwargs(var)
                decorated = option_group.option(*option_names, **option_kwargs)(decorated)

        return decorated  # type: ignore[return-value]

    return decorator


__all__ = ["configvar_options", "get_click_type"]
