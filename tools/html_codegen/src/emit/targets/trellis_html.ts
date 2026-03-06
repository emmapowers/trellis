import type { AttributeDef, ElementDef, IrDocument, TypeExpr } from "../../ir/types.js";
import { render_type_expr } from "../python/render_types.js";

export interface TrellisModulePayload {
  path: string;
  content: string;
}

function index_attributes(attributes: AttributeDef[]): Map<string, AttributeDef> {
  const by_id = new Map<string, AttributeDef>();
  for (const attribute of attributes) {
    by_id.set(attribute.id, attribute);
  }
  return by_id;
}

function input_type_expr(document: IrDocument): TypeExpr | undefined {
  const attributes_by_id = index_attributes(document.attributes);
  return attributes_by_id.get("html:input:type")?.type_expr;
}

function literal_alias_body(type_expr: TypeExpr | undefined): string | undefined {
  if (!type_expr) {
    return undefined;
  }
  if (type_expr.kind === "union") {
    return render_type_expr(type_expr);
  }
  if (type_expr.kind === "nullable" && type_expr.item.kind === "union") {
    return render_type_expr(type_expr.item);
  }
  return undefined;
}

function input_type_alias(document: IrDocument): string {
  const alias_body = literal_alias_body(input_type_expr(document));
  if (!alias_body) {
    return "InputType = str";
  }

  const body = alias_body.slice("Literal[".length, -1);
  const options = body.split(", ").map((option) => `    ${option},`);
  return ["InputType = Literal[", ...options, "]"].join("\n");
}

function parameter_annotation(element: ElementDef, attribute: AttributeDef): string {
  if (element.tag_name === "input" && attribute.name_python === "type") {
    return "InputType";
  }
  return render_type_expr(attribute.type_expr);
}

function parameter_default(element: ElementDef, attribute: AttributeDef): string | undefined {
  if (element.tag_name === "input" && attribute.name_python === "type") {
    return '"text"';
  }
  if (attribute.type_expr.kind === "nullable") {
    return "None";
  }
  return undefined;
}

function render_parameter(element: ElementDef, attribute: AttributeDef): string {
  const annotation = parameter_annotation(element, attribute);
  const default_value = parameter_default(element, attribute);
  if (default_value === undefined) {
    return `    ${attribute.name_python}: ${annotation},`;
  }
  return `    ${attribute.name_python}: ${annotation} = ${default_value},`;
}

function render_element_function(
  element: ElementDef,
  attributes_by_id: Map<string, AttributeDef>,
): string {
  const lines: string[] = [];
  const decorator_args = [`"${element.tag_name}"`];

  if (element.is_container) {
    decorator_args.push("is_container=True");
  }
  if (element.python_name.startsWith("_")) {
    decorator_args.push(`name="${element.python_name.slice(1)}"`);
  }

  lines.push(`@html_element(${decorator_args.join(", ")})`);
  lines.push(`def ${element.python_name}(`);
  lines.push("    *,");
  if (element.python_name === "_A") {
    lines.push("    _text: str | None = None,");
  }

  for (const attribute_id of element.attributes) {
    const attribute = attributes_by_id.get(attribute_id);
    if (!attribute) {
      continue;
    }
    lines.push(render_parameter(element, attribute));
  }

  lines.push("    data: Mapping[str, DataValue] | None = None,");
  lines.push(") -> Element:");
  lines.push(`    """Generated raw ${element.tag_name} binding."""`);
  lines.push("    ...");

  return lines.join("\n");
}

function emit_trellis_html_module(document: IrDocument): string {
  const attributes_by_id = index_attributes(document.attributes);
  const rendered_elements = document.elements
    .filter((element) => element.namespace === "html")
    .map((element) => render_element_function(element, attributes_by_id))
    .join("\n\n\n");

  return `"""Generated runtime-aligned HTML wrappers.

This module is intentionally scoped to the first generated HTML slice:
_A, Div, Img, and Input.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from trellis.core.rendering.element import Element
from trellis.html.base import Style, html_element
from trellis.html.events import (
    ChangeHandler,
    DragHandler,
    FocusHandler,
    InputHandler,
    KeyboardHandler,
    MouseHandler,
    ScrollHandler,
    WheelHandler,
)

__all__ = [
    "_A",
    "Div",
    "Img",
    "Input",
]

DataValue = str | int | float | bool | None
${input_type_alias(document)}


${rendered_elements}`.trimEnd() + "\n";
}

export function build_trellis_html_module(document: IrDocument): TrellisModulePayload {
  return {
    path: "src/trellis/html/_generated_runtime.py",
    content: emit_trellis_html_module(document),
  };
}
