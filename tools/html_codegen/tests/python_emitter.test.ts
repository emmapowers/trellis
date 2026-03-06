import { describe, expect, it } from "vitest";

import { emit_python_module } from "../src/emit/python/render_module.js";
import type { IrDocument } from "../src/ir/types.js";

describe("python emitter", () => {
  it("emits snake_case params and strict Literal unions", () => {
    const ir: IrDocument = {
      elements: [
        {
          namespace: "html",
          tag_name: "input",
          python_name: "Input",
          is_container: false,
          attributes: ["html:input:type", "html:global:class_name"],
          events: [],
          source: {
            winner: "react_ts",
            contributors: ["react_ts"],
            reason: "runtime_precedence",
            source_version: "@types/react@19.2.14",
          },
        },
      ],
      attributes: [
        {
          id: "html:input:type",
          name_source: "type",
          name_python: "type",
          applies_to: "element",
          type_expr: {
            kind: "union",
            options: [
              { kind: "literal", value: "text" },
              { kind: "literal", value: "number" },
            ],
          },
          required: false,
          category: "standard",
          source: {
            winner: "react_ts",
            contributors: ["react_ts"],
            reason: "runtime_precedence",
            source_version: "@types/react@19.2.14",
          },
        },
        {
          id: "html:global:class_name",
          name_source: "className",
          name_python: "class_name",
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
      attribute_patterns: [],
    };

    const source = emit_python_module(ir);
    expect(source).toContain("def Input(");
    expect(source).toContain("type: Literal[");
    expect(source).toContain("class_name:");
  });
});
