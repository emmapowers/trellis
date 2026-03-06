import type { TypeExpr } from "../ir/types.js";
import { read_source, resolve_react_types_path } from "./ts_helpers.js";

interface ReactElementSurface {
  attributes: Map<string, TypeExpr>;
  events: Set<string>;
}

export interface ReactEventBinding {
  prop_name: string;
  dom_event_name: string;
  react_handler_alias: string;
  react_event_interface: string;
  payload_name: string;
  typed_handler_name: string;
  handler_name: string;
}

export interface ReactSurface {
  elements: Map<string, ReactElementSurface>;
  event_bindings: Map<string, ReactEventBinding>;
}

interface InterfaceDef {
  extends_names: string[];
  properties: Map<string, { optional: boolean; type_string: string }>;
}

type AliasMap = Map<string, string>;

function primitive(name: "str" | "int" | "float" | "bool" | "none"): TypeExpr {
  return { kind: "primitive", name };
}

function nullable(item: TypeExpr): TypeExpr {
  return { kind: "nullable", item };
}

function reference(name: string): TypeExpr {
  return { kind: "reference", name };
}

function union(...options: TypeExpr[]): TypeExpr {
  return {
    kind: "union",
    options: options.flatMap((option) => (option.kind === "union" ? option.options : [option])),
  };
}

function normalize_ws(value: string): string {
  return value.replace(/\s+/g, " ").trim();
}

function strip_comments(value: string): string {
  return value
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/\/\/.*$/gm, "");
}

function split_top_level(value: string, delimiter: string): string[] {
  const parts: string[] = [];
  let depth_paren = 0;
  let depth_bracket = 0;
  let depth_brace = 0;
  let current = "";

  for (let index = 0; index < value.length; index += 1) {
    const char = value[index];
    if (char === "(") depth_paren += 1;
    if (char === ")") depth_paren -= 1;
    if (char === "[") depth_bracket += 1;
    if (char === "]") depth_bracket -= 1;
    if (char === "{") depth_brace += 1;
    if (char === "}") depth_brace -= 1;

    if (
      char === delimiter &&
      depth_paren === 0 &&
      depth_bracket === 0 &&
      depth_brace === 0
    ) {
      const part = current.trim();
      if (part) {
        parts.push(part);
      }
      current = "";
      continue;
    }

    current += char;
  }

  const trailing = current.trim();
  if (trailing) {
    parts.push(trailing);
  }

  return parts;
}

function extract_interface_header(source: string, interface_name: string): string | undefined {
  const marker = `interface ${interface_name}`;
  const start = source.indexOf(marker);
  if (start === -1) {
    return undefined;
  }

  const open_brace = source.indexOf("{", start);
  if (open_brace === -1) {
    return undefined;
  }

  return source.slice(start, open_brace);
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

function extract_interface_names(header: string | undefined): string[] {
  if (!header || !header.includes("extends")) {
    return [];
  }

  const extends_block = header.slice(header.indexOf("extends") + "extends".length);
  return split_top_level(extends_block, ",")
    .map((entry) => entry.replace(/^React\./, "").replace(/<[\s\S]*>/g, "").trim())
    .filter(Boolean);
}

function extract_interface_properties(
  block: string,
): Map<string, { optional: boolean; type_string: string }> {
  const properties = new Map<string, { optional: boolean; type_string: string }>();
  const stripped = strip_comments(block);
  for (const statement of split_top_level(stripped, ";")) {
    const entry = normalize_ws(statement);
    if (!entry || entry.startsWith("[") || entry.includes("(") && entry.indexOf("(") < entry.indexOf(":")) {
      continue;
    }

    const match = entry.match(/^([A-Za-z_$][A-Za-z0-9_$]*)(\?)?:\s*([\s\S]+)$/);
    if (!match) {
      continue;
    }
    properties.set(match[1], {
      optional: match[2] === "?",
      type_string: match[3].trim(),
    });
  }

  return properties;
}

function collect_interface_defs(
  source: string,
  interface_names: Iterable<string>,
): Map<string, InterfaceDef> {
  const defs = new Map<string, InterfaceDef>();
  const queue = [...interface_names];

  while (queue.length > 0) {
    const interface_name = queue.shift();
    if (!interface_name || defs.has(interface_name)) {
      continue;
    }

    const header = extract_interface_header(source, interface_name);
    const block = extract_interface_block(source, interface_name);
    if (!header || !block) {
      continue;
    }

    const extends_names = extract_interface_names(header);
    defs.set(interface_name, {
      extends_names,
      properties: extract_interface_properties(block),
    });

    queue.push(...extends_names);
  }

  return defs;
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

function extract_intrinsic_interfaces(source: string): Map<string, string> {
  const block = extract_interface_block(source, "IntrinsicElements");
  const element_interfaces = new Map<string, string>();
  const element_regex =
    /^\s*([a-z][A-Za-z0-9_-]*)\??:\s*React\.DetailedHTMLProps<React\.([A-Za-z0-9_]+)</gm;
  let match = element_regex.exec(block);
  while (match) {
    element_interfaces.set(match[1], match[2]);
    match = element_regex.exec(block);
  }
  return element_interfaces;
}

function extract_alias_sources(source: string): AliasMap {
  const aliases = new Map<string, string>();
  const alias_regex = /type\s+([A-Za-z0-9_]+)\s*=([\s\S]*?);/g;

  let match = alias_regex.exec(source);
  while (match) {
    aliases.set(match[1], match[2].trim());
    match = alias_regex.exec(source);
  }

  return aliases;
}

function event_dom_name(prop_name: string): string {
  const base_name = prop_name.slice(2);
  if (base_name === "DoubleClick") {
    return "dblclick";
  }
  return base_name.toLowerCase();
}

function payload_name_for_binding(
  prop_name: string,
  react_event_interface: string,
): string {
  if (prop_name === "onScroll") {
    return "ScrollEvent";
  }
  if (prop_name === "onSubmit") {
    return "FormEvent";
  }
  if (react_event_interface === "SyntheticEvent") {
    return "BaseEvent";
  }
  return react_event_interface;
}

function typed_handler_name_for_payload(payload_name: string): string {
  if (payload_name === "BaseEvent") {
    return "EventHandler";
  }
  return `${payload_name}Handler`;
}

function handler_name_for_payload(payload_name: string): string {
  if (payload_name === "BaseEvent") {
    return "EventHandler";
  }
  return `${payload_name.replace(/Event$/, "")}Handler`;
}

function parse_react_event_binding(
  prop_name: string,
  type_string: string,
): ReactEventBinding | undefined {
  const normalized = normalize_ws(type_string);
  const match =
    normalized.match(/^([A-Za-z0-9_]+EventHandler)(?:<[\s\S]*>)?$/) ??
    normalized.match(/^EventHandler<([A-Za-z0-9_]+Event)(?:<[\s\S]*>)?>$/);
  if (!match) {
    return undefined;
  }

  const react_handler_alias = match[1] ?? "EventHandler";
  const react_event_interface = react_handler_alias.replace(/Handler$/, "");
  const payload_name = payload_name_for_binding(prop_name, react_event_interface);

  return {
    prop_name,
    dom_event_name: event_dom_name(prop_name),
    react_handler_alias,
    react_event_interface,
    payload_name,
    typed_handler_name: typed_handler_name_for_payload(payload_name),
    handler_name: handler_name_for_payload(payload_name),
  };
}

export async function extract_react_event_bindings(): Promise<Map<string, ReactEventBinding>> {
  const types_path = resolve_react_types_path();
  const source = await read_source(types_path);
  const dom_attributes = extract_interface_properties(extract_interface_block(source, "DOMAttributes<T>"));
  const bindings = new Map<string, ReactEventBinding>();

  for (const [prop_name, property] of dom_attributes) {
    if (!prop_name.startsWith("on")) {
      continue;
    }

    const union_parts = split_top_level(normalize_ws(property.type_string), "|")
      .map(normalize_union_option)
      .filter((option) => option !== "undefined");
    if (union_parts.length !== 1) {
      continue;
    }

    const binding = parse_react_event_binding(prop_name, union_parts[0]);
    if (binding) {
      bindings.set(prop_name, binding);
    }
  }

  return bindings;
}

function array_item_type(type_name: string): TypeExpr | undefined {
  if (type_name === "string") {
    return primitive("str");
  }
  return undefined;
}

function normalize_union_option(option: string): string {
  return normalize_ws(option.replace(/^\((.*)\)$/, "$1"));
}

function resolve_alias_type(
  alias_name: string,
  aliases: AliasMap,
  cache: Map<string, TypeExpr | undefined>,
): TypeExpr | undefined {
  if (cache.has(alias_name)) {
    return cache.get(alias_name);
  }

  const alias_source = aliases.get(alias_name);
  if (!alias_source) {
    return undefined;
  }

  // Seed the cache before recursion so self-references settle to fallback behavior.
  cache.set(alias_name, undefined);
  const resolved = parse_type_expr(alias_source, aliases, alias_name, cache);
  cache.set(alias_name, resolved ?? primitive("str"));
  return cache.get(alias_name);
}

function parse_named_type(
  type_name: string,
  aliases: AliasMap,
  prop_name: string,
  cache: Map<string, TypeExpr | undefined>,
): TypeExpr | undefined {
  if (prop_name === "style" && type_name === "CSSProperties") {
    return reference("Style");
  }

  if (type_name === "string") {
    return primitive("str");
  }
  if (type_name === "number") {
    return union(primitive("int"), primitive("float"));
  }
  if (type_name === "boolean" || type_name === "Booleanish") {
    return primitive("bool");
  }
  if (type_name === "null") {
    return primitive("none");
  }
  if (type_name === "any") {
    if (prop_name === "download") {
      return union(primitive("str"), primitive("bool"));
    }
    return primitive("str");
  }

  const array_match = type_name.match(/^(?:readonly\s+)?(.+)\[\]$/);
  if (array_match) {
    const item = array_item_type(array_match[1].trim());
    if (item) {
      return { kind: "array", item };
    }
  }

  if (aliases.has(type_name)) {
    return resolve_alias_type(type_name, aliases, cache);
  }

  if (type_name.startsWith('"') && type_name.endsWith('"')) {
    return {
      kind: "literal",
      value: type_name.slice(1, -1),
    };
  }

  const event_binding = parse_react_event_binding(prop_name, type_name);
  if (event_binding) {
    return reference(event_binding.handler_name);
  }

  return undefined;
}

function parse_type_expr(
  type_string: string,
  aliases: AliasMap,
  prop_name: string,
  cache: Map<string, TypeExpr | undefined>,
): TypeExpr | undefined {
  const normalized = normalize_ws(type_string);
  const union_parts = split_top_level(normalized, "|").map(normalize_union_option);
  const is_nullable = union_parts.includes("undefined");
  const filtered_parts = union_parts.filter(
    (option) => option !== "undefined" && option !== "(string & {})" && option !== "string & {}",
  );

  const parsed_options = filtered_parts
    .map((option) => parse_named_type(option, aliases, prop_name, cache))
    .filter((option): option is TypeExpr => option !== undefined);

  if (parsed_options.length === 0) {
    return undefined;
  }

  const base_expr =
    parsed_options.length === 1 ? parsed_options[0] : union(...parsed_options);

  return is_nullable ? nullable(base_expr) : base_expr;
}

function collect_interface_properties_recursive(
  interface_name: string,
  defs: Map<string, InterfaceDef>,
  aliases: AliasMap,
  properties: Map<string, TypeExpr>,
  event_bindings: Map<string, ReactEventBinding>,
  visited: Set<string>,
): void {
  if (visited.has(interface_name)) {
    return;
  }
  visited.add(interface_name);

  const def = defs.get(interface_name);
  if (!def) {
    return;
  }

  for (const parent_name of def.extends_names) {
    collect_interface_properties_recursive(
      parent_name,
      defs,
      aliases,
      properties,
      event_bindings,
      visited,
    );
  }

  for (const [prop_name, property] of def.properties) {
    const event_binding = event_bindings.get(prop_name);
    if (event_binding) {
      properties.set(prop_name, nullable(reference(event_binding.handler_name)));
      continue;
    }

    const parsed = parse_type_expr(property.type_string, aliases, prop_name, new Map());
    if (parsed) {
      if (property.optional && parsed.kind !== "nullable") {
        properties.set(prop_name, nullable(parsed));
      } else {
        properties.set(prop_name, parsed);
      }
    }
  }
}

export async function extract_react_surface(): Promise<ReactSurface> {
  const types_path = resolve_react_types_path();
  const source = await read_source(types_path);
  const global_events = extract_dom_event_names(source);
  const intrinsic_interfaces = extract_intrinsic_interfaces(source);
  const aliases = extract_alias_sources(source);
  const interface_defs = collect_interface_defs(source, intrinsic_interfaces.values());
  const event_bindings = await extract_react_event_bindings();

  const elements = new Map<string, ReactElementSurface>();
  for (const [element_name, interface_name] of intrinsic_interfaces) {
    const attributes = new Map<string, TypeExpr>();
    collect_interface_properties_recursive(
      interface_name,
      interface_defs,
      aliases,
      attributes,
      event_bindings,
      new Set<string>(),
    );

    elements.set(element_name, {
      attributes,
      events: new Set(global_events),
    });
  }

  return {
    elements,
    event_bindings,
  };
}
