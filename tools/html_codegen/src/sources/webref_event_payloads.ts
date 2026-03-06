import { parseAll } from "@webref/idl";

import type { TypeExpr } from "../ir/types.js";

interface WebIdlMember {
  type?: string;
  name?: string;
  idlType?: unknown;
}

interface WebIdlDefinition {
  type?: string;
  name?: string;
  partial?: boolean;
  inheritance?: string | null;
  members?: WebIdlMember[];
}

export interface WebrefEventField {
  name_source: string;
  name_python: string;
  type_expr: TypeExpr;
}

export interface WebrefEventPayload {
  name: string;
  inheritance: string | null;
  fields: WebrefEventField[];
}

type ParsedIdlType =
  | string
  | {
      generic?: string;
      nullable?: boolean;
      union?: boolean;
      idlType?: ParsedIdlType | ParsedIdlType[];
    };

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

function to_snake_case(name: string): string {
  return name
    .replace(/([a-z0-9])([A-Z])/g, "$1_$2")
    .replace(/-/g, "_")
    .toLowerCase();
}

function parse_scalar_idl_type(type_name: string): TypeExpr | undefined {
  if (["DOMString", "USVString", "CSSOMString"].includes(type_name)) {
    return primitive("str");
  }
  if (["long", "unsigned long", "short", "unsigned short", "byte", "octet"].includes(type_name)) {
    return primitive("int");
  }
  if (["double", "float", "unrestricted double", "unrestricted float"].includes(type_name)) {
    return primitive("float");
  }
  if (type_name === "DOMHighResTimeStamp") {
    return primitive("float");
  }
  if (type_name === "boolean") {
    return primitive("bool");
  }
  if (type_name === "DataTransfer") {
    return reference("DataTransfer");
  }
  if (type_name === "File") {
    return reference("File");
  }
  if (type_name === "FileList") {
    return { kind: "array", item: reference("File") };
  }
  return undefined;
}

function parse_idl_type(idl_type: ParsedIdlType): TypeExpr | undefined {
  if (typeof idl_type === "string") {
    return parse_scalar_idl_type(idl_type);
  }

  if (idl_type.union && Array.isArray(idl_type.idlType)) {
    const options = idl_type.idlType
      .map((option) => parse_idl_type(option))
      .filter((option): option is TypeExpr => option !== undefined);
    if (options.length === 0) {
      return undefined;
    }
    const union_type = options.length === 1 ? options[0] : union(...options);
    return idl_type.nullable ? nullable(union_type) : union_type;
  }

  const nested = Array.isArray(idl_type.idlType) ? idl_type.idlType[0] : idl_type.idlType;
  if (!nested) {
    return undefined;
  }

  if (idl_type.generic === "sequence") {
    const item = parse_idl_type(nested);
    if (!item) {
      return undefined;
    }
    const array_type: TypeExpr = { kind: "array", item };
    return idl_type.nullable ? nullable(array_type) : array_type;
  }

  const resolved = parse_idl_type(nested);
  if (!resolved) {
    return undefined;
  }
  return idl_type.nullable ? nullable(resolved) : resolved;
}

function merge_payload_definitions(definitions: Iterable<WebIdlDefinition>): Map<string, WebIdlDefinition> {
  const merged = new Map<string, WebIdlDefinition>();

  for (const definition of definitions) {
    if (definition.type !== "interface" || !definition.name) {
      continue;
    }

    const current = merged.get(definition.name);
    if (!current) {
      merged.set(definition.name, {
        type: definition.type,
        name: definition.name,
        inheritance: definition.inheritance ?? null,
        members: [...(definition.members ?? [])],
      });
      continue;
    }

    if (!current.inheritance && definition.inheritance) {
      current.inheritance = definition.inheritance;
    }
    current.members = [...(current.members ?? []), ...(definition.members ?? [])];
  }

  return merged;
}

export async function extract_webref_event_payloads(
  interface_names: string[],
): Promise<Map<string, WebrefEventPayload>> {
  const parsed_idl = await parseAll();
  const merged = merge_payload_definitions(
    Object.values(parsed_idl).flatMap((definitions) => definitions as WebIdlDefinition[]),
  );

  const payloads = new Map<string, WebrefEventPayload>();
  for (const interface_name of interface_names) {
    const definition = merged.get(interface_name);
    if (!definition) {
      continue;
    }

    const fields = (definition.members ?? [])
      .filter((member) => member.type === "attribute" && member.name && member.idlType)
      .map((member) => {
        const type_expr = parse_idl_type(member.idlType as ParsedIdlType);
        if (!type_expr) {
          return undefined;
        }
        return {
          name_source: member.name as string,
          name_python: to_snake_case(member.name as string),
          type_expr,
        };
      })
      .filter((field): field is WebrefEventField => field !== undefined);

    payloads.set(interface_name, {
      name: interface_name,
      inheritance: definition.inheritance ?? null,
      fields,
    });
  }

  return payloads;
}
