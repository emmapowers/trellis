"""Compile structured Trellis styles into inline declarations and CSS rules."""

from __future__ import annotations

import hashlib
import json
import re
import typing as tp
from collections.abc import Mapping

from trellis.html._css_primitives import CssValue
from trellis.html._css_primitives import format_number as _format_number
from trellis.html._generated_style_metadata import AUTO_PX_FIELDS, CSS_NAME_BY_FIELD
from trellis.html._style_runtime import MediaRule, Style

StyleDict = dict[str, tp.Any]
CompiledStyle = tuple[StyleDict, str | None, str | None]

_CAMEL_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")
_CSS_NAME_BY_FIELD_REVERSED = {
    css_name: field_name for field_name, css_name in CSS_NAME_BY_FIELD.items()
}


def compile_style_props(props: dict[str, tp.Any]) -> dict[str, tp.Any]:
    style_input = props.get("style")
    if style_input is None:
        return dict(props)

    inline, class_name, style_rules = compile_style(style_input)
    result = dict(props)
    result["style"] = inline
    if class_name is not None:
        existing_class_name = result.get("class_name")
        if isinstance(existing_class_name, str) and existing_class_name:
            result["class_name"] = f"{existing_class_name} {class_name}"
        else:
            result["class_name"] = class_name
    if style_rules is not None:
        result["_style_rules"] = style_rules
    return result


def compile_style(style_input: tp.Any) -> CompiledStyle:
    inline, nested_rules = _normalize_style(style_input)
    if not nested_rules:
        return inline, None, None

    canonical = json.dumps(
        {
            "inline": inline,
            "rules": nested_rules,
        },
        sort_keys=True,
    )
    class_name = f"tcss_{hashlib.sha1(canonical.encode('utf-8')).hexdigest()[:12]}"
    css_text = "\n".join(_emit_rule(rule, f".{class_name}") for rule in nested_rules)
    return inline, class_name, css_text


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


def _normalize_style(style_input: tp.Any) -> tuple[StyleDict, list[dict[str, tp.Any]]]:
    inline: StyleDict = {}
    nested_rules: list[dict[str, tp.Any]] = []

    if style_input is None:
        return inline, nested_rules

    if isinstance(style_input, Mapping):
        style = Style(style_input)
    elif isinstance(style_input, Style):
        style = style_input
    else:
        raise TypeError(f"Unsupported style value: {style_input!r}")

    _consume_style_object(style, inline, nested_rules)
    return inline, nested_rules


def _style_input_to_mapping(style_input: tp.Any) -> dict[str, tp.Any]:
    inline, nested_rules = _normalize_style(style_input)
    mapping = dict(inline)
    for rule in nested_rules:
        if "media" in rule:
            mapping[f"@media {rule['media']}"] = _nested_rule_to_mapping(rule)
        elif "selector" in rule:
            mapping[rule["selector"]] = _nested_rule_to_mapping(rule)
    return mapping


def _consume_style_object(
    style: Style,
    inline: StyleDict,
    nested_rules: list[dict[str, tp.Any]],
) -> None:
    for name, value in style.props.items():
        css_name = _normalize_css_name(name)
        inline[css_name] = _serialize_value(value, auto_px=_should_auto_px(name, css_name))

    for key, raw_value in style.vars.items():
        inline[key if key.startswith("--") else f"--{key}"] = _serialize_value(
            raw_value, auto_px=False
        )

    for selector, nested_style in style.selectors.items():
        nested_inline, nested_children = _normalize_style(nested_style)
        nested_rules.append(
            {"selector": selector, "inline": nested_inline, "children": nested_children}
        )

    for rule in style.media:
        query = _media_query(rule)
        nested_inline, nested_children = _normalize_style(rule.style)
        nested_rules.append({"media": query, "inline": nested_inline, "children": nested_children})


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
    if isinstance(value, CssValue):
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


def _emit_rule(rule: dict[str, tp.Any], base_selector: str) -> str:
    selector = rule.get("selector")
    media = rule.get("media")
    inline = rule.get("inline", {})
    children = rule.get("children", [])

    if selector is not None:
        selector_text = _resolve_selector(base_selector, selector)
        body = _emit_rule_block(selector_text, inline, children)
    else:
        body = _emit_rule_block(base_selector, inline, children)

    if media is not None:
        return f"@media {media} {{{body}}}"
    return body


def _emit_rule_block(selector: str, inline: StyleDict, children: list[dict[str, tp.Any]]) -> str:
    declarations = "".join(f"{name}:{_css_text(value)};" for name, value in inline.items())
    child_css = "".join(_emit_rule(child, selector) for child in children)
    if not declarations:
        return child_css
    return f"{selector}{{{declarations}}}{child_css}"


def _resolve_selector(base_selector: str, selector: str) -> str:
    if "&" in selector:
        return selector.replace("&", base_selector)
    if selector.startswith(":"):
        return f"{base_selector}{selector}"
    return f"{base_selector} {selector}"


def _css_text(value: str | int | float) -> str:
    return str(value)


def _nested_rule_to_mapping(rule: dict[str, tp.Any]) -> dict[str, tp.Any]:
    mapping = dict(rule.get("inline", {}))
    for child in rule.get("children", []):
        if "media" in child:
            mapping[f"@media {child['media']}"] = _nested_rule_to_mapping(child)
        elif "selector" in child:
            mapping[child["selector"]] = _nested_rule_to_mapping(child)
    return mapping
