import { describe, expect, it } from "vitest";

import { build_trellis_events_module } from "../src/emit/targets/trellis_events.js";
import type { DataclassDef, EventDef, EventHandlerDef, IrDocument } from "../src/ir/types.js";

function sampleDataclass(name: string, fields: DataclassDef["fields"], base?: string): DataclassDef {
  return {
    name,
    frozen: true,
    base,
    fields,
    source: {
      winner: "webref",
      contributors: ["webref"],
      reason: "idl_payload",
      source_version: "@webref/idl",
    },
  };
}

function sampleEvent(
  dom_event_name: string,
  payload_name: string,
  handler_name: string,
): EventDef {
  return {
    id: `html:global:on_${dom_event_name.replace(/[^a-z]/g, "_")}`,
    name_source: `on${dom_event_name[0]!.toUpperCase()}${dom_event_name.slice(1)}`,
    name_python: `on_${dom_event_name.replace(/[^a-z]/g, "_")}`,
    dom_event_name,
    payload_name,
    handler_name,
    source: {
      winner: "react_ts",
      contributors: ["react_ts"],
      reason: "runtime_precedence",
      source_version: "@types/react@19.2.14",
    },
  };
}

function sampleHandler(payload_name: string): EventHandlerDef {
  return {
    payload_name,
    typed_handler_name: `${payload_name}Handler`,
    handler_name: `${payload_name}Handler`,
    source: {
      winner: "react_ts",
      contributors: ["react_ts"],
      reason: "runtime_precedence",
      source_version: "@types/react@19.2.14",
    },
  };
}

describe("trellis events target", () => {
  it("builds a generated events module with source-native payloads and event map", () => {
    const ir: IrDocument = {
      elements: [],
      attributes: [],
      events: [
        sampleEvent("click", "MouseEvent", "MouseEventHandler"),
        sampleEvent("change", "Event", "EventHandler"),
        sampleEvent("load", "Event", "EventHandler"),
        sampleEvent("play", "Event", "EventHandler"),
      ],
      event_handlers: [
        sampleHandler("Event"),
        sampleHandler("UIEvent"),
        sampleHandler("MouseEvent"),
        sampleHandler("FocusEvent"),
        sampleHandler("InputEvent"),
        sampleHandler("SubmitEvent"),
      ],
      dataclasses: [
        sampleDataclass("Event", [
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
              winner: "webref",
              contributors: ["webref"],
              reason: "idl_payload",
              source_version: "@webref/idl",
            },
          },
        ]),
        sampleDataclass(
          "UIEvent",
          [
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
          "Event",
        ),
        sampleDataclass(
          "FocusEvent",
          [
            {
              name_source: "relatedTarget",
              name_python: "related_target",
              type_expr: {
                kind: "nullable",
                item: { kind: "primitive", name: "str" },
              },
              default: null,
              source: {
                winner: "webref",
                contributors: ["webref"],
                reason: "idl_payload",
                source_version: "@webref/idl",
              },
            },
          ],
          "UIEvent",
        ),
        sampleDataclass(
          "InputEvent",
          [
            {
              name_source: "data",
              name_python: "data",
              type_expr: {
                kind: "nullable",
                item: { kind: "primitive", name: "str" },
              },
              default: null,
              source: {
                winner: "webref",
                contributors: ["webref"],
                reason: "idl_payload",
                source_version: "@webref/idl",
              },
            },
            {
              name_source: "dataTransfer",
              name_python: "data_transfer",
              type_expr: {
                kind: "nullable",
                item: { kind: "reference", name: "DataTransfer" },
              },
              default: null,
              source: {
                winner: "webref",
                contributors: ["webref"],
                reason: "idl_payload",
                source_version: "@webref/idl",
              },
            },
          ],
          "UIEvent",
        ),
        sampleDataclass(
          "SubmitEvent",
          [
            {
              name_source: "submitter",
              name_python: "submitter",
              type_expr: {
                kind: "nullable",
                item: { kind: "primitive", name: "str" },
              },
              default: null,
              source: {
                winner: "webref",
                contributors: ["webref"],
                reason: "idl_payload",
                source_version: "@webref/idl",
              },
            },
          ],
          "Event",
        ),
        sampleDataclass(
          "MouseEvent",
          [
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
          "UIEvent",
        ),
        sampleDataclass(
          "DataTransfer",
          [
            {
              name_source: "dropEffect",
              name_python: "drop_effect",
              type_expr: { kind: "primitive", name: "str" },
              default: "none",
              source: {
                winner: "webref",
                contributors: ["webref"],
                reason: "runtime_payload",
                source_version: "@webref/idl",
              },
            },
          ],
        ),
      ],
      attribute_patterns: [],
    };

    const payload = build_trellis_events_module(ir, "2026-03-07T12:00:00.000Z");
    expect(payload.path).toBe("src/trellis/html/_generated_events.py");
    expect(payload.content).toContain("Generated typed event definitions for trellis.html.");
    expect(payload.content).toContain("Generated by html-codegen.");
    expect(payload.content).toContain("class FocusEvent(UIEvent)");
    expect(payload.content).toContain("class InputEvent(UIEvent)");
    expect(payload.content).toContain("class SubmitEvent(Event)");
    expect(payload.content).toContain("related_target: str | None = None");
    expect(payload.content).toContain("data_transfer: DataTransfer | None = None");
    expect(payload.content).toContain("submitter: str | None = None");
    expect(payload.content).toContain("EventHandler = Callable[[Event], None]");
    expect(payload.content).toContain("FocusEventHandler = Callable[[FocusEvent], None]");
    expect(payload.content).toContain("InputEventHandler = Callable[[InputEvent], None]");
    expect(payload.content).toContain('"click": MouseEvent');
    expect(payload.content).toContain('"change": Event');
    expect(payload.content).toContain('"load": Event');
    expect(payload.content).toContain('"play": Event');
    expect(payload.content).toContain("def get_event_class(event_type: str) -> type[Event]:");
  });
});
