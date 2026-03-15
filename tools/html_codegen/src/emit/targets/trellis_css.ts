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
  if (property.value_type_name === "CssRawString") {
    type_expr = append_type_expr(type_expr, { kind: "reference", name: "builtins.str" });
  }
  if (property.is_shorthand && !CSS_VALUE_CAPABLE_ALIASES.has(property.value_type_name)) {
    type_expr = append_type_expr(type_expr, { kind: "reference", name: "CssRawString" });
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
  const lines = ["class _GeneratedStyleFields:"];
  for (const property of [...properties].sort((left, right) => left.python_name.localeCompare(right.python_name))) {
    lines.push(
      `    ${property.python_name}: ${render_type_expr(field_type_expr(property))} | None`,
    );
  }
  if (properties.length === 0) {
    lines.push("    pass");
  }
  return lines;
}

function emit_media_rule(media_features: CssMediaFeatureDef[]): string[] {
  const lines = ["class MediaRule:"];
  lines.push('    """Generated media query rule for `h.media(...)`.');
  lines.push("");
  lines.push("    Represents a typed subset of standard CSS media features.");
  lines.push("    Reference: https://developer.mozilla.org/en-US/docs/Web/CSS/@media");
  lines.push('    """');
  lines.push("    style: StyleInput");
  lines.push("    query: builtins.str | None");
  lines.push("    features: builtins.dict[builtins.str, Any]");
  for (const feature of [...media_features].sort((left, right) => left.python_name.localeCompare(right.python_name))) {
    lines.push(
      `    ${feature.python_name}: ${render_type_expr(qualify_field_primitives(feature.type_expr))} | None = None`,
    );
  }
  lines.push("    def __init__(");
  lines.push("        self,");
  lines.push("        *,");
  lines.push("        style: StyleInput,");
  lines.push("        query: builtins.str | None = None,");
  lines.push("        **feature_values: Unpack[_MediaRuleKwargs],");
  lines.push("    ) -> None: ...");
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
  return lines;
}

function emit_types_module(document: CssDocument, generated_at: string): string {
  const aliases = emit_aliases(document.value_aliases);
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
    "from typing import Literal, TypedDict",
    "",
    "from trellis.html._css_primitives import CssAngle, CssColor, CssLength, CssPercent, CssTime, CssRawString",
    "",
    ...aliases,
    "",
    ...media_rule_kwargs,
    "",
  ].join("\n");
}

function emit_style_runtime_stub(document: CssDocument, generated_at: string): string {
  const ordered_properties = [...document.properties].sort((left, right) =>
    left.python_name.localeCompare(right.python_name),
  );
  const ordered_alias_names = [...document.value_aliases]
    .map((alias) => alias.name)
    .sort((left, right) => left.localeCompare(right));
  const style_field_lines = emit_style_fields(document.properties);
  const media_rule_lines = emit_media_rule(document.media_features);
  // Names reserved by structural/pseudo-class params in Style.__init__.
  // CSS properties with these python_names are handled by the runtime's
  // _consume_kwargs, so they must not appear as duplicate __init__ params.
  const reserved_init_params = new Set([
    "vars", "selectors", "media",
    "hover", "focus", "focus_visible", "focus_within",
    "active", "visited", "disabled", "checked",
    "placeholder", "before", "after", "selection",
  ]);
  const init_properties = ordered_properties.filter(
    (property) => !reserved_init_params.has(property.python_name),
  );
  const init_lines = [
    "    def __init__(",
    "        self,",
    "        _mapping: StyleInput | None = None,",
    "        /,",
    "        *,",
    "        vars: builtins.dict[builtins.str, StyleScalar] | None = None,",
    "        selectors: builtins.dict[builtins.str, StyleInput] | None = None,",
    "        media: builtins.list[MediaRule] | builtins.dict[builtins.str, StyleInput] | None = None,",
    '        hover: Style | None = None,',
    '        focus: Style | None = None,',
    '        focus_visible: Style | None = None,',
    '        focus_within: Style | None = None,',
    '        active: Style | None = None,',
    '        visited: Style | None = None,',
    '        disabled: Style | None = None,',
    '        checked: Style | None = None,',
    '        placeholder: Style | None = None,',
    '        before: Style | None = None,',
    '        after: Style | None = None,',
    '        selection: Style | None = None,',
    ...init_properties.map(
      (property) =>
        `        ${property.python_name}: ${render_type_expr(field_type_expr(property))} | None = None,`,
    ),
    "        **extra_styles: Any,",
    "    ) -> None: ...",
  ];
  const helper_lines = [
    "def raw(value: builtins.str) -> CssRawString: ...",
    "def color(value: builtins.str) -> CssColor: ...",
    "def px(value: builtins.int | builtins.float) -> CssLength: ...",
    "def rem(value: builtins.int | builtins.float) -> CssLength: ...",
    "def em(value: builtins.int | builtins.float) -> CssLength: ...",
    "def vw(value: builtins.int | builtins.float) -> CssLength: ...",
    "def vh(value: builtins.int | builtins.float) -> CssLength: ...",
    "def pct(value: builtins.int | builtins.float) -> CssPercent: ...",
    "def sec(value: builtins.int | builtins.float) -> CssTime: ...",
    "def ms(value: builtins.int | builtins.float) -> CssTime: ...",
    "def deg(value: builtins.int | builtins.float) -> CssAngle: ...",
    "def rgb(red: builtins.int, green: builtins.int, blue: builtins.int) -> CssColor: ...",
    "def rgba(red: builtins.int, green: builtins.int, blue: builtins.int, alpha: builtins.float) -> CssColor: ...",
    "def hsl(hue: builtins.int | builtins.float, saturation: builtins.int | builtins.float, lightness: builtins.int | builtins.float) -> CssColor: ...",
    "def hwb(hue: builtins.int | builtins.float, whiteness: builtins.int | builtins.float, blackness: builtins.int | builtins.float, *, alpha: builtins.float | None = None) -> CssColor: ...",
    "def lab(lightness: builtins.int | builtins.float, a_value: builtins.int | builtins.float, b_value: builtins.int | builtins.float, *, alpha: builtins.float | None = None) -> CssColor: ...",
    "def lch(lightness: builtins.int | builtins.float, chroma: builtins.int | builtins.float, hue: builtins.int | builtins.float, *, alpha: builtins.float | None = None) -> CssColor: ...",
    "def oklab(lightness: builtins.int | builtins.float, a_value: builtins.int | builtins.float, b_value: builtins.int | builtins.float, *, alpha: builtins.float | None = None) -> CssColor: ...",
    "def oklch(lightness: builtins.int | builtins.float, chroma: builtins.int | builtins.float, hue: builtins.int | builtins.float, *, alpha: builtins.float | None = None) -> CssColor: ...",
    "def color_space(space: builtins.str, *components: builtins.int | builtins.float | builtins.str, alpha: builtins.float | None = None) -> CssColor: ...",
    "def var(name: builtins.str, fallback: StyleScalar | None = None) -> CssRawString: ...",
    "def calc(expression: builtins.str) -> CssRawString: ...",
    "def min_(*values: StyleScalar) -> CssRawString: ...",
    "def max_(*values: StyleScalar) -> CssRawString: ...",
    "def clamp(minimum: StyleScalar, preferred: StyleScalar, maximum: StyleScalar) -> CssRawString: ...",
    "def margin(*values: StyleScalar) -> CssRawString: ...",
    "def padding(*values: StyleScalar) -> CssRawString: ...",
    "def inset(*values: StyleScalar) -> CssRawString: ...",
    "def border(width: StyleScalar, style: builtins.str, color_value: StyleScalar) -> CssRawString: ...",
    "def shadow(*parts: StyleScalar) -> CssRawString: ...",
    "def scale(value: builtins.int | builtins.float) -> CssRawString: ...",
    "def rotate(value: CssAngle | builtins.int | builtins.float) -> CssRawString: ...",
    "def translate(x_value: StyleScalar, y_value: StyleScalar | None = None) -> CssRawString: ...",
    "def media(*, style: StyleInput, query: builtins.str | None = None, **feature_values: Unpack[_MediaRuleKwargs]) -> MediaRule: ...",
  ];

  // Public names exported by __all__ — types, classes, and helper functions.
  // Must match the __all__ in _style_runtime.py to keep star imports consistent.
  const helper_names = helper_lines.map((line) => {
    const match = line.match(/^def (\w+)\(/);
    return match ? match[1] : null;
  }).filter((name): name is string => name !== null);
  const all_names = [
    "CssAngle", "CssColor", "CssLength", "CssPercent", "CssTime", "CssRawString",
    "HeightInput", "MediaRule", "RawStyleMapping", "SpacingInput",
    "Style", "StyleInput", "StyleScalar", "WidthInput",
    ...helper_names,
  ].sort((a, b) => a.localeCompare(b));

  return [
    render_generated_module_docstring("Generated CSS runtime typing stubs.", generated_at, [
      "Internal codegen artifact describing the public runtime surface for trellis.html CSS helpers.",
      "Reference: https://developer.mozilla.org/en-US/docs/Web/CSS",
    ]),
    "from __future__ import annotations",
    "",
    "import builtins",
    "",
    "from collections.abc import Mapping",
    "from typing import Any, Literal, Unpack",
    "",
    "from trellis.html._css_primitives import CssAngle, CssColor, CssLength, CssPercent, CssTime, CssRawString",
    `from trellis.html._generated_style_types import ${[...ordered_alias_names, "_MediaRuleKwargs"].join(", ")}`,
    "",
    "__all__ = [",
    ...all_names.map((name) => `    "${name}",`),
    "]",
    "",
    "type StyleScalar = builtins.str | builtins.int | builtins.float | CssRawString",
    "type RawStyleMapping = Mapping[builtins.str, Any]",
    "type StyleInput = Style | RawStyleMapping",
    "type WidthInput = WidthValue | builtins.int | builtins.float | builtins.str",
    "type HeightInput = HeightValue | builtins.int | builtins.float | builtins.str",
    "type SpacingInput = SpacingShorthand | builtins.int | builtins.float | builtins.str",
    "",
    ...media_rule_lines,
    "",
    "class Style:",
    '    """Generated typing stub for `trellis.html.Style`."""',
    "    props: builtins.dict[builtins.str, Any]",
    "    vars: builtins.dict[builtins.str, StyleScalar]",
    "    selectors: builtins.dict[builtins.str, StyleInput]",
    "    media: builtins.list[MediaRule]",
    ...style_field_lines.slice(1),
    "",
    ...init_lines,
    "",
    ...helper_lines,
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
      path: "src/trellis/html/_generated_style_types.pyi",
      content: emit_types_module(document, generated_at),
    },
    {
      path: "src/trellis/html/_style_runtime.pyi",
      content: emit_style_runtime_stub(document, generated_at),
    },
    {
      path: "src/trellis/html/_generated_style_metadata.py",
      content: emit_metadata_module(document, generated_at),
    },
  ];
}
