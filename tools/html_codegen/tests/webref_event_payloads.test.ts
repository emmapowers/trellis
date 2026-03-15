import { describe, expect, it } from "vitest";

import { extract_webref_event_payloads } from "../src/sources/webref_event_payloads.js";

describe("webref event payloads", () => {
  it("extracts inheritance and typed fields for event interfaces", async () => {
    const payloads = await extract_webref_event_payloads([
      "Event",
      "MouseEvent",
      "KeyboardEvent",
      "WheelEvent",
      "DragEvent",
    ]);

    expect(payloads.get("Event")).toMatchObject({
      inheritance: null,
    });
    expect(payloads.get("Event")?.fields.find((field) => field.name_source === "type")).toMatchObject({
      name_python: "type",
      type_expr: { kind: "primitive", name: "str" },
    });

    expect(payloads.get("MouseEvent")).toMatchObject({
      inheritance: "UIEvent",
    });
    expect(
      payloads.get("MouseEvent")?.fields.filter((field) =>
        ["clientX", "clientY", "altKey"].includes(field.name_source),
      ),
    ).toHaveLength(3);

    expect(payloads.get("WheelEvent")).toMatchObject({
      inheritance: "MouseEvent",
    });
    expect(payloads.get("WheelEvent")?.fields.find((field) => field.name_source === "deltaMode")).toMatchObject({
      name_python: "delta_mode",
      type_expr: { kind: "primitive", name: "int" },
    });

    expect(payloads.get("DragEvent")).toMatchObject({
      inheritance: "MouseEvent",
    });
  });
});
