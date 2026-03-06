import type { TypeExpr } from "../ir/types.js";
import { read_source, resolve_react_types_path } from "./ts_helpers.js";

interface ReactElementSurface {
  attributes: Map<string, TypeExpr>;
  events: Set<string>;
}

export interface ReactSurface {
  elements: Map<string, ReactElementSurface>;
}

function extract_interface_block(source: string, interface_name: string): string {
  const marker = `interface ${interface_name}`;
  const start = source.indexOf(marker);
  if (start === -1) {
    return "";
  }

  const open_brace = source.indexOf("{", start);
  if (open_brace === -1) {
    return "";
  }

  let depth = 0;
  for (let index = open_brace; index < source.length; index += 1) {
    const char = source[index];
    if (char === "{") {
      depth += 1;
      continue;
    }
    if (char === "}") {
      depth -= 1;
      if (depth === 0) {
        return source.slice(open_brace + 1, index);
      }
    }
  }
  return "";
}

function extract_dom_event_names(source: string): Set<string> {
  const block = extract_interface_block(source, "DOMAttributes<T>");
  const event_names = new Set<string>();
  const event_regex = /^\s*(on[A-Z][A-Za-z0-9]*)\??:\s*/gm;
  let match = event_regex.exec(block);
  while (match) {
    event_names.add(match[1]);
    match = event_regex.exec(block);
  }
  return event_names;
}

function extract_intrinsic_elements(source: string): string[] {
  const block = extract_interface_block(source, "IntrinsicElements");
  const element_names: string[] = [];
  const element_regex = /^\s*([a-z][A-Za-z0-9_-]*)\??:\s*/gm;
  let match = element_regex.exec(block);
  while (match) {
    element_names.push(match[1]);
    match = element_regex.exec(block);
  }
  return element_names;
}

function extract_string_literal_union(
  source: string,
  alias_name: string,
): TypeExpr | undefined {
  const alias_regex = new RegExp(`type\\s+${alias_name}\\s*=([\\s\\S]*?);`);
  const alias_match = source.match(alias_regex);
  if (!alias_match) {
    return undefined;
  }
  const body = alias_match[1];
  const literal_regex = /"([^"]+)"/g;
  const options: TypeExpr[] = [];
  let literal_match = literal_regex.exec(body);
  while (literal_match) {
    options.push({
      kind: "literal",
      value: literal_match[1],
    });
    literal_match = literal_regex.exec(body);
  }
  if (options.length === 0) {
    return undefined;
  }
  return {
    kind: "union",
    options,
  };
}

export async function extract_react_surface(): Promise<ReactSurface> {
  const types_path = resolve_react_types_path();
  const source = await read_source(types_path);
  const global_events = extract_dom_event_names(source);
  const intrinsic_elements = extract_intrinsic_elements(source);
  const input_type_union = extract_string_literal_union(source, "HTMLInputTypeAttribute");

  const elements = new Map<string, ReactElementSurface>();
  for (const element_name of intrinsic_elements) {
    elements.set(element_name, {
      attributes: new Map<string, TypeExpr>(),
      events: new Set(global_events),
    });
  }

  const input = elements.get("input");
  if (input && input_type_union) {
    input.attributes.set("type", input_type_union);
  }

  return {
    elements,
  };
}
