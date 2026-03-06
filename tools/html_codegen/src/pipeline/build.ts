import type { AttributeDef, ElementDef, IrDocument, SourceProvenance, TypeExpr } from "../ir/types.js";
import { extract_react_surface } from "../sources/react_ts.js";

interface SliceElementConfig {
  tag_name: "a" | "div" | "img" | "input";
  python_name: "_A" | "Div" | "Img" | "Input";
  is_container: boolean;
  prop_names: string[];
}

const GLOBAL_PROP_NAMES = new Set(["className", "id", "style"]);

const SLICE_CONFIG: SliceElementConfig[] = [
  {
    tag_name: "a",
    python_name: "_A",
    is_container: true,
    prop_names: [
      "href",
      "target",
      "rel",
      "download",
      "className",
      "style",
      "id",
      "onClick",
      "onDoubleClick",
      "onContextMenu",
      "onKeyDown",
      "onKeyUp",
    ],
  },
  {
    tag_name: "div",
    python_name: "Div",
    is_container: true,
    prop_names: [
      "className",
      "style",
      "id",
      "onClick",
      "onDoubleClick",
      "onContextMenu",
      "onMouseEnter",
      "onMouseLeave",
      "onKeyDown",
      "onKeyUp",
      "onScroll",
      "onWheel",
      "onDragStart",
      "onDrag",
      "onDragEnd",
      "onDragEnter",
      "onDragOver",
      "onDragLeave",
      "onDrop",
    ],
  },
  {
    tag_name: "img",
    python_name: "Img",
    is_container: false,
    prop_names: [
      "src",
      "alt",
      "width",
      "height",
      "loading",
      "className",
      "style",
      "id",
      "onClick",
      "onDoubleClick",
      "onContextMenu",
    ],
  },
  {
    tag_name: "input",
    python_name: "Input",
    is_container: false,
    prop_names: [
      "type",
      "value",
      "placeholder",
      "disabled",
      "readOnly",
      "name",
      "checked",
      "required",
      "min",
      "max",
      "step",
      "pattern",
      "maxLength",
      "autoComplete",
      "autoFocus",
      "accept",
      "multiple",
      "onChange",
      "onInput",
      "onFocus",
      "onBlur",
      "onKeyDown",
      "onKeyUp",
      "className",
      "style",
      "id",
    ],
  },
];

function react_source(): SourceProvenance {
  return {
    winner: "react_ts",
    contributors: ["react_ts"],
    reason: "runtime_precedence",
    source_version: "@types/react@19.2.14",
  };
}

function primitive(name: "str" | "int" | "float" | "bool" | "none"): TypeExpr {
  return { kind: "primitive", name };
}

function union(...options: TypeExpr[]): TypeExpr {
  return { kind: "union", options };
}

function to_snake_case(name: string): string {
  return name
    .replace(/([a-z0-9])([A-Z])/g, "$1_$2")
    .replace(/-/g, "_")
    .toLowerCase();
}

function with_type_overrides(tag_name: string, prop_name: string, type_expr: TypeExpr): TypeExpr {
  if (tag_name === "img" && prop_name === "src" && type_expr.kind === "nullable") {
    return type_expr.item;
  }

  if (tag_name === "input" && prop_name === "type" && type_expr.kind === "nullable") {
    return type_expr.item;
  }

  return type_expr;
}

function build_attribute_def(
  tag_name: string,
  prop_name: string,
  type_expr: TypeExpr,
): AttributeDef {
  const name_python = to_snake_case(prop_name);
  const is_global = GLOBAL_PROP_NAMES.has(prop_name);

  return {
    id: is_global ? `html:global:${name_python}` : `html:${tag_name}:${name_python}`,
    name_source: prop_name,
    name_python,
    applies_to: is_global ? "global" : "element",
    type_expr: with_type_overrides(tag_name, prop_name, type_expr),
    required: false,
    category: "standard",
    source: react_source(),
  };
}

function build_element(config: SliceElementConfig, attribute_ids: string[]): ElementDef {
  return {
    namespace: "html",
    tag_name: config.tag_name,
    python_name: config.python_name,
    is_container: config.is_container,
    attributes: attribute_ids,
    events: [],
    source: react_source(),
  };
}

export async function build_ir_document(): Promise<IrDocument> {
  const react_surface = await extract_react_surface();
  const attributes_by_id = new Map<string, AttributeDef>();
  const elements: ElementDef[] = [];

  for (const config of SLICE_CONFIG) {
    const surface = react_surface.elements.get(config.tag_name);
    if (!surface) {
      throw new Error(`Missing react surface for <${config.tag_name}>.`);
    }

    const attribute_ids = config.prop_names.map((prop_name) => {
      const type_expr = surface.attributes.get(prop_name);
      if (!type_expr) {
        throw new Error(`Missing react prop ${config.tag_name}.${prop_name}.`);
      }

      const attribute = build_attribute_def(config.tag_name, prop_name, type_expr);
      attributes_by_id.set(attribute.id, attribute);
      return attribute.id;
    });

    elements.push(build_element(config, attribute_ids));
  }

  return {
    elements,
    attributes: [...attributes_by_id.values()],
    events: [],
    attribute_patterns: [
      {
        name: "data",
        python_param_name: "data",
        dom_prefix: "data-",
        key_style: "dom_suffix",
        value_type_expr: union(
          primitive("str"),
          primitive("int"),
          primitive("float"),
          primitive("bool"),
          primitive("none"),
        ),
      },
    ],
  };
}
