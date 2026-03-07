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

function collect_references(type_expr: TypeExpr, names: Set<string>): void {
  if (type_expr.kind === "reference") {
    names.add(type_expr.name);
    return;
  }
  if (type_expr.kind === "style_object") {
    return;
  }
  if (type_expr.kind === "nullable" || type_expr.kind === "array") {
    collect_references(type_expr.item, names);
    return;
  }
  if (type_expr.kind === "union") {
    for (const option of type_expr.options) {
      collect_references(option, names);
    }
    return;
  }
  if (type_expr.kind === "callable") {
    for (const param of type_expr.params) {
      collect_references(param, names);
    }
    collect_references(type_expr.returns, names);
    return;
  }
  if (type_expr.kind === "object") {
    for (const field of Object.values(type_expr.fields)) {
      collect_references(field, names);
    }
  }
}

function event_handler_imports(document: IrDocument): string[] {
  const attributes_by_id = index_attributes(document.attributes);
  const names = new Set<string>();

  for (const element of document.elements.filter((entry) => entry.namespace === "html")) {
    for (const attribute_id of element.attributes) {
      const attribute = attributes_by_id.get(attribute_id);
      if (!attribute) {
        continue;
      }
      collect_references(attribute.type_expr, names);
    }
  }

  return [...names]
    .filter((name) => name.endsWith("Handler"))
    .sort((left, right) => left.localeCompare(right));
}

function parameter_annotation(element: ElementDef, attribute: AttributeDef): string {
  if (element.tag_name === "input" && attribute.name_python === "type") {
    return "InputType";
  }
  return render_type_expr(attribute.type_expr);
}

function parameter_default(element: ElementDef, attribute: AttributeDef): string | undefined {
  if (attribute.default !== undefined) {
    if (typeof attribute.default === "string") {
      return JSON.stringify(attribute.default);
    }
    if (attribute.default === null) {
      return "None";
    }
    return String(attribute.default);
  }
  if (attribute.required) {
    return undefined;
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

function render_attribute_parameters(
  element: ElementDef,
  attributes_by_id: Map<string, AttributeDef>,
): string[] {
  const lines: string[] = [];
  for (const attribute_id of element.attributes) {
    const attribute = attributes_by_id.get(attribute_id);
    if (!attribute) {
      continue;
    }
    lines.push(render_parameter(element, attribute));
  }
  return lines;
}

function render_public_helper_overloads(
  element: ElementDef,
  attributes_by_id: Map<string, AttributeDef>,
): string[] {
  if (element.text_behavior !== "public_helper" || !element.is_container) {
    return [];
  }

  const attribute_parameters = render_attribute_parameters(element, attributes_by_id);
  return [
    "@overload",
    `def ${element.python_name}(`,
    "    inner_text: str,",
    "    /,",
    "    *,",
    ...attribute_parameters,
    "    data: Mapping[str, DataValue] | None = None,",
    ") -> Element: ...",
    "",
    "",
    "@overload",
    `def ${element.python_name}(`,
    "    *,",
    ...attribute_parameters,
    "    data: Mapping[str, DataValue] | None = None,",
    ") -> HtmlContainerElement: ...",
    "",
    "",
  ];
}

function render_element_function(
  element: ElementDef,
  attributes_by_id: Map<string, AttributeDef>,
): string {
  const lines: string[] = [];
  lines.push(...render_public_helper_overloads(element, attributes_by_id));

  const decorator_args = [`"${element.tag_name}"`];

  if (element.is_container) {
    decorator_args.push("is_container=True");
  }
  if (element.python_name.startsWith("_")) {
    decorator_args.push(`name="${element.python_name.slice(1)}"`);
  }

  lines.push(`@html_element(${decorator_args.join(", ")})`);
  lines.push(`def ${element.python_name}(`);
  if (element.text_behavior === "public_helper") {
    lines.push("    inner_text: str | None = None,");
    lines.push("    /,");
    lines.push("    *,");
  } else {
    lines.push("    *,");
  }

  lines.push(...render_attribute_parameters(element, attributes_by_id));

  lines.push("    data: Mapping[str, DataValue] | None = None,");
  const return_type = element.text_behavior === "public_helper" ? "Element" : element.is_container ? "HtmlContainerElement" : "Element";
  lines.push(`) -> ${return_type}:`);
  lines.push(`    """Generated raw ${element.tag_name} binding."""`);
  lines.push("    ...");

  return lines.join("\n");
}

function emit_trellis_html_module(document: IrDocument): string {
  const attributes_by_id = index_attributes(document.attributes);
  const handler_imports = event_handler_imports(document);
  const html_elements = document.elements.filter((element) => element.namespace === "html");
  const rendered_elements = html_elements
    .map((element) => render_element_function(element, attributes_by_id))
    .join("\n\n\n");
  const typing_imports = ["Literal"];
  if (html_elements.some((element) => element.text_behavior === "public_helper" && element.is_container)) {
    typing_imports.push("overload");
  }
  const exported_names = html_elements.map((element) => `    "${element.python_name}",`).join("\n");

  const events_import_block =
    handler_imports.length === 0
      ? ""
      : `from trellis.html.events import (
${handler_imports.map((name) => `    ${name},`).join("\n")}
)`;
  const first_party_imports = [
    "from trellis.core.rendering.element import Element",
    "from trellis.html.base import HtmlContainerElement, Style, html_element",
    ...(events_import_block ? [events_import_block] : []),
  ].join("\n");

  return `"""Generated runtime-aligned HTML wrappers.

This module is intentionally scoped to the first generated HTML slice:
_A, Div, Img, and Input.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import ${typing_imports.join(", ")}

${first_party_imports}

__all__ = [
${exported_names}
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
