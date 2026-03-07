import type { AttributeDef, ElementDef, IrDocument, TypeExpr } from "../../ir/types.js";
import { render_type_expr } from "../python/render_types.js";
import { render_generated_module_docstring } from "./generated_metadata.js";

export interface TrellisModulePayload {
  path: string;
  content: string;
}

interface HtmlFamily {
  module_name: string;
  title: string;
  tags: Set<string>;
}

interface AttributeTypeAlias {
  name: string;
  body: TypeExpr;
  attribute_ids: string[];
}

const HTML_FAMILIES: HtmlFamily[] = [
  {
    module_name: "document_metadata",
    title: "document metadata",
    tags: new Set([
      "base",
      "body",
      "head",
      "html",
      "link",
      "meta",
      "style",
      "title",
    ]),
  },
  {
    module_name: "sectioning_and_layout",
    title: "sectioning and layout",
    tags: new Set([
      "address",
      "article",
      "aside",
      "blockquote",
      "center",
      "details",
      "dialog",
      "div",
      "figcaption",
      "figure",
      "footer",
      "header",
      "hgroup",
      "main",
      "nav",
      "search",
      "section",
      "summary",
    ]),
  },
  {
    module_name: "text_content",
    title: "text content",
    tags: new Set([
      "abbr",
      "b",
      "bdi",
      "bdo",
      "big",
      "br",
      "cite",
      "code",
      "data",
      "del",
      "dfn",
      "em",
      "h1",
      "h2",
      "h3",
      "h4",
      "h5",
      "h6",
      "hr",
      "i",
      "ins",
      "kbd",
      "mark",
      "p",
      "pre",
      "q",
      "rp",
      "rt",
      "ruby",
      "s",
      "samp",
      "small",
      "span",
      "strong",
      "sub",
      "sup",
      "time",
      "u",
      "wbr",
    ]),
  },
  {
    module_name: "lists",
    title: "lists",
    tags: new Set(["dd", "dl", "dt", "li", "menu", "ol", "ul"]),
  },
  {
    module_name: "forms",
    title: "forms",
    tags: new Set([
      "button",
      "datalist",
      "fieldset",
      "form",
      "input",
      "label",
      "legend",
      "meter",
      "optgroup",
      "option",
      "output",
      "progress",
      "select",
      "textarea",
    ]),
  },
  {
    module_name: "table_content",
    title: "table content",
    tags: new Set(["caption", "col", "colgroup", "table", "tbody", "td", "tfoot", "th", "thead", "tr"]),
  },
  {
    module_name: "image_and_multimedia",
    title: "image and multimedia",
    tags: new Set(["area", "audio", "img", "map", "picture", "source", "track", "video"]),
  },
  {
    module_name: "embedded_content",
    title: "embedded content",
    tags: new Set(["canvas", "embed", "iframe", "object", "param"]),
  },
  {
    module_name: "interactive_elements",
    title: "interactive elements",
    tags: new Set(["a"]),
  },
  {
    module_name: "scripting_and_templates",
    title: "scripting and templates",
    tags: new Set(["noscript", "script", "slot", "template"]),
  },
  {
    module_name: "obsolete",
    title: "obsolete elements",
    tags: new Set(["keygen", "menuitem"]),
  },
];

function index_attributes(attributes: AttributeDef[]): Map<string, AttributeDef> {
  const by_id = new Map<string, AttributeDef>();
  for (const attribute of attributes) {
    by_id.set(attribute.id, attribute);
  }
  return by_id;
}

function strip_nullable(type_expr: TypeExpr): { base: TypeExpr; nullable: boolean } {
  if (type_expr.kind === "nullable") {
    return { base: type_expr.item, nullable: true };
  }
  return { base: type_expr, nullable: false };
}

function type_expr_contains_literal(type_expr: TypeExpr): boolean {
  switch (type_expr.kind) {
    case "literal":
      return true;
    case "nullable":
    case "array":
      return type_expr_contains_literal(type_expr.item);
    case "union":
      return type_expr.options.some((option) => type_expr_contains_literal(option));
    case "callable":
      return (
        type_expr.params.some((param) => type_expr_contains_literal(param)) ||
        type_expr_contains_literal(type_expr.returns)
      );
    case "object":
      return Object.values(type_expr.fields).some((field) => type_expr_contains_literal(field));
    default:
      return false;
  }
}

function type_expr_key(type_expr: TypeExpr): string {
  switch (type_expr.kind) {
    case "literal":
      return `literal:${JSON.stringify(type_expr.value)}`;
    case "primitive":
      return `primitive:${type_expr.name}`;
    case "reference":
      return `reference:${type_expr.name}`;
    case "style_object":
      return "style_object";
    case "nullable":
      return `nullable:${type_expr_key(type_expr.item)}`;
    case "array":
      return `array:${type_expr_key(type_expr.item)}`;
    case "union":
      return `union:${type_expr.options.map((option) => type_expr_key(option)).join("|")}`;
    case "callable":
      return `callable:${type_expr.params.map((param) => type_expr_key(param)).join(",")}=>${type_expr_key(type_expr.returns)}`;
    case "object":
      return `object:${Object.entries(type_expr.fields)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([name, field]) => `${name}:${type_expr_key(field)}`)
        .join(",")}`;
  }
}

function to_pascal_case(name: string): string {
  return name
    .split("_")
    .filter((part) => part.length > 0)
    .map((part) => part[0]!.toUpperCase() + part.slice(1))
    .join("");
}

function alias_name_for_attribute(attribute: AttributeDef): string | undefined {
  if (attribute.id === "html:input:type") {
    return "InputType";
  }
  if (attribute.name_python === "type") {
    return undefined;
  }
  return to_pascal_case(attribute.name_python);
}

function build_attribute_type_aliases(
  document: IrDocument,
  elements: ElementDef[],
): AttributeTypeAlias[] {
  const attributes_by_id = index_attributes(document.attributes);
  const usage_counts = new Map<string, number>();
  for (const element of elements) {
    for (const attribute_id of element.attributes) {
      usage_counts.set(attribute_id, (usage_counts.get(attribute_id) ?? 0) + 1);
    }
  }

  const groups = new Map<
    string,
    {
      alias_name: string;
      body: TypeExpr;
      attribute_ids: Set<string>;
      usage_count: number;
      automatic: boolean;
    }
  >();

  for (const [attribute_id, usage_count] of usage_counts) {
    const attribute = attributes_by_id.get(attribute_id);
    if (!attribute) {
      continue;
    }
    const alias_name = alias_name_for_attribute(attribute);
    if (!alias_name) {
      continue;
    }
    const { base } = strip_nullable(attribute.type_expr);
    if (!type_expr_contains_literal(base)) {
      continue;
    }

    const automatic = attribute.id !== "html:input:type";
    const key = automatic
      ? `${alias_name}:${type_expr_key(base)}`
      : attribute.id;
    const group = groups.get(key);
    if (group) {
      group.attribute_ids.add(attribute.id);
      group.usage_count += usage_count;
      continue;
    }
    groups.set(key, {
      alias_name,
      body: base,
      attribute_ids: new Set([attribute.id]),
      usage_count,
      automatic,
    });
  }

  const alias_name_keys = new Map<string, string[]>();
  for (const [key, group] of groups) {
    const keys = alias_name_keys.get(group.alias_name) ?? [];
    keys.push(key);
    alias_name_keys.set(group.alias_name, keys);
  }

  return [...groups.entries()]
    .filter(([_, group]) => group.usage_count > 1 || !group.automatic)
    .filter(([key, group]) => {
      const conflicting_keys = alias_name_keys.get(group.alias_name) ?? [];
      return conflicting_keys.length === 1 || !group.automatic || group.alias_name === "InputType";
    })
    .map(([_, group]) => ({
      name: group.alias_name,
      body: group.body,
      attribute_ids: [...group.attribute_ids].sort((left, right) => left.localeCompare(right)),
    }))
    .sort((left, right) => left.name.localeCompare(right.name));
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

function event_handler_imports(
  document: IrDocument,
  elements: ElementDef[],
): string[] {
  const attributes_by_id = index_attributes(document.attributes);
  const names = new Set<string>();

  for (const element of elements) {
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

function attribute_alias_name(
  aliases_by_attribute_id: Map<string, AttributeTypeAlias>,
  attribute: AttributeDef,
): string | undefined {
  return aliases_by_attribute_id.get(attribute.id)?.name;
}

function parameter_annotation(
  attribute: AttributeDef,
  aliases_by_attribute_id: Map<string, AttributeTypeAlias>,
): string {
  const alias_name = attribute_alias_name(aliases_by_attribute_id, attribute);
  if (!alias_name) {
    return render_type_expr(attribute.type_expr);
  }
  return attribute.type_expr.kind === "nullable" ? `${alias_name} | None` : alias_name;
}

function render_multiline_literal_union(type_expr: TypeExpr): string[] {
  if (type_expr.kind !== "union" || !type_expr.options.every((option) => option.kind === "literal")) {
    return [render_type_expr(type_expr)];
  }

  return [
    "Literal[",
    ...type_expr.options.map((option) => `    ${JSON.stringify(option.value)},`),
    "]",
  ];
}

function render_type_alias_lines(alias: AttributeTypeAlias): string[] {
  if (
    alias.body.kind === "union" &&
    alias.body.options.every((option) => option.kind === "literal")
  ) {
    return [`${alias.name} = Literal[`, ...alias.body.options.map((option) => `    ${JSON.stringify(option.value)},`), "]"];
  }
  return [`${alias.name} = ${render_type_expr(alias.body)}`];
}

function emit_attribute_types_module(
  aliases: AttributeTypeAlias[],
  generated_at: string,
): TrellisModulePayload {
  const exported_names = aliases.map((alias) => `    "${alias.name}",`).join("\n");
  const alias_lines = aliases.flatMap((alias, index) => {
    const lines = render_type_alias_lines(alias);
    if (index === 0) {
      return lines;
    }
    return ["", ...lines];
  });

  return {
    path: "src/trellis/html/_generated_attribute_types.py",
    content: `${render_generated_module_docstring("Generated HTML attribute type aliases.", generated_at)}

from __future__ import annotations

from typing import Literal

__all__ = [
${exported_names}
]

${alias_lines.join("\n")}
`,
  };
}

function attribute_type_imports(
  elements: ElementDef[],
  aliases_by_attribute_id: Map<string, AttributeTypeAlias>,
): string[] {
  const names = new Set<string>();
  for (const element of elements) {
    for (const attribute_id of element.attributes) {
      const alias = aliases_by_attribute_id.get(attribute_id);
      if (alias) {
        names.add(alias.name);
      }
    }
  }
  return [...names].sort((left, right) => left.localeCompare(right));
}

function type_expr_uses_literal(type_expr: TypeExpr): boolean {
  switch (type_expr.kind) {
    case "literal":
      return true;
    case "nullable":
    case "array":
      return type_expr_uses_literal(type_expr.item);
    case "union":
      return type_expr.options.some((option) => type_expr_uses_literal(option));
    case "callable":
      return (
        type_expr.params.some((param) => type_expr_uses_literal(param)) ||
        type_expr_uses_literal(type_expr.returns)
      );
    case "object":
      return Object.values(type_expr.fields).some((field) => type_expr_uses_literal(field));
    default:
      return false;
  }
}

function multiline_parameter_annotation(
  attribute: AttributeDef,
  aliases_by_attribute_id: Map<string, AttributeTypeAlias>,
): string[] {
  const alias_name = attribute_alias_name(aliases_by_attribute_id, attribute);
  if (alias_name) {
    return [attribute.type_expr.kind === "nullable" ? `${alias_name} | None` : alias_name];
  }

  if (
    attribute.type_expr.kind === "nullable" &&
    attribute.type_expr.item.kind === "union" &&
    attribute.type_expr.item.options.every((option) => option.kind === "literal")
  ) {
    return ["(", ...render_multiline_literal_union(attribute.type_expr.item), "    | None", ")"];
  }

  if (
    attribute.type_expr.kind === "union" &&
    attribute.type_expr.options.every((option) => option.kind === "literal")
  ) {
    return render_multiline_literal_union(attribute.type_expr);
  }

  return [render_type_expr(attribute.type_expr)];
}

function parameter_default(attribute: AttributeDef): string | undefined {
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

function render_parameter(
  attribute: AttributeDef,
  aliases_by_attribute_id: Map<string, AttributeTypeAlias>,
): string {
  const annotation = parameter_annotation(attribute, aliases_by_attribute_id);
  const default_value = parameter_default(attribute);
  const single_line = `    ${attribute.name_python}: ${annotation}${
    default_value === undefined ? "," : ` = ${default_value},`
  }`;

  if (single_line.length <= 88) {
    return single_line;
  }

  const annotation_lines = multiline_parameter_annotation(attribute, aliases_by_attribute_id);
  if (annotation_lines.length === 1) {
    return single_line;
  }

  if (default_value === undefined) {
    return [
      `    ${attribute.name_python}: ${annotation_lines[0]}`,
      ...annotation_lines.slice(1, -1).map((line) => `    ${line}`),
      `    ${annotation_lines.at(-1)!},`,
    ].join("\n");
  }
  return [
    `    ${attribute.name_python}: ${annotation_lines[0]}`,
    ...annotation_lines.slice(1, -1).map((line) => `    ${line}`),
    `    ${annotation_lines.at(-1)!} = ${default_value},`,
  ].join("\n");
}

function render_attribute_parameters(
  element: ElementDef,
  attributes_by_id: Map<string, AttributeDef>,
  aliases_by_attribute_id: Map<string, AttributeTypeAlias>,
): string[] {
  const lines: string[] = [];
  for (const attribute_id of element.attributes) {
    const attribute = attributes_by_id.get(attribute_id);
    if (!attribute) {
      continue;
    }
    lines.push(render_parameter(attribute, aliases_by_attribute_id));
  }
  return lines;
}

function render_public_helper_overloads(
  element: ElementDef,
  attributes_by_id: Map<string, AttributeDef>,
  aliases_by_attribute_id: Map<string, AttributeTypeAlias>,
): string[] {
  if (element.text_behavior !== "public_helper" || !element.is_container) {
    return [];
  }

  const attribute_parameters = render_attribute_parameters(
    element,
    attributes_by_id,
    aliases_by_attribute_id,
  );
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
  aliases_by_attribute_id: Map<string, AttributeTypeAlias>,
): string {
  const lines: string[] = [];
  lines.push(...render_public_helper_overloads(element, attributes_by_id, aliases_by_attribute_id));

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

  lines.push(...render_attribute_parameters(element, attributes_by_id, aliases_by_attribute_id));

  lines.push("    data: Mapping[str, DataValue] | None = None,");
  const return_type =
    element.text_behavior === "public_helper"
      ? "Element"
      : element.is_container
        ? "HtmlContainerElement"
        : "Element";
  lines.push(`) -> ${return_type}:`);
  lines.push(`    """<${element.tag_name} />"""`);
  lines.push("    ...");

  return lines.join("\n");
}

function family_for_tag(tag_name: string): HtmlFamily {
  for (const family of HTML_FAMILIES) {
    if (family.tags.has(tag_name)) {
      return family;
    }
  }
  throw new Error(`No HTML family configured for <${tag_name}>.`);
}

function emit_family_module(
  document: IrDocument,
  family: HtmlFamily,
  elements: ElementDef[],
  aliases_by_attribute_id: Map<string, AttributeTypeAlias>,
  generated_at: string,
): TrellisModulePayload {
  const attributes_by_id = index_attributes(document.attributes);
  const handler_imports = event_handler_imports(document, elements);
  const attribute_type_import_names = attribute_type_imports(elements, aliases_by_attribute_id);
  const rendered_elements = elements
    .map((element) => render_element_function(element, attributes_by_id, aliases_by_attribute_id))
    .join("\n\n\n");
  const needs_literal_import = elements.some((element) =>
    element.attributes.some((attribute_id) => {
      if (aliases_by_attribute_id.has(attribute_id)) {
        return false;
      }
      const attribute = attributes_by_id.get(attribute_id);
      return attribute ? type_expr_uses_literal(attribute.type_expr) : false;
    }),
  );
  const typing_imports = needs_literal_import ? ["Literal"] : [];
  if (elements.some((element) => element.text_behavior === "public_helper" && element.is_container)) {
    typing_imports.push("overload");
  }
  const needs_container_type = elements.some(
    (element) => element.is_container || (element.text_behavior === "public_helper" && element.is_container),
  );
  const exported_names = elements
    .map((element) => element.python_name)
    .sort()
    .map((name) => `    "${name}",`)
    .join("\n");

  const events_import_block =
    handler_imports.length === 0
      ? ""
      : `from trellis.html._generated_events import (
${handler_imports.map((name) => `    ${name},`).join("\n")}
)`;
  const attribute_types_import =
    attribute_type_import_names.length === 0
      ? ""
      : attribute_type_import_names.length === 1
        ? `from trellis.html._generated_attribute_types import ${attribute_type_import_names[0]}`
        : `from trellis.html._generated_attribute_types import (
${attribute_type_import_names.map((name) => `    ${name},`).join("\n")}
)`;
  const first_party_imports = [
    "from trellis.core.rendering.element import Element",
    "from trellis.html._style_runtime import StyleInput",
    `from trellis.html.base import ${needs_container_type ? "HtmlContainerElement, html_element" : "html_element"}`,
    ...(attribute_types_import ? [attribute_types_import] : []),
    ...(events_import_block ? [events_import_block] : []),
  ].join("\n");

  const parts = [
    render_generated_module_docstring(`Generated HTML ${family.title} elements.`, generated_at),
    "",
    "from __future__ import annotations",
    "",
    "from collections.abc import Mapping",
    ...(typing_imports.length > 0 ? [`from typing import ${typing_imports.join(", ")}`] : []),
    "",
    first_party_imports,
    "",
    "__all__ = [",
    exported_names,
    "]",
    "",
    "DataValue = str | int | float | bool | None",
    "",
    "",
    rendered_elements,
  ];

  return {
    path: `src/trellis/html/_generated_${family.module_name}.py`,
    content: `${parts.join("\n").trimEnd()}\n`,
  };
}

function emit_runtime_aggregator(
  family_modules: Array<{ family: HtmlFamily; elements: ElementDef[] }>,
  generated_at: string,
): TrellisModulePayload {
  const nonEmptyFamilies = family_modules.filter((entry) => entry.elements.length > 0);
  const importBlocks = nonEmptyFamilies.map((entry) => {
    const names = entry.elements
      .map((element) => element.python_name)
      .sort()
      .map((name) => `    ${name},`)
      .join("\n");
    return `from trellis.html._generated_${entry.family.module_name} import (
${names}
)`;
  });

  const exportedNames = nonEmptyFamilies
    .flatMap((entry) => entry.elements.map((element) => element.python_name))
    .sort()
    .map((name) => `    "${name}",`)
    .join("\n");

  return {
    path: "src/trellis/html/_generated_runtime.py",
    content: `${render_generated_module_docstring("Generated HTML runtime exports.", generated_at)}

from __future__ import annotations

${importBlocks.join("\n\n")}

__all__ = [
${exportedNames}
]
`,
  };
}

export function build_trellis_html_modules(
  document: IrDocument,
  generated_at: string,
): TrellisModulePayload[] {
  const html_elements = document.elements
    .filter((element) => element.namespace === "html")
    .slice()
    .sort((left, right) => left.python_name.localeCompare(right.python_name));
  const attribute_type_aliases = build_attribute_type_aliases(document, html_elements);
  const aliases_by_attribute_id = new Map<string, AttributeTypeAlias>();
  for (const alias of attribute_type_aliases) {
    for (const attribute_id of alias.attribute_ids) {
      aliases_by_attribute_id.set(attribute_id, alias);
    }
  }

  const grouped = new Map<string, { family: HtmlFamily; elements: ElementDef[] }>();
  for (const family of HTML_FAMILIES) {
    grouped.set(family.module_name, { family, elements: [] });
  }

  for (const element of html_elements) {
    const family = family_for_tag(element.tag_name);
    grouped.get(family.module_name)?.elements.push(element);
  }

  const familyModules = HTML_FAMILIES.map((family) => grouped.get(family.module_name)!)
    .filter((entry) => entry.elements.length > 0);

  return [
    ...(attribute_type_aliases.length > 0
      ? [emit_attribute_types_module(attribute_type_aliases, generated_at)]
      : []),
    emit_runtime_aggregator(familyModules, generated_at),
    ...familyModules.map((entry) =>
      emit_family_module(
        document,
        entry.family,
        entry.elements,
        aliases_by_attribute_id,
        generated_at,
      ),
    ),
  ];
}
