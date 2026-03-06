import { describe, expect, it } from "vitest";

import { extract_webref_element_surface } from "../src/sources/webref_elements.js";
import { extract_webref_event_names } from "../src/sources/webref_events.js";
import { extract_webref_idl_names } from "../src/sources/webref_idl.js";

describe("webref extraction", () => {
  it("loads html element, events, and idl metadata", async () => {
    const elements = await extract_webref_element_surface();
    const events = await extract_webref_event_names();
    const idl_names = await extract_webref_idl_names();

    expect(elements.has("button")).toBe(true);
    expect(events.size).toBeGreaterThan(0);
    expect(idl_names.has("HTMLButtonElement")).toBe(true);
  });
});
