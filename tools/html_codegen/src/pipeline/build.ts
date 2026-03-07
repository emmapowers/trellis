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

interface SlicePropConfig {
  name: string;
  required?: boolean;
  default?: string | number | boolean | null;
}

interface SliceElementConfig {
  tag_name: "a" | "div" | "img" | "input";
  python_name: "_A" | "Div" | "Img" | "Input";
  is_container: boolean;
  text_behavior: "none" | "public_helper" | "internal_text_prop";
  props: SlicePropConfig[];
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
  "onSubmit",
  "onScroll",
  "onWheel",
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

const SLICE_CONFIG: SliceElementConfig[] = [
  {
    tag_name: "a",
    python_name: "_A",
    is_container: true,
    text_behavior: "public_helper",
    props: [
      { name: "href" },
      { name: "target" },
      { name: "rel" },
      { name: "download" },
      { name: "className" },
      { name: "style" },
      { name: "id" },
      { name: "onClick" },
      { name: "onDoubleClick" },
      { name: "onContextMenu" },
      { name: "onKeyDown" },
      { name: "onKeyUp" },
    ],
  },
  {
    tag_name: "div",
    python_name: "Div",
    is_container: true,
    text_behavior: "none",
    props: [
      { name: "className" },
      { name: "style" },
      { name: "id" },
      { name: "onClick" },
      { name: "onDoubleClick" },
      { name: "onContextMenu" },
      { name: "onMouseEnter" },
      { name: "onMouseLeave" },
      { name: "onKeyDown" },
      { name: "onKeyUp" },
      { name: "onScroll" },
      { name: "onWheel" },
      { name: "onDragStart" },
      { name: "onDrag" },
      { name: "onDragEnd" },
      { name: "onDragEnter" },
      { name: "onDragOver" },
      { name: "onDragLeave" },
      { name: "onDrop" },
    ],
  },
  {
    tag_name: "img",
    python_name: "Img",
    is_container: false,
    text_behavior: "none",
    props: [
      { name: "src" },
      { name: "alt" },
      { name: "width" },
      { name: "height" },
      { name: "loading" },
      { name: "className" },
      { name: "style" },
      { name: "id" },
      { name: "onClick" },
      { name: "onDoubleClick" },
      { name: "onContextMenu" },
    ],
  },
  {
    tag_name: "input",
    python_name: "Input",
    is_container: false,
    text_behavior: "none",
    props: [
      { name: "type", default: "text" },
      { name: "value" },
      { name: "placeholder" },
      { name: "disabled" },
      { name: "readOnly" },
      { name: "name" },
      { name: "checked" },
      { name: "required" },
      { name: "min" },
      { name: "max" },
      { name: "step" },
      { name: "pattern" },
      { name: "maxLength" },
      { name: "autoComplete" },
      { name: "autoFocus" },
      { name: "accept" },
      { name: "multiple" },
      { name: "onChange" },
      { name: "onInput" },
      { name: "onFocus" },
      { name: "onBlur" },
      { name: "onKeyDown" },
      { name: "onKeyUp" },
      { name: "className" },
      { name: "style" },
      { name: "id" },
    ],
  },
];

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
    base: "Event",
    source_interface: "FocusEvent",
    fields: [],
    source: webref_source("idl_payload"),
  },
  {
    name: "SubmitEvent",
    base: "Event",
    source_interface: "SubmitEvent",
    fields: [],
    source: webref_source("idl_payload"),
  },
  {
    name: "InputEvent",
    base: "Event",
    source_interface: "InputEvent",
    fields: [
      { source_name: "data", default: null },
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

function normalize_attribute_type(prop: SlicePropConfig, type_expr: TypeExpr): TypeExpr {
  if (type_expr.kind !== "nullable") {
    return type_expr;
  }

  if (prop.required || prop.default !== undefined) {
    return type_expr.item;
  }

  return type_expr;
}

function is_event_prop(prop_name: string): boolean {
  return prop_name.startsWith("on");
}

function event_id_for_prop(prop_name: string): string {
  return `html:global:${to_snake_case(prop_name)}`;
}

function build_attribute_def(
  tag_name: string,
  prop: SlicePropConfig,
  type_expr: TypeExpr,
): AttributeDef {
  const prop_name = prop.name;
  const name_python = to_snake_case(prop_name);
  const is_global = GLOBAL_PROP_NAMES.has(prop_name);

  return {
    id: is_global ? `html:global:${name_python}` : `html:${tag_name}:${name_python}`,
    name_source: prop_name,
    name_python,
    applies_to: is_global ? "global" : "element",
    type_expr: normalize_attribute_type(prop, type_expr),
    required: prop.required ?? false,
    default: prop.default,
    category: "standard",
    source: react_source(),
  };
}

function build_event_def(binding: ReactEventBinding): EventDef {
  return {
    id: event_id_for_prop(binding.prop_name),
    name_source: binding.prop_name,
    name_python: to_snake_case(binding.prop_name),
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
      name_python: config.name_python ?? to_snake_case(config.name_source ?? "field"),
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

function build_element(
  config: SliceElementConfig,
  attribute_ids: string[],
  event_ids: string[],
): ElementDef {
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

  for (const config of SLICE_CONFIG) {
    const surface = react_surface.elements.get(config.tag_name);
    if (!surface) {
      throw new Error(`Missing react surface for <${config.tag_name}>.`);
    }

    const attribute_ids: string[] = [];
    const event_ids: string[] = [];

    for (const prop of config.props) {
      const type_expr = surface.attributes.get(prop.name);
      if (!type_expr) {
        throw new Error(`Missing react prop ${config.tag_name}.${prop.name}.`);
      }

      const attribute = build_attribute_def(config.tag_name, prop, type_expr);
      attributes_by_id.set(attribute.id, attribute);
      attribute_ids.push(attribute.id);

      if (is_event_prop(prop.name)) {
        event_ids.push(event_id_for_prop(prop.name));
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
