import { describe, expect, it } from "vitest";

import { extract_react_surface } from "../src/sources/react_ts.js";

describe("react source extraction", () => {
  it("extracts the first html slice props from react types", async () => {
    const surface = await extract_react_surface();

    const anchor = surface.elements.get("a");
    expect(anchor).toBeDefined();
    expect(anchor?.attributes.get("href")?.kind).toBe("nullable");
    expect(anchor?.attributes.get("target")?.kind).toBe("nullable");
    expect(anchor?.attributes.get("onClick")?.kind).toBe("nullable");
    expect(anchor?.attributes.get("target")).toEqual({
      kind: "nullable",
      item: {
        kind: "union",
        options: [
          { kind: "literal", value: "_self" },
          { kind: "literal", value: "_blank" },
          { kind: "literal", value: "_parent" },
          { kind: "literal", value: "_top" },
        ],
      },
    });

    const div = surface.elements.get("div");
    expect(div).toBeDefined();
    expect(div?.attributes.get("className")?.kind).toBe("nullable");
    expect(div?.attributes.get("aria-label")?.kind).toBe("nullable");
    expect(div?.attributes.get("aria-hidden")).toEqual({
      kind: "nullable",
      item: { kind: "primitive", name: "bool" },
    });
    expect(div?.attributes.get("style")?.kind).toBe("nullable");
    expect(div?.attributes.get("style")).toEqual({
      kind: "nullable",
      item: {
        kind: "style_object",
      },
    });
    expect(div?.attributes.get("onScroll")?.kind).toBe("nullable");

    const image = surface.elements.get("img");
    expect(image).toBeDefined();
    expect(image?.attributes.get("src")?.kind).toBe("nullable");
    expect(image?.attributes.get("loading")?.kind).toBe("nullable");
    expect(image?.attributes.get("width")).toEqual({
      kind: "nullable",
      item: {
        kind: "union",
        options: [
          { kind: "primitive", name: "int" },
          { kind: "primitive", name: "float" },
          { kind: "primitive", name: "str" },
        ],
      },
    });

    const input = surface.elements.get("input");
    expect(input).toBeDefined();
    expect(input?.attributes.get("type")?.kind).toBe("nullable");
    expect(input?.attributes.get("readOnly")?.kind).toBe("nullable");
    expect(input?.attributes.get("autoComplete")?.kind).toBe("nullable");
    expect(input?.attributes.get("onChange")?.kind).toBe("nullable");
    expect(input?.attributes.get("value")).toEqual({
      kind: "nullable",
      item: {
        kind: "union",
        options: [
          { kind: "primitive", name: "str" },
          {
            kind: "array",
            item: { kind: "primitive", name: "str" },
          },
          { kind: "primitive", name: "int" },
          { kind: "primitive", name: "float" },
        ],
      },
    });

    const audio = surface.elements.get("audio");
    expect(audio).toBeDefined();
    expect(audio?.attributes.get("autoPlay")?.kind).toBe("nullable");
    expect(audio?.attributes.get("controls")?.kind).toBe("nullable");
    expect(audio?.attributes.get("src")?.kind).toBe("nullable");
  });
});
