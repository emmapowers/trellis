import type { AttributeDef, IrDocument, TypeExpr } from "../ir/types.js";
import { extract_react_surface } from "../sources/react_ts.js";

function to_pascal_case(tag_name: string): string {
  if (tag_name === "i") {
    return "Italic";
  }
  return tag_name
    .split(/[-_]/g)
    .map((part) => part.slice(0, 1).toUpperCase() + part.slice(1))
    .join("");
}

function make_input_type_attribute(type_expr: TypeExpr) {
  return {
    id: "html:input:type",
    name_source: "type",
    name_python: "type",
    applies_to: "element" as const,
    type_expr,
    required: false,
    category: "standard" as const,
    source: {
      winner: "react_ts" as const,
      contributors: ["react_ts"],
      reason: "runtime_precedence",
      source_version: "@types/react",
    },
  };
}

export async function build_ir_document(): Promise<IrDocument> {
  const react_surface = await extract_react_surface();

  const global_class_name_attribute = {
    id: "html:global:class_name",
    name_source: "className",
    name_python: "class_name",
    applies_to: "global" as const,
    type_expr: { kind: "primitive", name: "str" } as const,
    required: false,
    category: "standard" as const,
    source: {
      winner: "react_ts" as const,
      contributors: ["react_ts"],
      reason: "runtime_precedence",
      source_version: "@types/react",
    },
  };

  const attributes: AttributeDef[] = [global_class_name_attribute];
  const input_surface = react_surface.elements.get("input");
  if (input_surface) {
    const input_type_expr = input_surface.attributes.get("type");
    if (input_type_expr) {
      attributes.push(make_input_type_attribute(input_type_expr));
    }
  }

  const html_tag_regex = /^[a-z][a-z0-9]*$/;
  const elements = [...react_surface.elements.keys()]
    .filter((name) => html_tag_regex.test(name))
    .sort((left, right) => left.localeCompare(right))
    .map((tag_name) => ({
      namespace: "html" as const,
      tag_name,
      python_name: to_pascal_case(tag_name),
      is_container: true,
      attributes: [
        "html:global:class_name",
        ...(tag_name === "input" ? ["html:input:type"] : []),
      ],
      events: [],
      source: {
        winner: "react_ts" as const,
        contributors: ["react_ts"],
        reason: "runtime_precedence",
        source_version: "@types/react",
      },
    }));

  return {
    elements,
    attributes,
    events: [],
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
  };
}
