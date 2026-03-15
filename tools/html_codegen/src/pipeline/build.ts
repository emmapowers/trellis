import type {
  AttributeDef,
  DataclassDef,
  DataclassFieldDef,
  ElementDef,
  EventDef,
  EventHandlerDef,
  IrDocument,
  SourceProvenance,
  TypeExpr,
} from "../ir/types.js";
import type { ReactEventBinding } from "../sources/react_ts.js";
import { extract_react_surface } from "../sources/react_ts.js";
import { extract_webref_event_payloads } from "../sources/webref_event_payloads.js";

interface ElementPolicy {
  tag_name: string;
  python_name: string;
  is_container: boolean;
  text_behavior: "none" | "public_helper" | "internal_text_prop";
}

interface DataclassFieldConfig {
  source_name?: string;
  name_source?: string;
  name_python?: string;
  type_expr?: TypeExpr;
  default?: string | number | boolean | null;
  default_factory?: "list";
}

interface DataclassConfig {
  name: string;
  base?: string;
  source_interface?: string;
  fields: DataclassFieldConfig[];
  source: SourceProvenance;
}

const GLOBAL_PROP_NAMES = new Set(["className", "id", "style"]);

const PUBLIC_EVENT_PROP_NAMES = [
  "onClick",
  "onDoubleClick",
  "onMouseDown",
  "onMouseUp",
  "onMouseMove",
  "onMouseEnter",
  "onMouseLeave",
  "onMouseOver",
  "onMouseOut",
  "onContextMenu",
  "onKeyDown",
  "onKeyUp",
  "onChange",
  "onInput",
  "onFocus",
  "onBlur",
  "onLoad",
  "onError",
  "onSubmit",
  "onScroll",
  "onWheel",
  "onPlay",
  "onPause",
  "onEnded",
  "onTimeUpdate",
  "onLoadedMetadata",
  "onDragStart",
  "onDrag",
  "onDragEnd",
  "onDragEnter",
  "onDragOver",
  "onDragLeave",
  "onDrop",
] as const;

const PUBLIC_HANDLER_PAYLOAD_NAMES = [
  "Event",
  "UIEvent",
  "MouseEvent",
  "KeyboardEvent",
  "FocusEvent",
  "SubmitEvent",
  "InputEvent",
  "WheelEvent",
  "DragEvent",
] as const;

const EXCLUDED_HTML_TAGS = new Set(["noindex", "webview"]);

const NON_CONTAINER_TAGS = new Set([
  "area",
  "base",
  "br",
  "col",
  "embed",
  "hr",
  "iframe",
  "img",
  "input",
  "keygen",
  "link",
  "menuitem",
  "meta",
  "option",
  "param",
  "rp",
  "script",
  "source",
  "style",
  "textarea",
  "track",
  "title",
  "wbr",
]);

const PUBLIC_TEXT_HELPER_TAGS = new Set([
  "a",
  "abbr",
  "b",
  "bdi",
  "bdo",
  "big",
  "blockquote",
  "button",
  "canvas",
  "caption",
  "cite",
  "code",
  "data",
  "dd",
  "del",
  "dfn",
  "div",
  "dt",
  "em",
  "figcaption",
  "h1",
  "h2",
  "h3",
  "h4",
  "h5",
  "h6",
  "i",
  "iframe",
  "ins",
  "kbd",
  "label",
  "legend",
  "li",
  "mark",
  "object",
  "option",
  "output",
  "p",
  "pre",
  "q",
  "rp",
  "rt",
  "ruby",
  "s",
  "samp",
  "script",
  "small",
  "span",
  "strong",
  "style",
  "sub",
  "summary",
  "sup",
  "td",
  "textarea",
  "th",
  "time",
  "title",
  "u",
]);

const PYTHON_NAME_OVERRIDES = new Map([
  ["a", "_A"],
  ["i", "Italic"],
  ["style", "StyleTag"],
]);

const ATTRIBUTE_DEFAULTS = new Map<string, string | number | boolean | null>([["input:type", "text"]]);

const PYTHON_KEYWORDS = new Set([
  "and",
  "as",
  "assert",
  "async",
  "await",
  "break",
  "case",
  "class",
  "continue",
  "def",
  "del",
  "elif",
  "else",
  "except",
  "false",
  "finally",
  "for",
  "from",
  "global",
  "if",
  "import",
  "in",
  "is",
  "lambda",
  "match",
  "nonlocal",
  "none",
  "not",
  "or",
  "pass",
  "raise",
  "return",
  "true",
  "try",
  "while",
  "with",
  "yield",
]);

const RESERVED_PARAMETER_NAMES = new Set(["data", "inner_text"]);

const DATACLASS_CONFIGS: DataclassConfig[] = [
  {
    name: "Event",
    source_interface: "Event",
    fields: [
      { source_name: "type", default: "" },
      { source_name: "timeStamp", default: 0.0 },
      { source_name: "bubbles", default: false },
      { source_name: "cancelable", default: false },
      { source_name: "defaultPrevented", default: false },
      { source_name: "eventPhase", default: 0 },
      { source_name: "isTrusted", default: false },
    ],
    source: webref_source("idl_payload"),
  },
  {
    name: "UIEvent",
    base: "Event",
    source_interface: "UIEvent",
    fields: [{ source_name: "detail", default: 0 }],
    source: webref_source("idl_payload"),
  },
  {
    name: "MouseEvent",
    base: "UIEvent",
    source_interface: "MouseEvent",
    fields: [
      { source_name: "clientX", default: 0 },
      { source_name: "clientY", default: 0 },
      { source_name: "screenX", default: 0 },
      { source_name: "screenY", default: 0 },
      { source_name: "button", default: 0 },
      { source_name: "buttons", default: 0 },
      { source_name: "altKey", default: false },
      { source_name: "ctrlKey", default: false },
      { source_name: "shiftKey", default: false },
      { source_name: "metaKey", default: false },
    ],
    source: webref_source("idl_payload"),
  },
  {
    name: "KeyboardEvent",
    base: "UIEvent",
    source_interface: "KeyboardEvent",
    fields: [
      { source_name: "key", default: "" },
      { source_name: "code", default: "" },
      { source_name: "location", default: 0 },
      { source_name: "altKey", default: false },
      { source_name: "ctrlKey", default: false },
      { source_name: "shiftKey", default: false },
      { source_name: "metaKey", default: false },
      { source_name: "repeat", default: false },
      { source_name: "isComposing", default: false },
    ],
    source: webref_source("idl_payload"),
  },
  {
    name: "FocusEvent",
    base: "UIEvent",
    source_interface: "FocusEvent",
    fields: [
      {
        name_source: "relatedTarget",
        name_python: "related_target",
        type_expr: { kind: "nullable", item: primitive("str") },
        default: null,
      },
    ],
    source: webref_source("idl_payload"),
  },
  {
    name: "SubmitEvent",
    base: "Event",
    source_interface: "SubmitEvent",
    fields: [
      {
        name_source: "submitter",
        name_python: "submitter",
        type_expr: { kind: "nullable", item: primitive("str") },
        default: null,
      },
    ],
    source: webref_source("idl_payload"),
  },
  {
    name: "InputEvent",
    base: "UIEvent",
    source_interface: "InputEvent",
    fields: [
      { source_name: "data", default: null },
      {
        name_source: "dataTransfer",
        name_python: "data_transfer",
        type_expr: { kind: "nullable", item: { kind: "reference", name: "DataTransfer" } },
        default: null,
      },
      { source_name: "isComposing", default: false },
      { source_name: "inputType", default: "" },
    ],
    source: webref_source("idl_payload"),
  },
  {
    name: "WheelEvent",
    base: "MouseEvent",
    source_interface: "WheelEvent",
    fields: [
      { source_name: "deltaX", default: 0.0 },
      { source_name: "deltaY", default: 0.0 },
      { source_name: "deltaZ", default: 0.0 },
      { source_name: "deltaMode", default: 0 },
    ],
    source: webref_source("idl_payload"),
  },
  {
    name: "File",
    fields: [
      { name_source: "name", name_python: "name", type_expr: primitive("str"), default: "" },
      { name_source: "size", name_python: "size", type_expr: primitive("int"), default: 0 },
      { name_source: "type", name_python: "type", type_expr: primitive("str"), default: "" },
    ],
    source: webref_source("runtime_payload"),
  },
  {
    name: "DataTransfer",
    fields: [
      { name_source: "dropEffect", name_python: "drop_effect", type_expr: primitive("str"), default: "none" },
      {
        name_source: "effectAllowed",
        name_python: "effect_allowed",
        type_expr: primitive("str"),
        default: "none",
      },
      {
        name_source: "types",
        name_python: "types",
        type_expr: { kind: "array", item: primitive("str") },
        default_factory: "list",
      },
      {
        name_source: "files",
        name_python: "files",
        type_expr: { kind: "array", item: { kind: "reference", name: "File" } },
        default_factory: "list",
      },
    ],
    source: webref_source("runtime_payload"),
  },
  {
    name: "DragEvent",
    base: "MouseEvent",
    source_interface: "DragEvent",
    fields: [{ source_name: "dataTransfer", default: null }],
    source: webref_source("idl_payload"),
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

function webref_source(reason: string): SourceProvenance {
  return {
    winner: "webref",
    contributors: ["webref"],
    reason,
    source_version: "@webref/idl",
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

function to_python_param_name(name: string): string {
  const snake_name = to_snake_case(name);
  if (PYTHON_KEYWORDS.has(snake_name) || RESERVED_PARAMETER_NAMES.has(snake_name)) {
    return `${snake_name}_`;
  }
  return snake_name;
}

function to_python_element_name(tag_name: string): string {
  const override = PYTHON_NAME_OVERRIDES.get(tag_name);
  if (override) {
    return override;
  }

  return tag_name
    .split("-")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join("");
}

function build_element_policy(tag_name: string): ElementPolicy | undefined {
  if (EXCLUDED_HTML_TAGS.has(tag_name)) {
    return undefined;
  }

  return {
    tag_name,
    python_name: to_python_element_name(tag_name),
    is_container: !NON_CONTAINER_TAGS.has(tag_name),
    text_behavior: PUBLIC_TEXT_HELPER_TAGS.has(tag_name) ? "public_helper" : "none",
  };
}

function attribute_default(tag_name: string, prop_name: string): string | number | boolean | null | undefined {
  return ATTRIBUTE_DEFAULTS.get(`${tag_name}:${prop_name}`);
}

// Attributes that React types incorrectly assign to elements.
// These are excluded from the generated stubs to match the HTML spec.
const EXCLUDED_ELEMENT_ATTRIBUTES = new Map<string, Set<string>>([
  // abbr and scope are Th-only attributes; React's TdHTMLAttributes
  // incorrectly includes them.
  ["td", new Set(["abbr", "scope"])],
]);

function should_exclude_attribute(tag_name: string, prop_name: string): boolean {
  return EXCLUDED_ELEMENT_ATTRIBUTES.get(tag_name)?.has(prop_name) ?? false;
}

function attribute_type_override(tag_name: string, prop_name: string): TypeExpr | undefined {
  if (tag_name === "table" && prop_name === "frame") {
    return {
      kind: "nullable",
      item: {
        kind: "union",
        options: [
          { kind: "literal", value: "void" },
          { kind: "literal", value: "above" },
          { kind: "literal", value: "below" },
          { kind: "literal", value: "hsides" },
          { kind: "literal", value: "vsides" },
          { kind: "literal", value: "lhs" },
          { kind: "literal", value: "rhs" },
          { kind: "literal", value: "box" },
          { kind: "literal", value: "border" },
        ],
      },
    };
  }
  return undefined;
}

function normalize_attribute_type(
  type_expr: TypeExpr,
  required: boolean,
  default_value: string | number | boolean | null | undefined,
): TypeExpr {
  if (type_expr.kind !== "nullable") {
    return type_expr;
  }

  if (required || default_value !== undefined) {
    return type_expr.item;
  }

  return type_expr;
}

function is_event_prop(prop_name: string): boolean {
  return prop_name.startsWith("on");
}

function event_id_for_prop(prop_name: string): string {
  return `html:global:${to_python_param_name(prop_name)}`;
}

function is_supported_event_prop(prop_name: string): boolean {
  return PUBLIC_EVENT_PROP_NAMES.includes(prop_name as (typeof PUBLIC_EVENT_PROP_NAMES)[number]);
}

function is_supported_prop(prop_name: string): boolean {
  if (!is_event_prop(prop_name)) {
    return true;
  }
  return is_supported_event_prop(prop_name);
}

function compare_prop_names(left: string, right: string): number {
  const left_is_event = is_event_prop(left);
  const right_is_event = is_event_prop(right);
  if (left_is_event !== right_is_event) {
    return left_is_event ? 1 : -1;
  }
  return left.localeCompare(right);
}

function build_attribute_def(
  tag_name: string,
  prop_name: string,
  type_expr: TypeExpr,
  required = false,
  default_value: string | number | boolean | null | undefined = undefined,
): AttributeDef {
  const name_python = to_python_param_name(prop_name);
  const is_aria = prop_name.startsWith("aria-");
  const is_global = GLOBAL_PROP_NAMES.has(prop_name) || is_aria;
  const overridden_type_expr = attribute_type_override(tag_name, prop_name) ?? type_expr;

  return {
    id: is_global ? `html:global:${name_python}` : `html:${tag_name}:${name_python}`,
    name_source: prop_name,
    name_python: to_python_param_name(prop_name),
    applies_to: is_global ? "global" : "element",
    type_expr: normalize_attribute_type(overridden_type_expr, required, default_value),
    required,
    default: default_value,
    category: is_aria ? "aria" : "standard",
    source: react_source(),
  };
}

function build_event_def(binding: ReactEventBinding): EventDef {
  return {
    id: event_id_for_prop(binding.prop_name),
    name_source: binding.prop_name,
    name_python: to_python_param_name(binding.prop_name),
    dom_event_name: binding.dom_event_name,
    handler_name: binding.handler_name,
    payload_name: binding.payload_name,
    source: react_source(),
  };
}

function build_event_handler_def(payload_name: (typeof PUBLIC_HANDLER_PAYLOAD_NAMES)[number]): EventHandlerDef {
  return {
    payload_name,
    typed_handler_name: `${payload_name}Handler`,
    handler_name: `${payload_name}Handler`,
    source: react_source(),
  };
}

function find_payload_field(
  payload_fields: DataclassFieldDef[],
  name_source: string,
): DataclassFieldDef | undefined {
  return payload_fields.find((field) => field.name_source === name_source);
}

function build_dataclass_field(
  config: DataclassFieldConfig,
  payload_fields: DataclassFieldDef[],
  dataclass_name: string,
  fallback_source: SourceProvenance,
): DataclassFieldDef {
  if (config.type_expr) {
    return {
      name_source: config.name_source ?? config.name_python ?? "field",
      name_python: config.name_python ?? to_python_param_name(config.name_source ?? "field"),
      type_expr: config.type_expr,
      default: config.default,
      default_factory: config.default_factory,
      source: fallback_source,
    };
  }

  const source_name = config.source_name;
  if (!source_name) {
    throw new Error(`Missing source_name for ${dataclass_name} field configuration.`);
  }

  const source_field = find_payload_field(payload_fields, source_name);
  if (!source_field) {
    throw new Error(`Missing webref field ${dataclass_name}.${source_name}.`);
  }

  return {
    name_source: source_name,
    name_python: config.name_python ?? source_field.name_python,
    type_expr: source_field.type_expr,
    default: config.default,
    default_factory: config.default_factory,
    source: source_field.source,
  };
}

function build_dataclass_def(
  config: DataclassConfig,
  webref_payload_fields: Map<string, DataclassFieldDef[]>,
): DataclassDef {
  const payload_fields = config.source_interface
    ? (webref_payload_fields.get(config.source_interface) ?? [])
    : [];

  return {
    name: config.name,
    base: config.base,
    frozen: true,
    fields: config.fields.map((field) =>
      build_dataclass_field(field, payload_fields, config.name, config.source),
    ),
    source: config.source,
  };
}

function build_element(config: ElementPolicy, attribute_ids: string[], event_ids: string[]): ElementDef {
  return {
    namespace: "html",
    tag_name: config.tag_name,
    python_name: config.python_name,
    is_container: config.is_container,
    text_behavior: config.text_behavior,
    attributes: attribute_ids,
    events: event_ids,
    source: react_source(),
  };
}

export async function build_ir_document(): Promise<IrDocument> {
  const react_surface = await extract_react_surface();
  const needed_payload_interfaces = [
    "Event",
    "UIEvent",
    "MouseEvent",
    "KeyboardEvent",
    "FocusEvent",
    "InputEvent",
    "SubmitEvent",
    "WheelEvent",
    "DragEvent",
  ];
  const webref_payloads = await extract_webref_event_payloads(needed_payload_interfaces);
  const webref_payload_fields = new Map<string, DataclassFieldDef[]>(
    [...webref_payloads.entries()].map(([name, payload]) => [
      name,
      payload.fields.map((field) => ({ ...field, source: webref_source("idl_payload") })),
    ]),
  );

  const attributes_by_id = new Map<string, AttributeDef>();
  const events_by_id = new Map<string, EventDef>();
  const elements: ElementDef[] = [];

  for (const prop_name of PUBLIC_EVENT_PROP_NAMES) {
    const binding = react_surface.event_bindings.get(prop_name);
    if (!binding) {
      throw new Error(`Missing react event binding for ${prop_name}.`);
    }
    events_by_id.set(event_id_for_prop(prop_name), build_event_def(binding));
  }

  const element_policies = [...react_surface.elements.keys()]
    .map((tag_name) => build_element_policy(tag_name))
    .filter((policy): policy is ElementPolicy => policy !== undefined)
    .sort((left, right) => left.tag_name.localeCompare(right.tag_name));

  for (const config of element_policies) {
    const surface = react_surface.elements.get(config.tag_name);
    if (!surface) {
      throw new Error(`Missing react surface for <${config.tag_name}>.`);
    }

    const attribute_ids: string[] = [];
    const event_ids: string[] = [];

    const prop_names = [...surface.attributes.keys()]
      .filter((prop_name) => is_supported_prop(prop_name))
      .filter((prop_name) => !should_exclude_attribute(config.tag_name, prop_name))
      .sort(compare_prop_names);

    for (const prop_name of prop_names) {
      const type_expr = surface.attributes.get(prop_name);
      if (!type_expr) {
        throw new Error(`Missing react prop ${config.tag_name}.${prop_name}.`);
      }

      const attribute = build_attribute_def(
        config.tag_name,
        prop_name,
        type_expr,
        false,
        attribute_default(config.tag_name, prop_name),
      );

      if (!attributes_by_id.has(attribute.id)) {
        attributes_by_id.set(attribute.id, attribute);
      }
      attribute_ids.push(attribute.id);

      if (is_event_prop(prop_name)) {
        event_ids.push(event_id_for_prop(prop_name));
      }
    }

    elements.push(build_element(config, attribute_ids, event_ids));
  }

  const dataclasses = DATACLASS_CONFIGS.map((config) => build_dataclass_def(config, webref_payload_fields));
  const event_handlers = PUBLIC_HANDLER_PAYLOAD_NAMES.map((payload_name) =>
    build_event_handler_def(payload_name),
  );

  return {
    elements,
    attributes: [...attributes_by_id.values()],
    events: [...events_by_id.values()],
    event_handlers,
    dataclasses,
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
