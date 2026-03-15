import type { TypeExpr } from "../ir/types.js";

export interface RawAttributeRecord {
  id: string;
  name_source: string;
  type_expr: TypeExpr;
  source: "react_ts" | "webref";
}

export interface RawEventRecord {
  id: string;
  name_source: string;
  source: "react_ts" | "webref";
}

export interface RawElementRecord {
  id: string;
  tag_name: string;
  source: "react_ts" | "webref";
}

export interface NormalizeInput {
  elements: RawElementRecord[];
  attributes: RawAttributeRecord[];
  events: RawEventRecord[];
}

export function normalize_input(input: NormalizeInput): NormalizeInput {
  return input;
}
