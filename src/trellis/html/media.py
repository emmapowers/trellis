"""Media and embed HTML elements.

Elements for video, audio, and embedded content.
"""

from __future__ import annotations

import typing as tp

from trellis.core.rendering.element import Element
from trellis.html.base import Style, html_element

__all__ = [
    "Audio",
    "Iframe",
    "Source",
    "Video",
]


@html_element("video", is_container=True)
def Video(
    *,
    src: str | None = None,
    controls: bool = False,
    autoPlay: bool = False,
    loop: bool = False,
    muted: bool = False,
    width: int | str | None = None,
    height: int | str | None = None,
    poster: str | None = None,
    preload: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A video element."""
    ...


@html_element("audio", is_container=True)
def Audio(
    *,
    src: str | None = None,
    controls: bool = False,
    autoPlay: bool = False,
    loop: bool = False,
    muted: bool = False,
    preload: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """An audio element."""
    ...


@html_element("source")
def Source(
    *,
    src: str | None = None,
    type: str | None = None,
    srcSet: str | None = None,
    sizes: str | None = None,
    media: str | None = None,
    **props: tp.Any,
) -> Element:
    """A media source element for use within Video or Audio."""
    ...


@html_element("iframe")
def Iframe(
    *,
    src: str | None = None,
    title: str | None = None,
    width: int | str | None = None,
    height: int | str | None = None,
    allow: str | None = None,
    sandbox: str | None = None,
    loading: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """An inline frame element."""
    ...
