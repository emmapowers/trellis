import { describe, expect, it } from "vitest";

import { extract_react_surface } from "../src/sources/react_ts.js";

describe("react source extraction", () => {
  it("extracts input type literal union and onClick event", async () => {
    const surface = await extract_react_surface();
    const input = surface.elements.get("input");
    expect(input).toBeDefined();
    expect(input?.attributes.get("type")?.kind).toBe("union");
    expect(input?.events.has("onClick")).toBe(true);
  });
});
