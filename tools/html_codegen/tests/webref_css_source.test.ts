import { describe, expect, it } from "vitest";

import { extract_css_surface } from "../src/sources/webref_css.js";

describe("webref css source extraction", () => {
  it("extracts css properties, value aliases, and auto-px metadata", async () => {
    const surface = await extract_css_surface();

    expect(surface.properties.get("display")?.python_name).toBe("display");
    expect(surface.properties.get("display")?.value_type_name).toBe("Display");
    expect(surface.properties.get("display")?.accepts_auto_px).toBe(false);
    expect(surface.properties.get("display")?.is_shorthand).toBe(false);

    expect(surface.properties.get("width")?.python_name).toBe("width");
    expect(surface.properties.get("width")?.value_type_name).toBe("WidthValue");
    expect(surface.properties.get("width")?.accepts_auto_px).toBe(true);

    expect(surface.properties.get("border-radius")?.python_name).toBe("border_radius");
    expect(surface.properties.get("border-radius")?.value_type_name).toBe("BorderRadiusValue");
    expect(surface.properties.get("border-radius")?.accepts_auto_px).toBe(true);

    expect(surface.properties.get("margin")?.is_shorthand).toBe(true);
    expect(surface.properties.get("padding")?.is_shorthand).toBe(true);
    expect(surface.properties.get("border")?.is_shorthand).toBe(true);
    expect(surface.properties.get("box-shadow")?.is_shorthand).toBe(true);

    expect(surface.properties.get("color")?.value_type_name).toBe("ColorValue");
    expect(surface.properties.get("font-family")?.value_type_name).toBe("CssValue");
    expect(surface.properties.get("cursor")?.value_type_name).toBe("CssValue");
    expect(surface.properties.get("list-style")?.value_type_name).toBe("CssValue");
    expect(surface.properties.get("font-size")?.value_type_name).toBe("LengthPercentage");
    expect(surface.properties.get("line-height")?.value_type_name).toBe("LineHeightValue");
    expect(surface.properties.get("line-height")?.accepts_auto_px).toBe(false);
    expect(surface.properties.get("opacity")?.accepts_auto_px).toBe(false);
    expect(surface.properties.get("z-index")?.accepts_auto_px).toBe(false);

    expect(surface.media_features.get("min-width")?.python_name).toBe("min_width");
    expect(surface.media_features.get("prefers-color-scheme")?.value_type_name).toBe(
      "PrefersColorScheme",
    );

    expect(surface.value_aliases.get("Display")?.kind).toBe("union");
    expect(surface.value_aliases.get("NamedColor")?.kind).toBe("union");
    expect(surface.value_aliases.get("NamedColor")).toMatchObject({
      kind: "union",
      options: expect.arrayContaining([{ kind: "literal", value: "rebeccapurple" }]),
    });
    expect(surface.value_aliases.get("ColorKeyword")).toMatchObject({
      kind: "union",
      options: expect.arrayContaining([
        { kind: "reference", name: "NamedColor" },
        { kind: "literal", value: "transparent" },
        { kind: "literal", value: "currentColor" },
      ]),
    });
    expect(surface.value_aliases.get("ColorValue")).toMatchObject({
      kind: "union",
      options: expect.arrayContaining([
        { kind: "reference", name: "ColorKeyword" },
        { kind: "primitive", name: "str" },
        { kind: "reference", name: "CssColor" },
        { kind: "reference", name: "CssValue" },
      ]),
    });
    expect(surface.value_aliases.get("Length")).toMatchObject({
      kind: "union",
      options: expect.arrayContaining([
        { kind: "reference", name: "CssLength" },
        { kind: "primitive", name: "str" },
        { kind: "reference", name: "CssValue" },
      ]),
    });
    expect(surface.value_aliases.get("WidthValue")).toMatchObject({
      kind: "union",
      options: expect.arrayContaining([
        { kind: "primitive", name: "str" },
        { kind: "reference", name: "CssValue" },
      ]),
    });
    expect(surface.value_aliases.get("SpacingShorthand")).toMatchObject({
      kind: "union",
      options: expect.arrayContaining([
        { kind: "primitive", name: "str" },
        { kind: "reference", name: "CssValue" },
      ]),
    });
    expect(surface.value_aliases.get("Display")).toMatchObject({
      kind: "union",
      options: expect.arrayContaining([
        { kind: "literal", value: "flex" },
        { kind: "primitive", name: "str" },
        { kind: "literal", value: "inline-flex" },
        { kind: "reference", name: "CssValue" },
      ]),
    });
    expect(surface.value_aliases.get("ShadowValue")).toMatchObject({
      kind: "union",
      options: expect.arrayContaining([
        { kind: "primitive", name: "str" },
        { kind: "reference", name: "CssValue" },
      ]),
    });
    expect(surface.value_aliases.get("TransitionValue")).toMatchObject({
      kind: "union",
      options: expect.arrayContaining([
        { kind: "primitive", name: "str" },
        { kind: "reference", name: "CssValue" },
      ]),
    });
    expect(surface.value_aliases.get("Opacity")).toMatchObject({
      kind: "union",
      options: expect.arrayContaining([
        { kind: "primitive", name: "float" },
        { kind: "reference", name: "CssValue" },
      ]),
    });
  });
});
