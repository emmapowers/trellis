import type {
  DataclassDef,
  DataclassFieldDef,
  EventDef,
  EventHandlerDef,
  IrDocument,
} from "../../ir/types.js";
import { render_type_expr } from "../python/render_types.js";
import { render_generated_module_docstring } from "./generated_metadata.js";

export interface TrellisModulePayload {
  path: string;
  content: string;
}

function event_reference(name: string): string {
  return `https://developer.mozilla.org/en-US/docs/Web/API/${name}`;
}

function exported_names(document: IrDocument): string[] {
  const names = new Set<string>();
  for (const dataclass_def of document.dataclasses) {
    names.add(dataclass_def.name);
  }
  for (const event_handler of document.event_handlers) {
    names.add(event_handler.typed_handler_name);
  }
  const middle_names = [...names].sort(
    (left, right) =>
      left.toLowerCase().localeCompare(right.toLowerCase()) || left.localeCompare(right),
  );
  return ["EVENT_TYPE_MAP", ...middle_names, "get_event_class"];
}

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
  lines.push(`    """Generated event type for \`${dataclass_def.name}\`.`);
  lines.push("");
  lines.push("    Derived from standard DOM event interfaces and React event bindings.");
  lines.push(`    Reference: ${event_reference(dataclass_def.name)}`);
  lines.push('    """');

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

function unique_event_payload_map(events: EventDef[]): Array<[string, string]> {
  const payloads = new Map<string, string>();
  for (const event of events) {
    payloads.set(event.dom_event_name, event.payload_name);
  }
  return [...payloads.entries()].sort(([left], [right]) => left.localeCompare(right));
}

function emit_trellis_events_module(document: IrDocument, generated_at: string): string {
  const rendered_dataclasses = document.dataclasses.map((entry) => render_dataclass(entry)).join("\n\n\n");
  const typed_handlers = document.event_handlers.map((entry) => render_typed_handler(entry)).join("\n");
  const event_map_lines = unique_event_payload_map(document.events).map(
    ([dom_event_name, payload_name]) => `    "${dom_event_name}": ${payload_name},`,
  );
  const root_event_name = document.dataclasses.find((entry) => !entry.base)?.name ?? "Event";

  return `${render_generated_module_docstring(
    "Generated typed event definitions for trellis.html.",
    generated_at,
    [
      "Internal codegen artifact for event payloads and handlers.",
      "Reference: https://developer.mozilla.org/en-US/docs/Web/API",
    ],
  )}

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

__all__ = [
${exported_names(document).map((name) => `    "${name}",`).join("\n")}
]


${rendered_dataclasses}


${typed_handlers}


EVENT_TYPE_MAP: dict[str, type[${root_event_name}]] = {
${event_map_lines.join("\n")}
}


def get_event_class(event_type: str) -> type[${root_event_name}]:
    return EVENT_TYPE_MAP.get(event_type, ${root_event_name})
`.trimEnd() + "\n";
}

export function build_trellis_events_module(
  document: IrDocument,
  generated_at: string,
): TrellisModulePayload {
  return {
    path: "src/trellis/html/_generated_events.py",
    content: emit_trellis_events_module(document, generated_at),
  };
}
