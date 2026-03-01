"""Icon asset generation with real format conversion.

Converts a single source icon (PNG or SVG) into web and desktop icon formats:
- favicon.ico (multi-size ICO)
- favicon.png (32x32)
- apple-touch-icon.png (180x180)
- favicon.icns (macOS, optional)
"""

from __future__ import annotations

import io
import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import resvg_py
from PIL import Image

logger = logging.getLogger(__name__)

FAVICON_ICO_SIZES = (16, 32, 48, 256)
FAVICON_PNG_SIZE = 32
APPLE_TOUCH_ICON_SIZE = 180
ICNS_SIZES = (16, 32, 64, 128, 256, 512, 1024)

MIN_RECOMMENDED_SIZE = 1024
SUPPORTED_EXTENSIONS = {".png", ".svg"}
MIN_ICNS_RETINA_SIZE = 16

_ICO_MIME_TYPE = "image/x-icon"


@dataclass(frozen=True)
class IconAssetResult:
    """Result of deriving web icon artifacts from a single source icon."""

    has_icon: bool
    favicon_href: str | None = None
    favicon_type: str | None = None
    apple_touch_icon_href: str | None = None
    generated_files: tuple[Path, ...] = ()


def _rasterize_svg(svg_path: Path, size: int) -> Image.Image:
    """Render an SVG file to a PIL Image at the given pixel size."""
    png_data = resvg_py.svg_to_bytes(svg_path=str(svg_path), width=size, height=size)
    return Image.open(io.BytesIO(png_data)).convert("RGBA")


def _load_source_icon(icon_path: Path) -> Image.Image:
    """Load a source icon as a PIL Image at maximum resolution.

    PNG sources are loaded directly; SVG sources are rasterized at 1024x1024.
    Warns if PNG source is smaller than 1024x1024.
    """
    ext = icon_path.suffix.lower()
    if ext == ".svg":
        return _rasterize_svg(icon_path, MIN_RECOMMENDED_SIZE)

    img = Image.open(icon_path).convert("RGBA")
    if img.width < MIN_RECOMMENDED_SIZE or img.height < MIN_RECOMMENDED_SIZE:
        logger.warning(
            "Source icon %s is %dx%d; recommend at least %dx%d for best results",
            icon_path.name,
            img.width,
            img.height,
            MIN_RECOMMENDED_SIZE,
            MIN_RECOMMENDED_SIZE,
        )
    return img


def _resize(source: Image.Image, size: int) -> Image.Image:
    """Downsample to size x size using LANCZOS resampling."""
    return source.resize((size, size), Image.Resampling.LANCZOS)


def _generate_ico(source: Image.Image, sizes: tuple[int, ...], output: Path) -> None:
    """Generate a multi-size ICO file."""
    images = [_resize(source, s) for s in sizes]
    images[0].save(
        str(output), format="ICO", sizes=[(s, s) for s in sizes], append_images=images[1:]
    )


def _generate_icns(source: Image.Image, sizes: tuple[int, ...], output: Path) -> None:
    """Generate a macOS ICNS file using iconutil.

    Creates a temporary .iconset directory with properly named PNG files,
    then runs iconutil to produce the .icns bundle.
    """
    iconset_dir = output.with_suffix(".iconset")
    iconset_dir.mkdir(parents=True, exist_ok=True)

    try:
        for size in sizes:
            icon = _resize(source, size)
            # Standard resolution
            name = f"icon_{size}x{size}.png"
            icon.save(str(iconset_dir / name), format="PNG")
            # @2x retina (half the pixel size label, double density)
            half = size // 2
            if half >= MIN_ICNS_RETINA_SIZE:
                retina_name = f"icon_{half}x{half}@2x.png"
                icon.save(str(iconset_dir / retina_name), format="PNG")

        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(output)],
            check=True,
            capture_output=True,
        )
    finally:
        shutil.rmtree(iconset_dir, ignore_errors=True)


def generate_icon_assets(
    icon_path: Path | None,
    dist_dir: Path,
    *,
    include_icns: bool = False,
) -> IconAssetResult:
    """Generate icon files in ``dist_dir`` from a single source icon file.

    Accepts .png or .svg source icons. Generates:
    - favicon.ico (multi-size: 16, 32, 48, 256)
    - favicon.png (32x32)
    - apple-touch-icon.png (180x180)
    - favicon.icns (macOS, only when include_icns=True)
    """
    if icon_path is None:
        return IconAssetResult(has_icon=False)
    if not icon_path.exists() or not icon_path.is_file():
        raise FileNotFoundError(f"Icon file not found: {icon_path}")

    extension = icon_path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported icon format '{extension}'; expected one of: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    if dist_dir.exists() and not dist_dir.is_dir():
        raise NotADirectoryError(f"Icon output path is not a directory: {dist_dir}")
    dist_dir.mkdir(parents=True, exist_ok=True)

    source = _load_source_icon(icon_path)
    generated_files: list[Path] = []

    # favicon.ico (multi-size)
    ico_path = dist_dir / "favicon.ico"
    _generate_ico(source, FAVICON_ICO_SIZES, ico_path)
    generated_files.append(ico_path)

    # favicon.png (32x32)
    favicon_png_path = dist_dir / "favicon.png"
    _resize(source, FAVICON_PNG_SIZE).save(str(favicon_png_path), format="PNG")
    generated_files.append(favicon_png_path)

    # apple-touch-icon.png (180x180)
    apple_path = dist_dir / "apple-touch-icon.png"
    _resize(source, APPLE_TOUCH_ICON_SIZE).save(str(apple_path), format="PNG")
    generated_files.append(apple_path)

    # favicon.icns (macOS)
    if include_icns:
        icns_path = dist_dir / "favicon.icns"
        _generate_icns(source, ICNS_SIZES, icns_path)
        generated_files.append(icns_path)

    return IconAssetResult(
        has_icon=True,
        favicon_href="favicon.ico",
        favicon_type=_ICO_MIME_TYPE,
        apple_touch_icon_href="apple-touch-icon.png",
        generated_files=tuple(generated_files),
    )
