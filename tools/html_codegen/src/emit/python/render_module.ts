import type { AttributeDef, IrDocument } from "../../ir/types.js";
import { render_element_function } from "./render_element.js";

function index_attributes(attributes: AttributeDef[]): Map<string, AttributeDef> {
  const by_id = new Map<string, AttributeDef>();
  for (const attribute of attributes) {
    by_id.set(attribute.id, attribute);
  }
  return by_id;
}

export function emit_python_module(document: IrDocument): string {
  const lines: string[] = [
    "from typing import Any, Callable, Literal, Mapping",
    "",
    "from trellis.core.rendering.element import Element",
    "",
    "DataValue = str | int | float | bool | None",
    "",
  ];

  const attributes_by_id = index_attributes(document.attributes);
  const elements = [...document.elements]
    .filter((element) => element.namespace === "html")
    .sort((left, right) => left.python_name.localeCompare(right.python_name));

  for (const element of elements) {
    const attributes = element.attributes
      .map((attribute_id) => attributes_by_id.get(attribute_id))
      .filter((value): value is AttributeDef => value !== undefined);
    lines.push(render_element_function(element, attributes));
  }

  return lines.join("\n");
}
