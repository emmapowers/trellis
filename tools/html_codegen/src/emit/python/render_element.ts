import type { AttributeDef, ElementDef } from "../../ir/types.js";
import { render_type_expr } from "./render_types.js";

export function render_element_function(
  element: ElementDef,
  attributes: AttributeDef[],
): string {
  const lines: string[] = [];
  const args = attributes
    .sort((left, right) => left.name_python.localeCompare(right.name_python))
    .map((attribute) => `    ${attribute.name_python}: ${render_type_expr(attribute.type_expr)} | None = None,`);

  lines.push(`def ${element.python_name}(`);
  lines.push("    *,");
  lines.push(...args);
  lines.push(") -> Element:");
  lines.push(`    \"\"\"Generated ${element.tag_name} element.\"\"\"`);
  lines.push("    ...");
  lines.push("");

  return lines.join("\n");
}
