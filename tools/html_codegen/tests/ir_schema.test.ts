import { describe, expect, it } from "vitest";

import { ir_schema } from "../src/ir/schema.js";

describe("ir schema", () => {
  it("rejects attribute without provenance winner", () => {
    const parsed = ir_schema.safeParse({
      elements: [],
      attributes: [
        {
          id: "html:div:id",
          name_source: "id",
          name_python: "id",
        },
      ],
      events: [],
      attribute_patterns: [],
    });

    expect(parsed.success).toBe(false);
  });

  it("accepts a minimal valid document", () => {
    const parsed = ir_schema.safeParse({
      elements: [
        {
          namespace: "html",
          tag_name: "div",
          python_name: "Div",
          is_container: true,
          attributes: ["html:global:id"],
          events: ["html:global:on_click"],
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
          id: "html:global:id",
          name_source: "id",
          name_python: "id",
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
        {
          id: "html:global:style",
          name_source: "style",
          name_python: "style",
          applies_to: "global",
          type_expr: { kind: "style_object" },
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
      events: [
        {
          id: "html:global:on_click",
          name_source: "onClick",
          name_python: "on_click",
          dom_event_name: "click",
          handler_name: "MouseEventHandler",
          payload_name: "MouseEvent",
          source: {
            winner: "react_ts",
            contributors: ["react_ts"],
            reason: "runtime_precedence",
            source_version: "@types/react@19.2.14",
          },
        },
      ],
      event_handlers: [
        {
          payload_name: "MouseEvent",
          typed_handler_name: "MouseEventHandler",
          handler_name: "MouseEventHandler",
          source: {
            winner: "react_ts",
            contributors: ["react_ts"],
            reason: "runtime_precedence",
            source_version: "@types/react@19.2.14",
          },
        },
      ],
      dataclasses: [
        {
          name: "Event",
          frozen: true,
          fields: [
            {
              name_source: "type",
              name_python: "type",
              type_expr: { kind: "primitive", name: "str" },
              default: "",
              source: {
                winner: "webref",
                contributors: ["webref"],
                reason: "idl_payload",
                source_version: "@webref/idl",
              },
            },
          ],
          source: {
            winner: "webref",
            contributors: ["webref"],
            reason: "idl_payload",
            source_version: "@webref/idl",
          },
        },
        {
          name: "MouseEvent",
          base: "Event",
          frozen: true,
          fields: [
            {
              name_source: "clientX",
              name_python: "client_x",
              type_expr: { kind: "primitive", name: "int" },
              default: 0,
              source: {
                winner: "webref",
                contributors: ["webref"],
                reason: "idl_payload",
                source_version: "@webref/idl",
              },
            },
          ],
          source: {
            winner: "webref",
            contributors: ["webref"],
            reason: "idl_payload",
            source_version: "@webref/idl",
          },
        },
      ],
      attribute_patterns: [
        {
          name: "data",
          python_param_name: "data",
          dom_prefix: "data-",
          key_style: "dom_suffix",
          value_type_expr: {
            kind: "union",
            options: [
              { kind: "primitive", name: "str" },
              { kind: "primitive", name: "int" },
              { kind: "primitive", name: "float" },
              { kind: "primitive", name: "bool" },
              { kind: "primitive", name: "none" },
            ],
          },
        },
      ],
    });

    expect(parsed.success).toBe(true);
  });
});
