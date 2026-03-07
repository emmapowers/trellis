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
          handler_name: "MouseEventHandler",
          payload_name: "MouseEvent",
          source: {
            winner: "react_ts",
            contributors: ["react_ts"],
            reason: "runtime_precedence",
            source_version: "@types/react@19.2.14",
          },
        },
        {
          id: "html:global:on_change",
          name_source: "onChange",
          name_python: "on_change",
          dom_event_name: "change",
          handler_name: "EventHandler",
          payload_name: "Event",
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
          payload_name: "Event",
          typed_handler_name: "EventHandler",
          handler_name: "EventHandler",
          source: {
            winner: "react_ts",
            contributors: ["react_ts"],
            reason: "runtime_precedence",
            source_version: "@types/react@19.2.14",
          },
        },
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
            {
              name_source: "timeStamp",
              name_python: "time_stamp",
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
          name: "UIEvent",
          frozen: true,
          base: "Event",
          fields: [
            {
              name_source: "detail",
              name_python: "detail",
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
        {
          name: "MouseEvent",
          frozen: true,
          base: "UIEvent",
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

    const payload = build_trellis_events_module(ir, "2026-03-07T12:00:00.000Z");
    expect(payload.path).toBe("src/trellis/html/events.py");
    expect(payload.content).toContain("Generated at: 2026-03-07T12:00:00.000Z");
    expect(payload.content).toContain("class Event");
    expect(payload.content).toContain("class UIEvent(Event)");
    expect(payload.content).toContain("class MouseEvent(UIEvent)");
    expect(payload.content).not.toContain("class ChangeEvent");
    expect(payload.content).toContain("EventHandler = Callable[[Event], None]");
    expect(payload.content).toContain("MouseEventHandler = Callable[[MouseEvent], None]");
    expect(payload.content).not.toContain("MouseHandler =");
    expect(payload.content).toContain("alt_key: bool = False");
    expect(payload.content).toContain('"click": MouseEvent');
    expect(payload.content).toContain('"change": Event');
    expect(payload.content).toContain("def get_event_class(event_type: str) -> type[Event]:");
  });
});
