"""Icon asset generation helpers for the bundler."""

from __future__ import annotations

import mimetypes
import shutil
from dataclasses import dataclass
from pathlib import Path

_ICO_MIME_TYPE = "image/x-icon"


@dataclass(frozen=True)
class IconAssetResult:
    """Result of deriving web icon artifacts from a single source icon."""

    has_icon: bool
    favicon_href: str | None = None
    favicon_type: str | None = None
    apple_touch_icon_href: str | None = None
    generated_files: tuple[Path, ...] = ()


def _mime_for_icon_extension(extension: str) -> str:
    """Return MIME type for an icon file extension."""
    if extension == ".ico":
        return _ICO_MIME_TYPE
    return mimetypes.types_map.get(extension, "application/octet-stream")


def generate_icon_assets(icon_path: Path | None, dist_dir: Path) -> IconAssetResult:
    """Generate icon files in ``dist_dir`` from a single source icon file.

    This intentionally keeps derivation simple: copy the source to canonical
    output filenames used by templates and packaging.
    """
    if icon_path is None:
        return IconAssetResult(has_icon=False)
    if not icon_path.exists() or not icon_path.is_file():
        raise FileNotFoundError(f"Icon file not found: {icon_path}")

    extension = icon_path.suffix.lower()
    if not extension:
        raise ValueError("Icon file must have an extension")

    generated_files: list[Path] = []
    favicon_name = f"favicon{extension}"
    favicon_output = dist_dir / favicon_name
    shutil.copy2(icon_path, favicon_output)
    generated_files.append(favicon_output)

    apple_touch_icon_href: str | None = None
    if extension == ".png":
        apple_name = "apple-touch-icon.png"
        apple_output = dist_dir / apple_name
        if apple_output != favicon_output:
            shutil.copy2(icon_path, apple_output)
            generated_files.append(apple_output)
        apple_touch_icon_href = apple_name

    return IconAssetResult(
        has_icon=True,
        favicon_href=favicon_name,
        favicon_type=_mime_for_icon_extension(extension),
        apple_touch_icon_href=apple_touch_icon_href,
        generated_files=tuple(generated_files),
    )
