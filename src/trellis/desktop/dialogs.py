"""Desktop-native async file dialogs.

This module exposes desktop-only async helpers for common file dialog flows.
Calls must happen while running in the Trellis desktop runtime.
"""

from __future__ import annotations

import asyncio
import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

    from pytauri import ImplManager

_DIALOG_RUNTIME_UNAVAILABLE = (
    "Desktop dialogs are only available while running in a desktop runtime. "
    "Use these APIs from desktop callbacks or desktop tasks."
)


@dataclass(frozen=True, slots=True)
class FileDialogFilter:
    """A single file-extension filter for dialog selection."""

    name: str
    extensions: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("FileDialogFilter.name cannot be empty")
        if not self.extensions:
            raise ValueError("FileDialogFilter.extensions cannot be empty")


@dataclass(frozen=True, slots=True)
class FileDialogOptions:
    """Options shared by open/save/select file dialogs."""

    title: str | None = None
    directory: Path | str | None = None
    file_name: str | None = None
    filter: FileDialogFilter | None = None
    can_create_directories: bool | None = None


_dialog_manager: ImplManager | None = None
_DialogResult = TypeVar("_DialogResult")


def _set_dialog_runtime(manager: ImplManager) -> None:
    """Install desktop runtime manager for dialog operations."""
    global _dialog_manager
    _dialog_manager = manager


def _clear_dialog_runtime() -> None:
    """Clear desktop runtime manager when desktop app disconnects."""
    global _dialog_manager
    _dialog_manager = None


def _require_dialog_manager() -> ImplManager:
    if _dialog_manager is None:
        raise RuntimeError(_DIALOG_RUNTIME_UNAVAILABLE)
    return _dialog_manager


def _load_dialog_ext() -> Any:
    try:
        dialog_module = importlib.import_module("pytauri_plugins.dialog")
        return dialog_module.DialogExt
    except (ModuleNotFoundError, AttributeError) as exc:
        raise RuntimeError(
            "Desktop dialog plugin is unavailable. Ensure pytauri dialog support is installed."
        ) from exc


def _build_dialog_kwargs(options: FileDialogOptions) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    if options.title is not None:
        kwargs["set_title"] = options.title
    if options.directory is not None:
        kwargs["set_directory"] = Path(options.directory)
    if options.file_name is not None:
        kwargs["set_file_name"] = options.file_name
    if options.filter is not None:
        kwargs["add_filter"] = (options.filter.name, options.filter.extensions)
    if options.can_create_directories is not None:
        kwargs["set_can_create_directories"] = options.can_create_directories
    return kwargs


def _to_path(raw: Any) -> Path:
    if isinstance(raw, Path):
        return raw
    return Path(str(raw))


async def _call_dialog(
    method_name: str,
    *,
    options: FileDialogOptions,
    normalize: Callable[[Any], _DialogResult],
) -> _DialogResult:
    manager = _require_dialog_manager()
    dialog_ext = _load_dialog_ext()
    builder = dialog_ext.file(manager)
    kwargs = _build_dialog_kwargs(options)
    method = getattr(builder, method_name)

    loop = asyncio.get_running_loop()
    future: asyncio.Future[_DialogResult] = loop.create_future()

    def _set_result(value: _DialogResult) -> None:
        if not future.done():
            future.set_result(value)

    def _set_exception(error: Exception) -> None:
        if not future.done():
            future.set_exception(error)

    def _resolve(result: Any) -> None:
        try:
            normalized_result = normalize(result)
        except Exception as error:
            loop.call_soon_threadsafe(_set_exception, error)
            return
        loop.call_soon_threadsafe(_set_result, normalized_result)

    method(_resolve, **kwargs)
    return await future


def _normalize_optional_path(result: Any) -> Path | None:
    if result is None:
        return None
    return _to_path(result)


def _normalize_path_list(result: Any) -> list[Path]:
    if result is None:
        return []
    return [_to_path(value) for value in result]


async def open_file(*, options: FileDialogOptions | None = None) -> Path | None:
    """Show native open-file dialog and return selected file path."""
    resolved_options = options or FileDialogOptions()
    return await _call_dialog(
        "pick_file",
        options=resolved_options,
        normalize=_normalize_optional_path,
    )


async def open_files(*, options: FileDialogOptions | None = None) -> list[Path]:
    """Show native multi-file open dialog and return selected paths."""
    resolved_options = options or FileDialogOptions()
    return await _call_dialog(
        "pick_files",
        options=resolved_options,
        normalize=_normalize_path_list,
    )


async def save_file(*, options: FileDialogOptions | None = None) -> Path | None:
    """Show native save-file dialog and return destination path."""
    resolved_options = options or FileDialogOptions()
    return await _call_dialog(
        "save_file",
        options=resolved_options,
        normalize=_normalize_optional_path,
    )


async def select_directory(*, options: FileDialogOptions | None = None) -> Path | None:
    """Show native directory picker dialog and return selected path."""
    resolved_options = options or FileDialogOptions()
    return await _call_dialog(
        "pick_folder",
        options=resolved_options,
        normalize=_normalize_optional_path,
    )


__all__ = [
    "FileDialogFilter",
    "FileDialogOptions",
    "open_file",
    "open_files",
    "save_file",
    "select_directory",
]
