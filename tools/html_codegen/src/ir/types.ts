export type SourceWinner = "react_ts" | "webref" | "trellis_policy";

export interface SourceProvenance {
  winner: SourceWinner;
  contributors: string[];
  reason: string;
  source_version: string;
}

export type TypeExpr =
  | {
      kind: "literal";
      value: string | number | boolean | null;
    }
  | {
      kind: "primitive";
      name: "str" | "int" | "float" | "bool" | "none";
    }
  | {
      kind: "union";
      options: TypeExpr[];
    }
  | {
      kind: "array";
      item: TypeExpr;
    }
  | {
      kind: "reference";
      name: string;
    }
  | {
      kind: "nullable";
      item: TypeExpr;
    }
  | {
      kind: "callable";
      params: TypeExpr[];
      returns: TypeExpr;
    }
  | {
      kind: "object";
      fields: Record<string, TypeExpr>;
    };

export interface AttributeDef {
  id: string;
  name_source: string;
  name_python: string;
  applies_to: "global" | "element";
  type_expr: TypeExpr;
  required: boolean;
  default?: string | number | boolean | null;
  category: "standard" | "aria" | "data";
  source: SourceProvenance;
}

export interface EventDef {
  id: string;
  name_source: string;
  name_python: string;
  dom_event_name: string;
  handler_name: string;
  payload_name: string;
  source: SourceProvenance;
}

export interface EventHandlerDef {
  payload_name: string;
  typed_handler_name: string;
  handler_name: string;
  source: SourceProvenance;
}

export interface DataclassFieldDef {
  name_source: string;
  name_python: string;
  type_expr: TypeExpr;
  default?: string | number | boolean | null;
  default_factory?: "list";
  source: SourceProvenance;
}

export interface DataclassDef {
  name: string;
  base?: string;
  frozen: boolean;
  fields: DataclassFieldDef[];
  source: SourceProvenance;
}

export interface ElementDef {
  namespace: "html" | "svg" | "mathml";
  tag_name: string;
  python_name: string;
  is_container: boolean;
  attributes: string[];
  events: string[];
  source: SourceProvenance;
}

export interface AttributePatternDef {
  name: "data";
  python_param_name: "data";
  dom_prefix: "data-";
  key_style: "dom_suffix";
  value_type_expr: TypeExpr;
}

export interface IrDocument {
  elements: ElementDef[];
  attributes: AttributeDef[];
  events: EventDef[];
  event_handlers: EventHandlerDef[];
  dataclasses: DataclassDef[];
  attribute_patterns: AttributePatternDef[];
}
