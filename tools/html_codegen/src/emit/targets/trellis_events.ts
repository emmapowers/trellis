import type {
  DataclassDef,
  DataclassFieldDef,
  EventDef,
  EventHandlerDef,
  IrDocument,
} from "../../ir/types.js";
import { render_type_expr } from "../python/render_types.js";

export interface TrellisModulePayload {
  path: string;
  content: string;
}

const EVENTS_ALL_EXPORTS = [
  "EVENT_TYPE_MAP",
  "BaseEvent",
  "ChangeEvent",
  "ChangeEventHandler",
  "ChangeHandler",
  "DragDataTransfer",
  "DragDataTransferFile",
  "DragEvent",
  "DragEventHandler",
  "DragHandler",
  "EventHandler",
  "FocusEvent",
  "FocusEventHandler",
  "FocusHandler",
  "FormEvent",
  "FormEventHandler",
  "FormHandler",
  "InputEvent",
  "InputEventHandler",
  "InputHandler",
  "KeyboardEvent",
  "KeyboardEventHandler",
  "KeyboardHandler",
  "MouseEvent",
  "MouseEventHandler",
  "MouseHandler",
  "ScrollEvent",
  "ScrollEventHandler",
  "ScrollHandler",
  "WheelEvent",
  "WheelEventHandler",
  "WheelHandler",
  "get_event_class",
] as const;

function is_float_type(field: DataclassFieldDef): boolean {
  return (
    field.type_expr.kind === "primitive" && field.type_expr.name === "float"
  ) || (
    field.type_expr.kind === "nullable" &&
    field.type_expr.item.kind === "primitive" &&
    field.type_expr.item.name === "float"
  );
}

function render_default_value(field: DataclassFieldDef): string | undefined {
  if (field.default_factory === "list") {
    return "field(default_factory=list)";
  }
  if (field.default === undefined) {
    return undefined;
  }
  if (typeof field.default === "string") {
    return JSON.stringify(field.default);
  }
  if (field.default === null) {
    return "None";
  }
  if (typeof field.default === "boolean") {
    return field.default ? "True" : "False";
  }
  if (typeof field.default === "number" && is_float_type(field) && Number.isInteger(field.default)) {
    return `${field.default}.0`;
  }
  return String(field.default);
}

function render_dataclass_field(field: DataclassFieldDef): string {
  const annotation = render_type_expr(field.type_expr);
  const default_value = render_default_value(field);
  if (default_value === undefined) {
    return `    ${field.name_python}: ${annotation}`;
  }
  return `    ${field.name_python}: ${annotation} = ${default_value}`;
}

function render_dataclass(dataclass_def: DataclassDef): string {
  const base = dataclass_def.base ? `(${dataclass_def.base})` : "";
  const lines = ["@dataclass(frozen=True)", `class ${dataclass_def.name}${base}:`];

  if (dataclass_def.fields.length === 0) {
    lines.push("    pass");
    return lines.join("\n");
  }

  lines.push(...dataclass_def.fields.map((field) => render_dataclass_field(field)));
  return lines.join("\n");
}

function render_typed_handler(handler: EventHandlerDef): string {
  return `${handler.typed_handler_name} = Callable[[${handler.payload_name}], None] | Callable[[${handler.payload_name}], Awaitable[None]]`;
}

function render_handler_union(handler: EventHandlerDef): string {
  return `${handler.handler_name} = EventHandler | ${handler.typed_handler_name}`;
}

function unique_event_payload_map(events: EventDef[]): Array<[string, string]> {
  const payloads = new Map<string, string>();
  for (const event of events) {
    payloads.set(event.dom_event_name, event.payload_name);
  }
  return [...payloads.entries()].sort(([left], [right]) => left.localeCompare(right));
}

function emit_trellis_events_module(document: IrDocument): string {
  const rendered_dataclasses = document.dataclasses.map((entry) => render_dataclass(entry)).join("\n\n\n");
  const typed_handlers = document.event_handlers.map((entry) => render_typed_handler(entry)).join("\n");
  const handler_unions = document.event_handlers.map((entry) => render_handler_union(entry)).join("\n");
  const event_map_lines = unique_event_payload_map(document.events).map(
    ([dom_event_name, payload_name]) => `    "${dom_event_name}": ${payload_name},`,
  );

  return `"""Generated typed event definitions for HTML elements."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

__all__ = [
${EVENTS_ALL_EXPORTS.map((name) => `    "${name}",`).join("\n")}
]


${rendered_dataclasses}


EventHandler = Callable[[], None] | Callable[[], Awaitable[None]]

${typed_handlers}

${handler_unions}


EVENT_TYPE_MAP: dict[str, type[BaseEvent]] = {
${event_map_lines.join("\n")}
}


def get_event_class(event_type: str) -> type[BaseEvent]:
    return EVENT_TYPE_MAP.get(event_type, BaseEvent)
`.trimEnd() + "\n";
}

export function build_trellis_events_module(document: IrDocument): TrellisModulePayload {
  return {
    path: "src/trellis/html/events.py",
    content: emit_trellis_events_module(document),
  };
}
