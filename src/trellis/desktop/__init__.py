"""Desktop-only APIs for Trellis applications."""

from trellis.desktop.dialogs import (
    FileDialogFilter,
    FileDialogOptions,
    open_file,
    open_files,
    save_file,
    select_directory,
)

__all__ = [
    "FileDialogFilter",
    "FileDialogOptions",
    "open_file",
    "open_files",
    "save_file",
    "select_directory",
]
