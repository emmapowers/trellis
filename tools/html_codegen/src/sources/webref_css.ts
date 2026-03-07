import { index, type CssFeature } from "@webref/css";

import type { CssMediaFeatureDef, CssPropertyDef, SourceProvenance, TypeExpr } from "../ir/types.js";

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
  return name.replace(/-/g, "_");
}

function keyword_union(values: string[]): TypeExpr {
  return union(...values.map((value) => literal(value)));
}

function fallback_css_value(...options: TypeExpr[]): TypeExpr {
  return union(...options, reference("CssValue"));
}

function value_aliases(): Map<string, TypeExpr> {
  return new Map<string, TypeExpr>([
    ["CssValue", reference("CssValue")],
    ["Length", reference("CssLength")],
    ["Percent", reference("CssPercent")],
    ["ColorValue", reference("CssColor")],
    ["TimeValue", reference("CssTime")],
    ["AngleValue", reference("CssAngle")],
    ["Display", keyword_union(["block", "inline", "inline-block", "flex", "grid", "none", "contents"])],
    ["Position", keyword_union(["static", "relative", "absolute", "fixed", "sticky"])],
    ["Overflow", keyword_union(["visible", "hidden", "clip", "scroll", "auto"])],
    ["TextAlign", keyword_union(["left", "right", "center", "justify", "start", "end"])],
    ["FontWeight", union(primitive("int"), keyword_union(["normal", "bold", "lighter", "bolder"]))],
    ["FlexDirection", keyword_union(["row", "row-reverse", "column", "column-reverse"])],
    ["FlexWrap", keyword_union(["nowrap", "wrap", "wrap-reverse"])],
    ["JustifyContent", keyword_union(["flex-start", "flex-end", "center", "space-between", "space-around", "space-evenly", "start", "end"])],
    ["AlignItems", keyword_union(["stretch", "center", "start", "end", "flex-start", "flex-end", "baseline"])],
    ["LengthPercentage", union(reference("Length"), reference("Percent"))],
    ["WidthValue", fallback_css_value(reference("LengthPercentage"), keyword_union(["auto", "min-content", "max-content", "fit-content", "stretch", "contain"]))],
    ["HeightValue", fallback_css_value(reference("LengthPercentage"), keyword_union(["auto", "min-content", "max-content", "fit-content", "stretch", "contain"]))],
    ["BorderRadiusValue", fallback_css_value(reference("LengthPercentage"))],
    ["SpacingShorthand", fallback_css_value(reference("LengthPercentage"))],
    ["GapValue", fallback_css_value(reference("LengthPercentage"), keyword_union(["normal"]))],
    ["LineHeightValue", fallback_css_value(reference("LengthPercentage"), primitive("float"), keyword_union(["normal"]))],
    ["ShadowValue", reference("CssValue")],
    ["TransformValue", reference("CssValue")],
    ["TransitionValue", reference("CssValue")],
    ["PrefersColorScheme", keyword_union(["light", "dark"])],
    ["PrefersReducedMotion", keyword_union(["reduce", "no-preference"])],
    ["PointerCapability", keyword_union(["none", "coarse", "fine"])],
    ["HoverCapability", keyword_union(["none", "hover"])],
  ]);
}

function infer_alias_name(css_name: string, feature: CssFeature): string {
  if (css_name === "display") return "Display";
  if (css_name === "position") return "Position";
  if (css_name === "overflow" || css_name.startsWith("overflow-")) return "Overflow";
  if (css_name === "text-align") return "TextAlign";
  if (css_name === "font-weight") return "FontWeight";
  if (css_name === "flex-direction") return "FlexDirection";
  if (css_name === "flex-wrap") return "FlexWrap";
  if (css_name === "justify-content") return "JustifyContent";
  if (css_name === "align-items") return "AlignItems";
  if (css_name === "box-shadow") return "ShadowValue";
  if (css_name === "transform") return "TransformValue";
  if (css_name === "transition" || css_name.startsWith("transition-")) return "TransitionValue";
  if (css_name === "color" || css_name.endsWith("-color") || css_name === "background-color") {
    return "ColorValue";
  }
  if (css_name === "width" || css_name.endsWith("-width")) return "WidthValue";
  if (css_name === "height" || css_name.endsWith("-height")) return "HeightValue";
  if (css_name.includes("radius")) return "BorderRadiusValue";
  if (
    css_name === "margin" ||
    css_name === "padding" ||
    css_name.startsWith("margin-") ||
    css_name.startsWith("padding-") ||
    css_name === "inset" ||
    css_name.startsWith("inset-")
  ) {
    return "SpacingShorthand";
  }
  if (css_name === "gap" || css_name.endsWith("-gap")) return "GapValue";
  if (css_name === "line-height") return "LineHeightValue";
  if (css_name === "opacity") return "Opacity";
  if (css_name === "z-index") return "ZIndex";

  const syntax = feature.syntax ?? "";
  if (syntax.includes("<color>")) return "ColorValue";
  if (syntax.includes("<length-percentage")) return "LengthPercentage";
  if (syntax.includes("<length")) return "Length";
  if (syntax.includes("<time")) return "TimeValue";
  if (syntax.includes("<angle")) return "AngleValue";
  return "CssValue";
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
      return primitive("float");
    case "ZIndex":
      return union(primitive("int"), literal("auto"));
    default:
      return reference("CssValue");
  }
}

function accepts_auto_px(feature: CssFeature): boolean {
  const syntax = feature.syntax ?? "";
  return syntax.includes("<length") || syntax.includes("<length-percentage");
}

function is_property_shorthand(css_name: string, feature: CssFeature): boolean {
  return Boolean(feature.longhands?.length) || SHORTHAND_PROPERTIES.has(css_name);
}

function build_property_def(css_name: string, feature: CssFeature): CssPropertyDef {
  const value_type_name = infer_alias_name(css_name, feature);
  return {
    css_name,
    python_name: to_snake_case(css_name),
    value_type_name,
    type_expr: infer_type_expr(value_type_name),
    accepts_auto_px: accepts_auto_px(feature),
    is_shorthand: is_property_shorthand(css_name, feature),
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
  return "CssValue";
}

function build_media_feature_def(css_name: string, feature: CssFeature): CssMediaFeatureDef {
  const value_type_name = media_feature_alias(css_name);
  const type_expr =
    value_type_name === "Orientation"
      ? keyword_union(["portrait", "landscape"])
      : value_type_name === "CssValue"
        ? reference("CssValue")
        : reference(value_type_name);
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
  aliases.set("Orientation", keyword_union(["portrait", "landscape"]));

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
