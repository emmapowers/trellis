import { describe, expect, it } from "vitest";

import { build_trellis_css_modules } from "../src/emit/targets/trellis_css.js";
import type { CssDocument } from "../src/ir/types.js";

function sample_css_document(): CssDocument {
  return {
    properties: [
      {
        css_name: "display",
        python_name: "display",
        value_type_name: "Display",
        type_expr: {
          kind: "union",
          options: [
            { kind: "literal", value: "block" },
            { kind: "literal", value: "flex" },
            { kind: "literal", value: "none" },
          ],
        },
        accepts_auto_px: false,
        is_shorthand: false,
        source: {
          winner: "webref",
          contributors: ["webref", "csstype"],
          reason: "css_property",
          source_version: "@webref/css@8.4.0",
        },
      },
      {
        css_name: "width",
        python_name: "width",
        value_type_name: "WidthValue",
        type_expr: { kind: "reference", name: "WidthValue" },
        accepts_auto_px: true,
        is_shorthand: false,
        source: {
          winner: "webref",
          contributors: ["webref", "csstype"],
          reason: "css_property",
          source_version: "@webref/css@8.4.0",
        },
      },
      {
        css_name: "margin",
        python_name: "margin",
        value_type_name: "SpacingShorthand",
        type_expr: { kind: "reference", name: "SpacingShorthand" },
        accepts_auto_px: true,
        is_shorthand: true,
        source: {
          winner: "webref",
          contributors: ["webref", "csstype"],
          reason: "css_property",
          source_version: "@webref/css@8.4.0",
        },
      },
      {
        css_name: "border",
        python_name: "border",
        value_type_name: "ColorValue",
        type_expr: { kind: "reference", name: "ColorValue" },
        accepts_auto_px: false,
        is_shorthand: true,
        source: {
          winner: "webref",
          contributors: ["webref", "csstype"],
          reason: "css_property",
          source_version: "@webref/css@8.4.0",
        },
      },
      {
        css_name: "opacity",
        python_name: "opacity",
        value_type_name: "Opacity",
        type_expr: { kind: "primitive", name: "float" },
        accepts_auto_px: false,
        is_shorthand: false,
        source: {
          winner: "webref",
          contributors: ["webref", "csstype"],
          reason: "css_property",
          source_version: "@webref/css@8.4.0",
        },
      },
    ],
    media_features: [
      {
        css_name: "min-width",
        python_name: "min_width",
        value_type_name: "Length",
        type_expr: { kind: "reference", name: "Length" },
        accepts_auto_px: true,
        source: {
          winner: "webref",
          contributors: ["webref"],
          reason: "css_media_feature",
          source_version: "@webref/css@8.4.0",
        },
      },
      {
        css_name: "prefers-color-scheme",
        python_name: "prefers_color_scheme",
        value_type_name: "PrefersColorScheme",
        type_expr: {
          kind: "union",
          options: [
            { kind: "literal", value: "light" },
            { kind: "literal", value: "dark" },
          ],
        },
        accepts_auto_px: false,
        source: {
          winner: "webref",
          contributors: ["webref"],
          reason: "css_media_feature",
          source_version: "@webref/css@8.4.0",
        },
      },
    ],
    value_aliases: [
      {
        name: "Display",
        type_expr: {
          kind: "union",
          options: [
            { kind: "literal", value: "block" },
            { kind: "literal", value: "flex" },
            { kind: "literal", value: "none" },
          ],
        },
        source: {
          winner: "webref",
          contributors: ["webref"],
          reason: "css_value_alias",
          source_version: "@webref/css@8.4.0",
        },
      },
      {
        name: "Length",
        type_expr: { kind: "reference", name: "CssLength" },
        source: {
          winner: "trellis_policy",
          contributors: ["webref"],
          reason: "css_value_alias",
          source_version: "@webref/css@8.4.0",
        },
      },
      {
        name: "LengthPercentage",
        type_expr: {
          kind: "union",
          options: [
            { kind: "reference", name: "Length" },
            { kind: "reference", name: "Percent" },
          ],
        },
        source: {
          winner: "trellis_policy",
          contributors: ["webref"],
          reason: "css_value_alias",
          source_version: "@webref/css@8.4.0",
        },
      },
      {
        name: "NamedColor",
        type_expr: {
          kind: "union",
          options: [
            { kind: "literal", value: "rebeccapurple" },
            { kind: "literal", value: "tomato" },
          ],
        },
        source: {
          winner: "trellis_policy",
          contributors: ["webref"],
          reason: "css_value_alias",
          source_version: "@webref/css@8.4.0",
        },
      },
      {
        name: "ColorValue",
        type_expr: {
          kind: "union",
          options: [
            { kind: "reference", name: "NamedColor" },
            { kind: "primitive", name: "str" },
            { kind: "reference", name: "CssColor" },
          ],
        },
        source: {
          winner: "trellis_policy",
          contributors: ["webref"],
          reason: "css_value_alias",
          source_version: "@webref/css@8.4.0",
        },
      },
    ],
  };
}

describe("trellis css target", () => {
  it("emits generated style type and metadata modules", () => {
    const modules = build_trellis_css_modules(sample_css_document(), "2026-03-07T12:00:00.000Z");

    expect(modules.map((module) => module.path)).toEqual([
      "src/trellis/html/_generated_style_types.py",
      "src/trellis/html/_generated_style_metadata.py",
    ]);

    const types_module = modules.find((module) => module.path.endsWith("_generated_style_types.py"));
    expect(types_module?.content).toContain("Generated at: 2026-03-07T12:00:00.000Z");
    expect(types_module?.content).toContain("import builtins");
    expect(types_module?.content).toContain("NamedColor = Literal[");
    expect(types_module?.content).toContain('Literal["rebeccapurple"');
    expect(types_module?.content).toContain("ColorValue = NamedColor | str | CssColor");
    expect(types_module?.content).toContain("Display = Literal[");
    expect(types_module?.content).toContain("class _GeneratedStyleFields:");
    expect(types_module?.content).toContain("border: ColorValue | CssValue | None = None");
    expect(types_module?.content).toContain(
      "width: WidthValue | builtins.int | builtins.float | None = None",
    );
    expect(types_module?.content).toContain(
      "margin: SpacingShorthand | builtins.int | builtins.float | None = None",
    );
    expect(types_module?.content).toContain("opacity: builtins.float | None = None");
    expect(types_module?.content).toContain("class MediaRule:");
    expect(types_module?.content).toContain("prefers_color_scheme: PrefersColorScheme | None = None");

    const metadata_module = modules.find((module) => module.path.endsWith("_generated_style_metadata.py"));
    expect(metadata_module?.content).toContain("CSS_NAME_BY_FIELD = {");
    expect(metadata_module?.content).toContain('"display": "display"');
    expect(metadata_module?.content).toContain("AUTO_PX_FIELDS = frozenset({");
    expect(metadata_module?.content).toContain('"width"');
    expect(metadata_module?.content).toContain("SHORTHAND_FIELDS = frozenset({");
    expect(metadata_module?.content).toContain('"margin"');
  });
});
