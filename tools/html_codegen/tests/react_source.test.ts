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

    const div = surface.elements.get("div");
    expect(div).toBeDefined();
    expect(div?.attributes.get("className")?.kind).toBe("nullable");
    expect(div?.attributes.get("style")?.kind).toBe("nullable");
    expect(div?.attributes.get("onScroll")?.kind).toBe("nullable");

    const image = surface.elements.get("img");
    expect(image).toBeDefined();
    expect(image?.attributes.get("src")?.kind).toBe("nullable");
    expect(image?.attributes.get("loading")?.kind).toBe("nullable");

    const input = surface.elements.get("input");
    expect(input).toBeDefined();
    expect(input?.attributes.get("type")?.kind).toBe("nullable");
    expect(input?.attributes.get("readOnly")?.kind).toBe("nullable");
    expect(input?.attributes.get("autoComplete")?.kind).toBe("nullable");
    expect(input?.attributes.get("onChange")?.kind).toBe("nullable");
  });
});
