"""Compile structured Trellis styles into inline declarations and CSS rules."""

from __future__ import annotations

import hashlib
import json
import typing as tp
from collections.abc import Mapping
from dataclasses import fields

from trellis.html._css_primitives import CssValue
from trellis.html._generated_style_metadata import AUTO_PX_FIELDS, CSS_NAME_BY_FIELD
from trellis.html._generated_style_types import MediaRule
from trellis.html._style_runtime import Style

StyleDict = dict[str, tp.Any]
CompiledStyle = tuple[StyleDict, str | None, str | None]
WidgetStyleField = tp.Literal[
    "margin", "padding", "width", "height", "flex", "text_align", "font_weight"
]

_PSEUDO_FIELDS = {
    "hover": ":hover",
    "focus": ":focus",
    "focus_visible": ":focus-visible",
    "focus_within": ":focus-within",
    "active": ":active",
    "visited": ":visited",
    "disabled": ":disabled",
    "checked": ":checked",
    "placeholder": "::placeholder",
    "before": "::before",
    "after": "::after",
    "selection": "::selection",
}

_CSS_NAME_BY_FIELD_REVERSED = {
    css_name: field_name for field_name, css_name in CSS_NAME_BY_FIELD.items()
}
_FONT_WEIGHT_KEYWORDS = {"normal": 400, "medium": 500, "semibold": 600, "bold": 700}


def merge_widget_style_props(
    props: dict[str, tp.Any],
    style_fields: frozenset[WidgetStyleField],
) -> dict[str, tp.Any]:
    result = dict(props)
    style_updates: dict[str, tp.Any] = {}

    for field_name in ("margin", "padding", "width", "height", "flex"):
        if field_name in style_fields and field_name in result:
            value = result.pop(field_name)
            if value is not None:
                style_updates[field_name] = value

    if "text_align" in style_fields and "text_align" in result:
        value = result.pop("text_align")
        if value is not None:
            style_updates["text_align"] = value

    if "font_weight" in style_fields and "font_weight" in result:
        value = result.pop("font_weight")
        if value is not None:
            if isinstance(value, str):
                value = _FONT_WEIGHT_KEYWORDS.get(value, value)
            style_updates["font_weight"] = value

    merged_style = result.pop("style", None)
    if style_updates:
        merged_style = merge_style_inputs(merged_style, Style(**style_updates))
    if merged_style is not None:
        result["style"] = merged_style
    return result


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

    merged = dict(base_mapping)
    merged.update(overlay_mapping)
    return merged


def _normalize_style(style_input: tp.Any) -> tuple[StyleDict, list[dict[str, tp.Any]]]:
    inline: StyleDict = {}
    nested_rules: list[dict[str, tp.Any]] = []

    if style_input is None:
        return inline, nested_rules

    if isinstance(style_input, Style):
        _consume_style_object(style_input, inline, nested_rules)
        return inline, nested_rules

    if isinstance(style_input, Mapping):
        _consume_raw_mapping(style_input, inline, nested_rules)
        return inline, nested_rules

    raise TypeError(f"Unsupported style value: {style_input!r}")


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
    style: Style, inline: StyleDict, nested_rules: list[dict[str, tp.Any]]
) -> None:
    for field in fields(style):
        value = getattr(style, field.name)
        if value is None:
            continue

        if field.name == "vars":
            for key, raw_value in value.items():
                inline[key] = _serialize_value(raw_value, auto_px=False)
            continue

        if field.name in _PSEUDO_FIELDS:
            nested_inline, nested_children = _normalize_style(value)
            nested_rules.append(
                {
                    "selector": _PSEUDO_FIELDS[field.name],
                    "inline": nested_inline,
                    "children": nested_children,
                }
            )
            continue

        if field.name == "media":
            if isinstance(value, Mapping):
                for query, nested_style in value.items():
                    media_query = query.removeprefix("@media ").strip()
                    nested_inline, nested_children = _normalize_style(nested_style)
                    nested_rules.append(
                        {"media": media_query, "inline": nested_inline, "children": nested_children}
                    )
            else:
                for rule in value:
                    query = _media_query(rule)
                    nested_inline, nested_children = _normalize_style(rule.style)
                    nested_rules.append(
                        {"media": query, "inline": nested_inline, "children": nested_children}
                    )
            continue

        if field.name == "selectors":
            for selector, nested_style in value.items():
                nested_inline, nested_children = _normalize_style(nested_style)
                nested_rules.append(
                    {"selector": selector, "inline": nested_inline, "children": nested_children}
                )
            continue

        css_name = CSS_NAME_BY_FIELD.get(field.name)
        if css_name is None:
            continue
        inline[css_name] = _serialize_value(value, auto_px=field.name in AUTO_PX_FIELDS)


def _consume_raw_mapping(
    style_mapping: Mapping[str, tp.Any],
    inline: StyleDict,
    nested_rules: list[dict[str, tp.Any]],
) -> None:
    for key, value in style_mapping.items():
        if key.startswith("@media "):
            nested_inline, nested_children = _normalize_style(value)
            nested_rules.append(
                {
                    "media": key.removeprefix("@media ").strip(),
                    "inline": nested_inline,
                    "children": nested_children,
                }
            )
            continue

        if key.startswith(":") or key.startswith("&"):
            nested_inline, nested_children = _normalize_style(value)
            nested_rules.append(
                {"selector": key, "inline": nested_inline, "children": nested_children}
            )
            continue

        auto_px = _CSS_NAME_BY_FIELD_REVERSED.get(key, "") in AUTO_PX_FIELDS
        inline[key] = _serialize_value(value, auto_px=auto_px)


def _serialize_value(value: tp.Any, *, auto_px: bool) -> str | int | float:
    if isinstance(value, CssValue):
        return value.css_text
    if isinstance(value, (int, float)):
        if auto_px:
            return f"{_format_number(value)}px"
        return value
    return str(value)


def _format_number(value: int | float) -> str:
    if isinstance(value, int):
        return str(value)
    if value.is_integer():
        return str(int(value))
    return format(value, "g")


def _media_query(rule: MediaRule) -> str:
    parts: list[str] = []
    if rule.query:
        parts.append(rule.query)
    for field_name in (
        "min_width",
        "max_width",
        "min_height",
        "max_height",
        "orientation",
        "hover",
        "pointer",
        "prefers_color_scheme",
        "prefers_reduced_motion",
    ):
        value = getattr(rule, field_name)
        if value is None:
            continue
        css_name = field_name.replace("_", "-")
        serialized = _serialize_value(
            value,
            auto_px=field_name in {"min_width", "max_width", "min_height", "max_height"},
        )
        parts.append(f"({css_name}: {serialized})")
    return " and ".join(parts)


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
