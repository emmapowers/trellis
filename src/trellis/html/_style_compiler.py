"""Compile structured Trellis styles into inline declarations and CSS rules."""

from __future__ import annotations

import re
import typing as tp
from collections.abc import Mapping

from trellis.html._css_primitives import (
    CssAngle,
    CssColor,
    CssLength,
    CssPercent,
    CssRawString,
    CssTime,
)
from trellis.html._css_primitives import format_number as _format_number
from trellis.html._generated_style_metadata import AUTO_PX_FIELDS, CSS_NAME_BY_FIELD
from trellis.html._style_runtime import Css, CssClass, MediaRule

StyleDict = dict[str, tp.Any]

_CAMEL_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")
_CSS_NAME_BY_FIELD_REVERSED = {
    css_name: field_name for field_name, css_name in CSS_NAME_BY_FIELD.items()
}


def compile_style_props(props: dict[str, tp.Any]) -> dict[str, tp.Any]:
    """Compile a Css object or raw dict in the ``style`` prop to inline CSS."""

    style_input = props.get("style")
    if style_input is None:
        return dict(props)

    inline = _compile_inline(style_input)
    result = dict(props)
    result["style"] = inline
    return result


def compile_css_class(css_class: CssClass) -> str:
    """Compile a CssClass into a CSS rule block string."""
    selector = f".{css_class.class_name}"
    parts: list[str] = []

    # Base rule (plain CSS properties on the class itself)
    base_inline = _compile_css_props(css_class.props, css_class.vars)
    if base_inline:
        declarations = "".join(f"{name}:{_css_text(value)};" for name, value in base_inline.items())
        parts.append(f"{selector}{{{declarations}}}")

    # Selector rules (hover, focus, etc.)
    for child_selector, nested_style in css_class.selectors.items():
        nested_inline = _compile_inline(nested_style)
        if nested_inline:
            resolved = _resolve_selector(selector, child_selector)
            declarations = "".join(
                f"{name}:{_css_text(value)};" for name, value in nested_inline.items()
            )
            parts.append(f"{resolved}{{{declarations}}}")

    # Media rules
    for rule in css_class.media:
        query = _media_query(rule)
        nested_inline = _compile_inline(rule.style)
        if nested_inline:
            declarations = "".join(
                f"{name}:{_css_text(value)};" for name, value in nested_inline.items()
            )
            parts.append(f"@media {query}{{{selector}{{{declarations}}}}}")

    return "\n".join(parts)


def merge_style_inputs(
    base_style: tp.Any,
    overlay_style: tp.Any,
) -> Mapping[str, tp.Any] | None:
    base_mapping = _style_input_to_mapping(base_style)
    overlay_mapping = _style_input_to_mapping(overlay_style)

    if not base_mapping and not overlay_mapping:
        return None

    return _deep_merge_style_mappings(base_mapping, overlay_mapping)


def _deep_merge_style_mappings(
    base_mapping: Mapping[str, tp.Any],
    overlay_mapping: Mapping[str, tp.Any],
) -> dict[str, tp.Any]:
    merged = dict(base_mapping)
    for key, overlay_value in overlay_mapping.items():
        base_value = merged.get(key)
        if isinstance(base_value, Mapping) and isinstance(overlay_value, Mapping):
            merged[key] = _deep_merge_style_mappings(base_value, overlay_value)
            continue
        merged[key] = overlay_value
    return merged


def _compile_inline(style_input: tp.Any) -> StyleDict:
    """Compile a Css object or raw mapping to a flat CSS property dict."""
    if style_input is None:
        return {}

    if isinstance(style_input, Mapping):
        style = Css(style_input)
    elif isinstance(style_input, Css):
        style = style_input
    else:
        raise TypeError(f"Unsupported style value: {style_input!r}")

    return _compile_css_props(style.props, style.vars)


def _compile_css_props(props: dict[str, tp.Any], vars: dict[str, tp.Any]) -> StyleDict:
    """Compile props and vars into a flat CSS property dict."""
    inline: StyleDict = {}
    for name, value in props.items():
        css_name = _normalize_css_name(name)
        inline[css_name] = _serialize_value(value, auto_px=_should_auto_px(name, css_name))

    for key, raw_value in vars.items():
        inline[key if key.startswith("--") else f"--{key}"] = _serialize_value(
            raw_value, auto_px=False
        )
    return inline


def _style_input_to_mapping(style_input: tp.Any) -> dict[str, tp.Any]:
    return dict(_compile_inline(style_input))


def _normalize_css_name(name: str) -> str:
    if name.startswith("--"):
        return name
    if name in CSS_NAME_BY_FIELD:
        return CSS_NAME_BY_FIELD[name]
    if "-" in name:
        normalized = name.lower()
    elif "_" in name:
        normalized = name.replace("_", "-").lower()
    else:
        normalized = _CAMEL_BOUNDARY.sub("-", name).lower()

    for prefix in ("webkit-", "moz-", "ms-", "o-"):
        if normalized.startswith(prefix):
            return f"-{normalized}"
    return normalized


def _should_auto_px(source_name: str, css_name: str) -> bool:
    if source_name in AUTO_PX_FIELDS:
        return True
    normalized_field_name = _CSS_NAME_BY_FIELD_REVERSED.get(css_name)
    return normalized_field_name in AUTO_PX_FIELDS


def _serialize_value(value: tp.Any, *, auto_px: bool) -> str | int | float:
    if isinstance(value, (CssRawString, CssLength, CssPercent, CssTime, CssAngle, CssColor)):
        return value.css_text
    if isinstance(value, (int, float)):
        if auto_px:
            return f"{_format_number(value)}px"
        return value
    return str(value)


def _media_query(rule: MediaRule) -> str:
    parts: list[str] = []
    if rule.query:
        parts.append(rule.query)
    for name, value in rule.features.items():
        css_name = _normalize_css_name(name)
        serialized = _serialize_value(value, auto_px=_is_auto_px_media_feature(css_name))
        parts.append(f"({css_name}: {serialized})")
    if not parts:
        raise ValueError("MediaRule must define `query` or at least one media feature")
    return " and ".join(parts)


def _is_auto_px_media_feature(css_name: str) -> bool:
    return "width" in css_name or "height" in css_name


def _resolve_selector(base_selector: str, selector: str) -> str:
    if "&" in selector:
        return selector.replace("&", base_selector)
    if selector.startswith(":"):
        return f"{base_selector}{selector}"
    return f"{base_selector} {selector}"


def _css_text(value: str | int | float) -> str:
    return str(value)
