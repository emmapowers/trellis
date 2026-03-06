import { describe, expect, it } from "vitest";

import { validate_ir } from "../src/validate/validate_ir.js";

describe("policy validation", () => {
  it("rejects non-snake-case python names", () => {
    const result = validate_ir({
      elements: [],
      attributes: [
        {
          id: "html:global:class_name",
          name_source: "className",
          name_python: "className",
          applies_to: "global",
          type_expr: { kind: "primitive", name: "str" },
          required: false,
          category: "standard",
          source: {
            winner: "react_ts",
            contributors: ["react_ts"],
            reason: "runtime_precedence",
            source_version: "@types/react@19.2.14",
          },
        },
      ],
      events: [],
      event_handlers: [],
      dataclasses: [],
      attribute_patterns: [],
    });

    expect(result.ok).toBe(false);
    expect(result.errors.some((error) => error.includes("snake_case"))).toBe(true);
  });
});
