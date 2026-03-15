import { index, type CssFeature } from "@webref/css";

import type { CssMediaFeatureDef, CssPropertyDef, CssValueTier, SourceProvenance, TypeExpr } from "../ir/types.js";

export interface CssSurface {
  properties: Map<string, CssPropertyDef>;
  media_features: Map<string, CssMediaFeatureDef>;
  value_aliases: Map<string, TypeExpr>;
}

const SHORTHAND_PROPERTIES = new Set([
  "background",
  "border",
  "border-color",
  "border-radius",
  "border-style",
  "border-width",
  "box-shadow",
  "flex",
  "font",
  "gap",
  "grid",
  "grid-area",
  "grid-column",
  "grid-row",
  "grid-template",
  "inset",
  "margin",
  "outline",
  "padding",
  "place-content",
  "place-items",
  "place-self",
  "text-decoration",
  "transform",
  "transition",
]);

const PYTHON_KEYWORDS = new Set([
  "and",
  "as",
  "assert",
  "async",
  "await",
  "break",
  "case",
  "class",
  "continue",
  "def",
  "del",
  "elif",
  "else",
  "except",
  "false",
  "finally",
  "for",
  "from",
  "global",
  "if",
  "import",
  "in",
  "is",
  "lambda",
  "match",
  "nonlocal",
  "none",
  "not",
  "or",
  "pass",
  "raise",
  "return",
  "true",
  "try",
  "while",
  "with",
  "yield",
]);

const NAMED_COLORS = [
  "aliceblue",
  "antiquewhite",
  "aqua",
  "aquamarine",
  "azure",
  "beige",
  "bisque",
  "black",
  "blanchedalmond",
  "blue",
  "blueviolet",
  "brown",
  "burlywood",
  "cadetblue",
  "chartreuse",
  "chocolate",
  "coral",
  "cornflowerblue",
  "cornsilk",
  "crimson",
  "cyan",
  "darkblue",
  "darkcyan",
  "darkgoldenrod",
  "darkgray",
  "darkgreen",
  "darkgrey",
  "darkkhaki",
  "darkmagenta",
  "darkolivegreen",
  "darkorange",
  "darkorchid",
  "darkred",
  "darksalmon",
  "darkseagreen",
  "darkslateblue",
  "darkslategray",
  "darkslategrey",
  "darkturquoise",
  "darkviolet",
  "deeppink",
  "deepskyblue",
  "dimgray",
  "dimgrey",
  "dodgerblue",
  "firebrick",
  "floralwhite",
  "forestgreen",
  "fuchsia",
  "gainsboro",
  "ghostwhite",
  "gold",
  "goldenrod",
  "gray",
  "green",
  "greenyellow",
  "grey",
  "honeydew",
  "hotpink",
  "indianred",
  "indigo",
  "ivory",
  "khaki",
  "lavender",
  "lavenderblush",
  "lawngreen",
  "lemonchiffon",
  "lightblue",
  "lightcoral",
  "lightcyan",
  "lightgoldenrodyellow",
  "lightgray",
  "lightgreen",
  "lightgrey",
  "lightpink",
  "lightsalmon",
  "lightseagreen",
  "lightskyblue",
  "lightslategray",
  "lightslategrey",
  "lightsteelblue",
  "lightyellow",
  "lime",
  "limegreen",
  "linen",
  "magenta",
  "maroon",
  "mediumaquamarine",
  "mediumblue",
  "mediumorchid",
  "mediumpurple",
  "mediumseagreen",
  "mediumslateblue",
  "mediumspringgreen",
  "mediumturquoise",
  "mediumvioletred",
  "midnightblue",
  "mintcream",
  "mistyrose",
  "moccasin",
  "navajowhite",
  "navy",
  "oldlace",
  "olive",
  "olivedrab",
  "orange",
  "orangered",
  "orchid",
  "palegoldenrod",
  "palegreen",
  "paleturquoise",
  "palevioletred",
  "papayawhip",
  "peachpuff",
  "peru",
  "pink",
  "plum",
  "powderblue",
  "purple",
  "rebeccapurple",
  "red",
  "rosybrown",
  "royalblue",
  "saddlebrown",
  "salmon",
  "sandybrown",
  "seagreen",
  "seashell",
  "sienna",
  "silver",
  "skyblue",
  "slateblue",
  "slategray",
  "slategrey",
  "snow",
  "springgreen",
  "steelblue",
  "tan",
  "teal",
  "thistle",
  "tomato",
  "turquoise",
  "violet",
  "wheat",
  "white",
  "whitesmoke",
  "yellow",
  "yellowgreen",
] as const;

function source(reason: string, contributors: string[] = ["webref", "csstype"]): SourceProvenance {
  return {
    winner: "webref",
    contributors,
    reason,
    source_version: "@webref/css@8.4.0",
  };
}

function primitive(name: "str" | "int" | "float" | "bool" | "none"): TypeExpr {
  return { kind: "primitive", name };
}

function literal(value: string | number | boolean | null): TypeExpr {
  return { kind: "literal", value };
}

function reference(name: string): TypeExpr {
  return { kind: "reference", name };
}

function union(...options: TypeExpr[]): TypeExpr {
  return {
    kind: "union",
    options: options.flatMap((option) => (option.kind === "union" ? option.options : [option])),
  };
}

function to_snake_case(name: string): string {
  const snake = name.replace(/-/g, "_");
  return PYTHON_KEYWORDS.has(snake) ? `${snake}_` : snake;
}

function keyword_union(values: string[]): TypeExpr {
  return union(...values.map((value) => literal(value)));
}

// Build a type union with CssRawString as the escape hatch (no bare str).
function with_raw_escape(...options: TypeExpr[]): TypeExpr {
  return union(...options, reference("CssRawString"));
}

function value_aliases(): Map<string, TypeExpr> {
  return new Map<string, TypeExpr>([
    ["CssRawString", reference("CssRawString")],

    // Dimensional types — no bare str, use typed helpers or raw()
    ["Length", union(reference("CssLength"), reference("CssRawString"))],
    ["Percent", union(reference("CssPercent"), reference("CssRawString"))],
    ["LengthPercentage", union(reference("Length"), reference("Percent"))],
    ["TimeValue", union(reference("CssTime"), reference("CssRawString"))],
    ["AngleValue", union(reference("CssAngle"), reference("CssRawString"))],

    // Color — keeps str for hex codes, named colors give autocomplete
    ["NamedColor", keyword_union([...NAMED_COLORS])],
    [
      "ColorKeyword",
      union(reference("NamedColor"), literal("transparent"), literal("currentColor")),
    ],
    [
      "ColorValue",
      union(reference("ColorKeyword"), primitive("str"), reference("CssColor"), reference("CssRawString")),
    ],

    // Keyword unions — no bare str, CssRawString is escape hatch
    [
      "Display",
      with_raw_escape(
        keyword_union([
          "block",
          "inline",
          "inline-block",
          "flex",
          "inline-flex",
          "grid",
          "inline-grid",
          "none",
          "contents",
        ]),
      ),
    ],
    ["Position", with_raw_escape(keyword_union(["static", "relative", "absolute", "fixed", "sticky"]))],
    ["Overflow", with_raw_escape(keyword_union(["visible", "hidden", "clip", "scroll", "auto"]))],
    ["TextAlign", with_raw_escape(keyword_union(["left", "right", "center", "justify", "start", "end"]))],
    [
      "FontWeight",
      with_raw_escape(union(primitive("int"), keyword_union(["normal", "bold", "lighter", "bolder"]))),
    ],
    ["FlexDirection", with_raw_escape(keyword_union(["row", "row-reverse", "column", "column-reverse"]))],
    ["FlexWrap", with_raw_escape(keyword_union(["nowrap", "wrap", "wrap-reverse"]))],
    [
      "JustifyContent",
      with_raw_escape(
        keyword_union(["flex-start", "flex-end", "center", "space-between", "space-around", "space-evenly", "start", "end"]),
      ),
    ],
    [
      "AlignItems",
      with_raw_escape(keyword_union(["stretch", "center", "start", "end", "flex-start", "flex-end", "baseline"])),
    ],

    // Dimensional layout types
    ["WidthValue", with_raw_escape(reference("LengthPercentage"), keyword_union(["auto", "min-content", "max-content", "fit-content", "stretch", "contain"]))],
    ["HeightValue", with_raw_escape(reference("LengthPercentage"), keyword_union(["auto", "min-content", "max-content", "fit-content", "stretch", "contain"]))],
    ["BorderRadiusValue", with_raw_escape(reference("LengthPercentage"))],
    ["SpacingShorthand", with_raw_escape(reference("LengthPercentage"))],
    ["GapValue", with_raw_escape(reference("LengthPercentage"), keyword_union(["normal"]))],
    ["LineHeightValue", with_raw_escape(reference("LengthPercentage"), primitive("float"), keyword_union(["normal"]))],

    // Shorthand/complex types — keep str for complex multi-value syntax
    ["ShadowValue", union(primitive("str"), reference("CssRawString"))],
    ["TransformValue", union(primitive("str"), reference("CssRawString"))],
    ["TransitionValue", union(primitive("str"), reference("CssRawString"))],

    // Numeric types
    ["Opacity", union(primitive("float"), reference("CssRawString"))],
    ["ZIndex", union(primitive("int"), literal("auto"), reference("CssRawString"))],

    // Media features
    ["MediaFeatureValue", union(primitive("str"), primitive("int"), primitive("float"), reference("CssRawString"))],
    ["PrefersColorScheme", with_raw_escape(keyword_union(["light", "dark"]))],
    ["PrefersReducedMotion", with_raw_escape(keyword_union(["reduce", "no-preference"]))],
    ["PointerCapability", with_raw_escape(keyword_union(["none", "coarse", "fine"]))],
    ["HoverCapability", with_raw_escape(keyword_union(["none", "hover"]))],
  ]);
}

// Properties that use the Overflow type (visible|hidden|clip|scroll|auto).
// Explicit list prevents overflow-anchor, overflow-wrap, overflow-clip-margin
// from being misclassified.
const OVERFLOW_PROPERTIES = new Set([
  "overflow",
  "overflow-x",
  "overflow-y",
  "overflow-block",
  "overflow-inline",
]);

// Properties that use SpacingShorthand (length/percentage shorthand values).
// Explicit list prevents margin-trim, margin-break (keyword-only) from being
// misclassified.
const SPACING_PROPERTIES = new Set([
  "margin",
  "margin-top",
  "margin-right",
  "margin-bottom",
  "margin-left",
  "margin-block",
  "margin-block-start",
  "margin-block-end",
  "margin-inline",
  "margin-inline-start",
  "margin-inline-end",
  "padding",
  "padding-top",
  "padding-right",
  "padding-bottom",
  "padding-left",
  "padding-block",
  "padding-block-start",
  "padding-block-end",
  "padding-inline",
  "padding-inline-start",
  "padding-inline-end",
  "inset",
  "inset-block",
  "inset-block-start",
  "inset-block-end",
  "inset-inline",
  "inset-inline-start",
  "inset-inline-end",
]);

// Layout width/height properties. Border widths, outline-width, etc. use
// <line-width> (thin|medium|thick|<length>) which is different from layout
// widths (auto|min-content|max-content|fit-content|stretch|<length>).
const WIDTH_PROPERTIES = new Set([
  "width",
  "min-width",
  "max-width",
  "block-size",
  "min-block-size",
  "max-block-size",
  "inline-size",
  "min-inline-size",
  "max-inline-size",
  "flex-basis",
  "column-width",
]);

const HEIGHT_PROPERTIES = new Set([
  "height",
  "min-height",
  "max-height",
]);

// Properties where the <angle> syntax fallback would give a wrong type
// because they are primarily keyword-based with optional angle values.
const ANGLE_SYNTAX_EXCLUSIONS = new Set([
  "font-style",
  "image-orientation",
]);

function infer_alias_name(css_name: string, feature: CssFeature): string {
  if (css_name === "display") return "Display";
  if (css_name === "position") return "Position";
  if (OVERFLOW_PROPERTIES.has(css_name)) return "Overflow";
  if (css_name === "text-align") return "TextAlign";
  if (css_name === "font-weight") return "FontWeight";
  if (css_name === "flex-direction") return "FlexDirection";
  if (css_name === "flex-wrap") return "FlexWrap";
  if (css_name === "justify-content") return "JustifyContent";
  if (css_name === "align-items") return "AlignItems";
  if (css_name === "box-shadow") return "ShadowValue";
  if (css_name === "transform") return "TransformValue";
  if (css_name === "transition") return "TransitionValue";
  if (css_name === "color" || css_name.endsWith("-color") || css_name === "background-color") {
    return "ColorValue";
  }
  if (css_name === "line-height") return "LineHeightValue";
  if (css_name.includes("radius")) return "BorderRadiusValue";
  if (SPACING_PROPERTIES.has(css_name)) return "SpacingShorthand";
  if (css_name === "gap" || css_name.endsWith("-gap")) return "GapValue";
  if (WIDTH_PROPERTIES.has(css_name)) return "WidthValue";
  if (HEIGHT_PROPERTIES.has(css_name)) return "HeightValue";
  if (css_name === "opacity") return "Opacity";
  if (css_name === "z-index") return "ZIndex";

  const syntax = feature.syntax ?? "";
  if (syntax.includes("<color>")) return "ColorValue";
  if (syntax.includes("<length-percentage")) return "LengthPercentage";
  if (syntax.includes("<length")) return "Length";
  if (syntax.includes("<time")) return "TimeValue";
  if (!ANGLE_SYNTAX_EXCLUSIONS.has(css_name) && syntax.includes("<angle")) return "AngleValue";
  return "CssRawString";
}

function infer_type_expr(alias_name: string): TypeExpr {
  switch (alias_name) {
    case "LengthPercentage":
      return reference("LengthPercentage");
    case "Length":
      return reference("Length");
    case "TimeValue":
      return reference("TimeValue");
    case "AngleValue":
      return reference("AngleValue");
    case "ColorValue":
      return reference("ColorValue");
    case "Display":
      return reference("Display");
    case "Position":
      return reference("Position");
    case "Overflow":
      return reference("Overflow");
    case "TextAlign":
      return reference("TextAlign");
    case "FontWeight":
      return reference("FontWeight");
    case "FlexDirection":
      return reference("FlexDirection");
    case "FlexWrap":
      return reference("FlexWrap");
    case "JustifyContent":
      return reference("JustifyContent");
    case "AlignItems":
      return reference("AlignItems");
    case "WidthValue":
      return reference("WidthValue");
    case "HeightValue":
      return reference("HeightValue");
    case "BorderRadiusValue":
      return reference("BorderRadiusValue");
    case "SpacingShorthand":
      return reference("SpacingShorthand");
    case "GapValue":
      return reference("GapValue");
    case "LineHeightValue":
      return reference("LineHeightValue");
    case "ShadowValue":
      return reference("ShadowValue");
    case "TransformValue":
      return reference("TransformValue");
    case "TransitionValue":
      return reference("TransitionValue");
    case "Opacity":
      return reference("Opacity");
    case "ZIndex":
      return reference("ZIndex");
    case "MediaFeatureValue":
      return reference("MediaFeatureValue");
    default:
      return reference("CssRawString");
  }
}

const AUTO_PX_ALIASES = new Set([
  "WidthValue",
  "HeightValue",
  "BorderRadiusValue",
  "SpacingShorthand",
  "GapValue",
  "Length",
  "LengthPercentage",
]);

function accepts_auto_px(feature: CssFeature, value_type_name: string): boolean {
  if (value_type_name === "LineHeightValue") {
    return false;
  }
  if (AUTO_PX_ALIASES.has(value_type_name)) {
    return true;
  }
  const syntax = feature.syntax ?? "";
  return syntax.includes("<length") || syntax.includes("<length-percentage");
}

function is_property_shorthand(css_name: string, feature: CssFeature): boolean {
  return Boolean(feature.longhands?.length) || SHORTHAND_PROPERTIES.has(css_name);
}

// Properties whose values are genuinely free-form strings (font names, URLs,
// content strings, etc.) — these accept bare `str` in the typed API.
const STRING_NATIVE_PROPERTIES = new Set([
  "content",
  "counter-increment",
  "counter-reset",
  "counter-set",
  "cursor",
  "font-family",
  "font-feature-settings",
  "font-variation-settings",
  "grid-template-areas",
  "grid-template-columns",
  "grid-template-rows",
  "list-style-image",
  "list-style-type",
  "mask-image",
  "quotes",
  "will-change",
]);

// Properties where `str` is kept because the syntax contains <string>,
// <url>, or <image> productions — free-form values that can't be typed.
function is_string_native_by_syntax(feature: CssFeature): boolean {
  const syntax = feature.syntax ?? "";
  return syntax.includes("<string>") || syntax.includes("<url") || syntax.includes("<image>");
}

function classify_value_tier(
  css_name: string,
  feature: CssFeature,
  value_type_name: string,
  is_shorthand: boolean,
): CssValueTier {
  if (STRING_NATIVE_PROPERTIES.has(css_name) || is_string_native_by_syntax(feature)) {
    return "string_native";
  }
  if (is_shorthand) {
    return "shorthand";
  }
  // Aliases that represent dimensional values (lengths, percentages, etc.)
  const dimensional_aliases = new Set([
    "Length",
    "Percent",
    "LengthPercentage",
    "WidthValue",
    "HeightValue",
    "BorderRadiusValue",
    "SpacingShorthand",
    "GapValue",
    "LineHeightValue",
    "TimeValue",
    "AngleValue",
  ]);
  if (dimensional_aliases.has(value_type_name)) {
    return "dimensional";
  }
  return "keyword";
}

function build_property_def(css_name: string, feature: CssFeature): CssPropertyDef {
  const value_type_name = infer_alias_name(css_name, feature);
  const is_shorthand = is_property_shorthand(css_name, feature);
  return {
    css_name,
    python_name: to_snake_case(css_name),
    value_type_name,
    type_expr: infer_type_expr(value_type_name),
    accepts_auto_px: accepts_auto_px(feature, value_type_name),
    is_shorthand,
    value_tier: classify_value_tier(css_name, feature, value_type_name, is_shorthand),
    source: source("css_property"),
  };
}

function media_feature_alias(name: string): string {
  if (name === "min-width" || name === "max-width" || name === "min-height" || name === "max-height") {
    return "Length";
  }
  if (name === "prefers-color-scheme") {
    return "PrefersColorScheme";
  }
  if (name === "prefers-reduced-motion") {
    return "PrefersReducedMotion";
  }
  if (name === "pointer" || name === "any-pointer") {
    return "PointerCapability";
  }
  if (name === "hover" || name === "any-hover") {
    return "HoverCapability";
  }
  if (name === "orientation") {
    return "Orientation";
  }
  return "MediaFeatureValue";
}

function build_media_feature_def(css_name: string, feature: CssFeature): CssMediaFeatureDef {
  const value_type_name = media_feature_alias(css_name);
  let type_expr =
    value_type_name === "Orientation"
      ? keyword_union(["portrait", "landscape"])
      : reference(value_type_name);
  if (css_name.includes("width") || css_name.includes("height")) {
    type_expr = union(type_expr, primitive("int"), primitive("float"));
  }
  return {
    css_name,
    python_name: to_snake_case(css_name),
    value_type_name,
    type_expr,
    accepts_auto_px: css_name.includes("width") || css_name.includes("height"),
    source: source("css_media_feature", ["webref"]),
  };
}

function supported_property_names(features: Record<string, CssFeature>): string[] {
  return Object.keys(features)
    .filter((name) => !name.startsWith("--"))
    .filter((name) => !name.startsWith("-"))
    .sort((left, right) => left.localeCompare(right));
}

export async function extract_css_surface(): Promise<CssSurface> {
  const css = await index();
  const aliases = value_aliases();
  aliases.set("Orientation", with_raw_escape(keyword_union(["portrait", "landscape"])));

  const properties = new Map<string, CssPropertyDef>();
  for (const name of supported_property_names(css.properties)) {
    properties.set(name, build_property_def(name, css.properties[name]!));
  }

  const media_features = new Map<string, CssMediaFeatureDef>();
  const descriptors = css.atrules["@media"]?.descriptors ?? {};
  for (const [name, feature] of Object.entries(descriptors)) {
    if (name.startsWith("-")) {
      continue;
    }
    media_features.set(name, build_media_feature_def(name, feature));
    if (name === "width" || name === "height") {
      media_features.set(`min-${name}`, build_media_feature_def(`min-${name}`, feature));
      media_features.set(`max-${name}`, build_media_feature_def(`max-${name}`, feature));
    }
  }

  return {
    properties,
    media_features,
    value_aliases: aliases,
  };
}
