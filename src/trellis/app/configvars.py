"""ConfigVar system for declarative configuration with CLI > ENV > default resolution.

This module provides a type-safe configuration variable system that resolves values
from multiple sources in priority order:
1. CLI arguments (highest priority)
2. Environment variables
3. Constructor values (passed to Config())
4. Default values (lowest priority)

Usage:
    from trellis.app.configvars import ConfigVar, cli_context

    # Define a config var
    _PORT = ConfigVar("port", default=8000, category="server")

    # In CLI command, set context before loading config
    with cli_context({"port": 9000}):
        config = load_config()  # port will be 9000

    # Or via ENV
    # TRELLIS_SERVER_PORT=8080 trellis run
"""

from __future__ import annotations

import os
from collections.abc import Callable
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Generic, TypeVar, cast, get_args, get_origin

from trellis.utils.debug import DEBUG_CATEGORIES

T = TypeVar("T")

# Module-level registry of all ConfigVars
_configvar_registry: list[ConfigVar[Any]] = []

# Constants for validation bounds
MAX_PORT = 65535
MIN_BATCH_DELAY = 0.001
MAX_BATCH_DELAY = 10.0
WINDOW_SIZE_PARTS_COUNT = 2

# Context variable to hold CLI arguments
_cli_context: ContextVar[dict[str, Any] | None] = ContextVar("cli_context", default=None)


@contextmanager
def cli_context(args: dict[str, Any]) -> Any:
    """Set CLI arguments for ConfigVar resolution within this context.

    Args:
        args: Dictionary mapping config var names to their CLI values.
              None values are ignored (fall through to next source).

    Example:
        with cli_context({"port": 8080, "host": "0.0.0.0"}):
            apploader = AppLoader(app_path)
            apploader.load_config()  # Config will use CLI values
    """
    token = _cli_context.set(args)
    try:
        yield
    finally:
        _cli_context.reset(token)


def get_cli_args() -> dict[str, Any]:
    """Get the current CLI arguments from context."""
    return _cli_context.get() or {}


@dataclass
class ConfigVar(Generic[T]):
    """A configuration variable that resolves from CLI > ENV > constructor > default.

    Type Parameters:
        T: The type of the configuration value

    Attributes:
        name: Variable name (used for CLI arg name and ENV var suffix)
        default: Default value when no other source provides a value
        category: Optional category prefix for ENV var (e.g., "server" -> TRELLIS_SERVER_*)
        env_name: Override the auto-generated ENV var name
        help: Help text for CLI option
        validator: Optional function to validate/transform the resolved value
        type_hint: Explicit type hint for coercion when default is None
        short_name: Single character for short CLI option (e.g., "d" for -d)
        is_flag: If True, option is a flag (--watch). If False with bool type,
                 uses --option/--no-option pattern.
    """

    name: str
    default: T
    category: str = ""
    env_name: str | None = None
    help: str = ""
    validator: Callable[[T], T] | None = None
    type_hint: type | None = None
    short_name: str | None = None
    is_flag: bool = False
    hidden: bool = False

    def __post_init__(self) -> None:
        """Register this ConfigVar in the module-level registry."""
        _configvar_registry.append(self)

    def get_env_name(self) -> str:
        """Get the environment variable name for this config var.

        Returns:
            TRELLIS_{NAME} or TRELLIS_{CATEGORY}_{NAME} in uppercase
        """
        if self.env_name:
            return self.env_name

        parts = ["TRELLIS"]
        if self.category:
            parts.append(self.category.upper())
        parts.append(self.name.upper())
        return "_".join(parts)

    def get_cli_name(self) -> str:
        """Get the CLI option name for this config var.

        Returns:
            --{name} with underscores replaced by hyphens
        """
        return f"--{self.name.replace('_', '-')}"

    def get_cli_short_name(self) -> str | None:
        """Get the short CLI option name for this config var.

        Returns:
            -{short_name} if short_name is set, None otherwise
        """
        if self.short_name is None:
            return None
        return f"-{self.short_name}"

    def _get_target_type(self) -> type | None:
        """Get the target type for coercion."""
        if self.type_hint is not None:
            return self.type_hint

        # Infer from default value type
        if self.default is not None:
            return type(self.default)
        return None

    def _coerce(self, value: str, target_type: type | None = None) -> T:  # noqa: PLR0911
        """Coerce a string value to the target type.

        Args:
            value: String value (already stripped) from ENV
            target_type: Explicit type to coerce to. If None, inferred from
                         type_hint or default value.

        Returns:
            Value coerced to target type T

        Raises:
            ValueError: If coercion fails
        """
        if target_type is None:
            target_type = self._get_target_type()

        # Handle None type or unknown - return string as-is
        if target_type is None:
            return value  # type: ignore

        # Handle Union types (e.g., int | None, Path | None)
        origin = get_origin(target_type)
        if origin is type(int | None):  # UnionType
            # Get non-None types from union
            args = [a for a in get_args(target_type) if a is not type(None)]
            if args:
                target_type = args[0]
                origin = get_origin(target_type)

        # Handle list types (e.g., list[Path], list[str])
        if origin is list:
            type_args = get_args(target_type)
            element_type = type_args[0] if type_args else str
            elements = [elem.strip() for elem in value.split(",")]
            return [self._coerce(elem, element_type) for elem in elements]  # type: ignore

        # String - return as-is
        if target_type is str:
            return value  # type: ignore

        # Integer
        if target_type is int:
            return int(value)  # type: ignore

        # Float
        if target_type is float:
            return float(value)  # type: ignore

        # Boolean
        if target_type is bool:
            lower = value.lower()
            if lower in ("true", "1", "yes"):
                return True  # type: ignore
            if lower in ("false", "0", "no"):
                return False  # type: ignore
            raise ValueError(f"Cannot convert '{value}' to bool")

        # Path
        if target_type is Path or (isinstance(target_type, type) and issubclass(target_type, Path)):
            return Path(value).expanduser()  # type: ignore

        # StrEnum - case insensitive lookup by value or name
        if isinstance(target_type, type) and issubclass(target_type, StrEnum):
            lower_value = value.lower()
            for member in target_type:
                if member.value.lower() == lower_value or member.name.lower() == lower_value:
                    return member  # type: ignore
            raise ValueError(f"'{value}' is not a valid {target_type.__name__}")

        # Fallback - try calling the type directly
        return target_type(value)  # type: ignore

    def resolve(self, constructor_value: T | None = None) -> T:
        """Resolve the configuration value from all sources.

        Resolution priority (highest to lowest):
        1. CLI arguments (from cli_context)
        2. Environment variables
        3. Constructor value (passed as argument)
        4. Default value

        Args:
            constructor_value: Optional value passed to Config() constructor

        Returns:
            The resolved configuration value

        Raises:
            ValueError: If coercion or validation fails
        """
        value: T | None = None

        # 1. CLI context (highest priority)
        cli_args = get_cli_args()
        cli_value = cli_args.get(self.name)
        if cli_value is not None:
            value = self._coerce_input_value(cli_value)
        else:
            # 2. Environment variable
            env_str = os.environ.get(self.get_env_name())
            if env_str is not None:
                # Strip whitespace
                env_str = env_str.strip()
                # Empty string treated as unset
                if env_str:
                    value = self._coerce(env_str)

        # 3. Constructor value (if not set from CLI or ENV)
        if value is None and constructor_value is not None:
            value = self._coerce_input_value(constructor_value)

        # 4. Default (if nothing else set)
        if value is None:
            value = self.default

        # Apply validator if present and value is not None
        if self.validator is not None and value is not None:
            value = self.validator(value)

        # Value could be the default (type T), so this is safe
        return value

    def _coerce_input_value(self, value: Any) -> T:
        """Coerce CLI/constructor values using this ConfigVar's target type when needed."""
        target_type = self._get_target_type()
        if target_type is None:
            return cast("T", value)

        if isinstance(value, str):
            return self._coerce(value, target_type)

        origin = get_origin(target_type)
        if origin is type(int | None):
            args = [a for a in get_args(target_type) if a is not type(None)]
            if args:
                target_type = args[0]
                origin = get_origin(target_type)

        if origin is list and isinstance(value, list):
            type_args = get_args(target_type)
            element_type = type_args[0] if type_args else str
            return cast(
                "T",
                [
                    self._coerce(item, element_type) if isinstance(item, str) else item
                    for item in value
                ],
            )

        return cast("T", value)


# ============================================================================
# Validators
# ============================================================================


def validate_port_or_none(port: int | None) -> int | None:
    """Validate that a port is in the valid range 1-65535, or None.

    Args:
        port: Port number or None

    Returns:
        The port number unchanged

    Raises:
        ValueError: If port is outside valid range
    """
    if port is None:
        return None
    if port < 1 or port > MAX_PORT:
        raise ValueError(f"Port must be 1-{MAX_PORT}, got {port}")
    return port


def validate_positive_int(value: int) -> int:
    """Validate that a value is a positive integer (> 0).

    Args:
        value: Integer value

    Returns:
        The value unchanged

    Raises:
        ValueError: If value is not positive
    """
    if value <= 0:
        raise ValueError(f"Value must be positive, got {value}")
    return value


def validate_positive_float(value: float) -> float:
    """Validate that a value is a positive float (> 0).

    Args:
        value: Float value

    Returns:
        The value unchanged

    Raises:
        ValueError: If value is not positive
    """
    if value <= 0:
        raise ValueError(f"Value must be positive, got {value}")
    return value


def validate_batch_delay(value: float) -> float:
    """Validate that batch_delay is within acceptable bounds.

    Args:
        value: Batch delay in seconds

    Returns:
        The value unchanged

    Raises:
        ValueError: If value is outside 0.001-10.0 range
    """
    if value < MIN_BATCH_DELAY or value > MAX_BATCH_DELAY:
        raise ValueError(f"batch_delay must be {MIN_BATCH_DELAY}-{MAX_BATCH_DELAY}, got {value}")
    return value


def validate_window_size(value: str) -> str:
    """Validate and normalize window size string.

    Accepts either "maximized" (case-insensitive) or "WIDTHxHEIGHT" format.

    Args:
        value: Window size string

    Returns:
        Normalized window size ("maximized" or "WxH")

    Raises:
        ValueError: If format is invalid or dimensions are not positive
    """
    stripped = value.strip().lower()

    if stripped == "maximized":
        return "maximized"

    # Try WxH format
    parts = stripped.replace(" ", "").split("x")
    if len(parts) != WINDOW_SIZE_PARTS_COUNT:
        raise ValueError(
            f"Invalid window size '{value}': must be 'maximized' or 'WIDTHxHEIGHT' (e.g., '1024x768')"
        )

    try:
        width = int(parts[0])
        height = int(parts[1])
    except ValueError as e:
        raise ValueError(
            f"Invalid window size '{value}': must be 'maximized' or 'WIDTHxHEIGHT' (e.g., '1024x768')"
        ) from e

    if width <= 0:
        raise ValueError(f"Window width must be positive, got {width}")
    if height <= 0:
        raise ValueError(f"Window height must be positive, got {height}")

    return f"{width}x{height}"


def get_config_vars() -> list[ConfigVar[Any]]:
    """Return all registered ConfigVars.

    Returns:
        A copy of the registry list (modifications do not affect the original).
    """
    return list(_configvar_registry)


def coerce_value(field_name: str, value: str) -> Any:
    """Coerce a string value using the ConfigVar registry.

    Args:
        field_name: The name of the ConfigVar field
        value: String value to coerce

    Returns:
        Value coerced to the ConfigVar's target type

    Raises:
        KeyError: If no ConfigVar is registered for the field name
    """
    for cv in _configvar_registry:
        if cv.name == field_name:
            return cv._coerce(value)
    raise KeyError(f"No ConfigVar registered for field: {field_name}")


def validate_debug_categories(value: str) -> str:
    """Validate and normalize debug category string.

    Strips whitespace, removes duplicates, and validates category names.

    Args:
        value: Comma-separated category names (e.g., "render,state")

    Returns:
        Normalized category string (stripped, deduplicated)

    Raises:
        ValueError: If an unknown category is specified
    """
    if not value:
        return ""

    # Split, strip, and deduplicate
    categories = []
    seen: set[str] = set()
    for raw_cat in value.split(","):
        cat = raw_cat.strip().lower()
        if cat and cat not in seen:
            categories.append(cat)
            seen.add(cat)

    # "all" is a special value that's always valid
    if "all" in categories:
        return ",".join(categories)

    # Validate each category
    unknown = [c for c in categories if c not in DEBUG_CATEGORIES]
    if unknown:
        raise ValueError(f"Unknown debug categories: {', '.join(unknown)}")

    return ",".join(categories)


__all__ = [
    "ConfigVar",
    "cli_context",
    "coerce_value",
    "get_cli_args",
    "get_config_vars",
    "validate_batch_delay",
    "validate_debug_categories",
    "validate_port_or_none",
    "validate_positive_float",
    "validate_positive_int",
    "validate_window_size",
]
