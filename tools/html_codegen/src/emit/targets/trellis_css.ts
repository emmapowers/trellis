import type {
  CssDocument,
  CssMediaFeatureDef,
  CssPropertyDef,
  CssValueAliasDef,
  TypeExpr,
} from "../../ir/types.js";
import { render_type_expr } from "../python/render_types.js";
import { render_generated_module_docstring } from "./generated_metadata.js";

import type { TrellisModulePayload } from "./trellis_html.js";

function sort_by_name<T extends { name?: string; python_name?: string }>(items: T[]): T[] {
  return [...items].sort((left, right) =>
    (left.name ?? left.python_name ?? "").localeCompare(right.name ?? right.python_name ?? ""),
  );
}

const CSS_ALIAS_PRIORITY = [
  "Length",
  "Percent",
  "LengthPercentage",
  "TimeValue",
  "AngleValue",
  "NamedColor",
  "ColorKeyword",
  "ColorValue",
  "Display",
  "Position",
  "Overflow",
  "TextAlign",
  "FontWeight",
  "FlexDirection",
  "FlexWrap",
  "JustifyContent",
  "AlignItems",
  "WidthValue",
  "HeightValue",
  "BorderRadiusValue",
  "SpacingShorthand",
  "GapValue",
  "LineHeightValue",
  "ShadowValue",
  "TransformValue",
  "TransitionValue",
  "Opacity",
  "ZIndex",
  "MediaFeatureValue",
  "Orientation",
  "PrefersColorScheme",
  "PrefersReducedMotion",
  "PointerCapability",
  "HoverCapability",
] as const;

const CSS_VALUE_CAPABLE_ALIASES = new Set([
  "WidthValue",
  "HeightValue",
  "BorderRadiusValue",
  "SpacingShorthand",
  "GapValue",
  "LineHeightValue",
  "ShadowValue",
  "TransformValue",
  "TransitionValue",
]);

function emit_aliases(aliases: CssValueAliasDef[]): string[] {
  const priority = new Map<string, number>(CSS_ALIAS_PRIORITY.map((name, index) => [name, index]));
  const lines: string[] = [];
  const ordered_aliases = [...aliases].sort((left, right) => {
    const left_priority = priority.get(left.name) ?? Number.MAX_SAFE_INTEGER;
    const right_priority = priority.get(right.name) ?? Number.MAX_SAFE_INTEGER;
    if (left_priority !== right_priority) {
      return left_priority - right_priority;
    }
    return left.name.localeCompare(right.name);
  });
  for (const alias of ordered_aliases) {
    lines.push(`${alias.name} = ${render_type_expr(alias.type_expr)}`);
  }
  return lines;
}

function flatten_union(type_expr: TypeExpr): TypeExpr[] {
  if (type_expr.kind === "union") {
    return type_expr.options.flatMap(flatten_union);
  }
  return [type_expr];
}

function append_type_expr(base: TypeExpr, addition: TypeExpr): TypeExpr {
  const options = [...flatten_union(base)];
  const rendered = new Set(options.map((option) => JSON.stringify(option)));
  const additions = flatten_union(addition);
  for (const option of additions) {
    const key = JSON.stringify(option);
    if (rendered.has(key)) {
      continue;
    }
    rendered.add(key);
    options.push(option);
  }

  if (options.length === 1) {
    return options[0]!;
  }
  return { kind: "union", options };
}

function qualify_field_primitives(type_expr: TypeExpr): TypeExpr {
  switch (type_expr.kind) {
    case "primitive":
      if (type_expr.name === "none") {
        return type_expr;
      }
      return { kind: "reference", name: `builtins.${type_expr.name}` };
    case "union":
      return {
        kind: "union",
        options: type_expr.options.map(qualify_field_primitives),
      };
    case "array":
      return {
        kind: "array",
        item: qualify_field_primitives(type_expr.item),
      };
    case "nullable":
      return {
        kind: "nullable",
        item: qualify_field_primitives(type_expr.item),
      };
    default:
      return type_expr;
  }
}

function field_type_expr(property: CssPropertyDef): TypeExpr {
  let type_expr = qualify_field_primitives(property.type_expr);
  if (property.value_type_name === "CssValue") {
    type_expr = append_type_expr(type_expr, { kind: "primitive", name: "str" });
  }
  if (property.is_shorthand && !CSS_VALUE_CAPABLE_ALIASES.has(property.value_type_name)) {
    type_expr = append_type_expr(type_expr, { kind: "reference", name: "CssValue" });
  }
  if (property.accepts_auto_px) {
    type_expr = append_type_expr(type_expr, {
      kind: "union",
      options: [
        { kind: "reference", name: "builtins.int" },
        { kind: "reference", name: "builtins.float" },
      ],
    });
  }
  return type_expr;
}

function emit_style_fields(properties: CssPropertyDef[]): string[] {
  const lines = ["@dataclass(kw_only=True)", "class _GeneratedStyleFields:"];
  lines.push('    """Generated CSS style field definitions.');
  lines.push("");
  lines.push("    Internal base class for `trellis.html.Style`.");
  lines.push("    Reference: https://developer.mozilla.org/en-US/docs/Web/CSS");
  lines.push('    """');
  for (const property of [...properties].sort((left, right) => left.python_name.localeCompare(right.python_name))) {
    lines.push(
      `    ${property.python_name}: ${render_type_expr(field_type_expr(property))} | None = None`,
    );
  }
  if (properties.length === 0) {
    lines.push("    pass");
  }
  return lines;
}

function emit_media_rule(media_features: CssMediaFeatureDef[]): string[] {
  const lines = ["@dataclass(frozen=True, kw_only=True)", "class MediaRule:"];
  lines.push('    """Generated media query rule for `h.media(...)`.');
  lines.push("");
  lines.push("    Represents a typed subset of standard CSS media features.");
  lines.push("    Reference: https://developer.mozilla.org/en-US/docs/Web/CSS/@media");
  lines.push('    """');
  lines.push("    style: Style");
  for (const feature of [...media_features].sort((left, right) => left.python_name.localeCompare(right.python_name))) {
    lines.push(
      `    ${feature.python_name}: ${render_type_expr(qualify_field_primitives(feature.type_expr))} | None = None`,
    );
  }
  lines.push('    query: str | None = None');
  return lines;
}

function emit_media_rule_kwargs(media_features: CssMediaFeatureDef[]): string[] {
  const lines = ["class _MediaRuleKwargs(TypedDict, total=False):"];
  lines.push('    """Generated keyword surface for `h.media(...)`."""');
  for (const feature of [...media_features].sort((left, right) => left.python_name.localeCompare(right.python_name))) {
    lines.push(
      `    ${feature.python_name}: ${render_type_expr(qualify_field_primitives(feature.type_expr))}`,
    );
  }
  lines.push("    query: builtins.str");
  return lines;
}

function emit_types_module(document: CssDocument, generated_at: string): string {
  const aliases = emit_aliases(document.value_aliases);
  const style_fields = emit_style_fields(document.properties);
  const media_rule = emit_media_rule(document.media_features);
  const media_rule_kwargs = emit_media_rule_kwargs(document.media_features);
  return [
    render_generated_module_docstring("Generated CSS style type declarations.", generated_at, [
      "Internal codegen artifact for trellis.html CSS typing.",
      "Reference: https://developer.mozilla.org/en-US/docs/Web/CSS",
    ]),
    "from __future__ import annotations",
    "",
    "import builtins",
    "",
    "from dataclasses import dataclass",
    "from typing import TYPE_CHECKING, Literal, TypedDict",
    "",
    "from trellis.html._css_primitives import CssAngle, CssColor, CssLength, CssPercent, CssTime, CssValue",
    "",
    "if TYPE_CHECKING:",
    "    from trellis.html._style_runtime import Style",
    "",
    ...aliases,
    "",
    ...style_fields,
    "",
    ...media_rule,
    "",
    ...media_rule_kwargs,
    "",
  ].join("\n");
}

function emit_metadata_module(document: CssDocument, generated_at: string): string {
  const css_name_by_field = [...document.properties]
    .sort((left, right) => left.python_name.localeCompare(right.python_name))
    .map((property) => `    "${property.python_name}": "${property.css_name}",`)
    .join("\n");

  const auto_px_fields = [...document.properties]
    .filter((property) => property.accepts_auto_px)
    .sort((left, right) => left.python_name.localeCompare(right.python_name))
    .map((property) => `    "${property.python_name}",`)
    .join("\n");

  const shorthand_fields = [...document.properties]
    .filter((property) => property.is_shorthand)
    .sort((left, right) => left.python_name.localeCompare(right.python_name))
    .map((property) => `    "${property.python_name}",`)
    .join("\n");

  return [
    render_generated_module_docstring("Generated CSS style metadata.", generated_at, [
      "Internal codegen artifact used to normalize trellis.html styles.",
      "Reference: https://developer.mozilla.org/en-US/docs/Web/CSS",
    ]),
    "from __future__ import annotations",
    "",
    "CSS_NAME_BY_FIELD = {",
    css_name_by_field,
    "}",
    "",
    "AUTO_PX_FIELDS = frozenset({",
    auto_px_fields,
    "})",
    "",
    "SHORTHAND_FIELDS = frozenset({",
    shorthand_fields,
    "})",
    "",
  ].join("\n");
}

export function build_trellis_css_modules(
  document: CssDocument,
  generated_at: string,
): TrellisModulePayload[] {
  return [
    {
      path: "src/trellis/html/_generated_style_types.py",
      content: emit_types_module(document, generated_at),
    },
    {
      path: "src/trellis/html/_generated_style_metadata.py",
      content: emit_metadata_module(document, generated_at),
    },
  ];
}
