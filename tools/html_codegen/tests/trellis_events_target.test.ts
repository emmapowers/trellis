import { describe, expect, it } from "vitest";

import { build_trellis_events_module } from "../src/emit/targets/trellis_events.js";
import type { IrDocument } from "../src/ir/types.js";

describe("trellis events target", () => {
  it("builds a generated events module with dataclasses, handlers, and event map", () => {
    const ir: IrDocument = {
      elements: [],
      attributes: [],
      events: [
        {
          id: "html:global:on_click",
          name_source: "onClick",
          name_python: "on_click",
          dom_event_name: "click",
          handler_name: "MouseHandler",
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
          handler_name: "MouseHandler",
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
          name: "BaseEvent",
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
            {
              name_source: "timestamp",
              name_python: "timestamp",
              type_expr: { kind: "primitive", name: "float" },
              default: 0,
              source: {
                winner: "trellis_policy",
                contributors: ["react_ts", "trellis_policy"],
                reason: "runtime_payload",
                source_version: "local",
              },
            },
          ],
          source: {
            winner: "webref",
            contributors: ["webref", "trellis_policy"],
            reason: "runtime_payload",
            source_version: "@webref/idl",
          },
        },
        {
          name: "MouseEvent",
          frozen: true,
          base: "BaseEvent",
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
            {
              name_source: "altKey",
              name_python: "alt_key",
              type_expr: { kind: "primitive", name: "bool" },
              default: false,
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
      attribute_patterns: [],
    };

    const payload = build_trellis_events_module(ir);
    expect(payload.path).toBe("src/trellis/html/events.py");
    expect(payload.content).toContain("class BaseEvent");
    expect(payload.content).toContain("class MouseEvent(BaseEvent)");
    expect(payload.content).toContain("MouseEventHandler = Callable[[MouseEvent], None]");
    expect(payload.content).toContain("MouseHandler = EventHandler | MouseEventHandler");
    expect(payload.content).toContain("alt_key: bool = False");
    expect(payload.content).toContain('"click": MouseEvent');
    expect(payload.content).toContain("def get_event_class(event_type: str) -> type[BaseEvent]:");
  });
});
