import { z } from "zod";

const snake_case_regex = /^[a-z][a-z0-9_]*$/;

const source_provenance_schema = z.object({
  winner: z.enum(["react_ts", "webref"]),
  contributors: z.array(z.string()).min(1),
  reason: z.string().min(1),
  source_version: z.string().min(1),
});

const literal_schema = z.object({
  kind: z.literal("literal"),
  value: z.union([z.string(), z.number(), z.boolean(), z.null()]),
});

const primitive_schema = z.object({
  kind: z.literal("primitive"),
  name: z.enum(["str", "int", "float", "bool", "none"]),
});

const type_expr_schema: z.ZodType = z.lazy(() =>
  z.discriminatedUnion("kind", [
    literal_schema,
    primitive_schema,
    z.object({
      kind: z.literal("union"),
      options: z.array(type_expr_schema).min(1),
    }),
    z.object({
      kind: z.literal("array"),
      item: type_expr_schema,
    }),
    z.object({
      kind: z.literal("reference"),
      name: z.string().min(1),
    }),
    z.object({
      kind: z.literal("nullable"),
      item: type_expr_schema,
    }),
    z.object({
      kind: z.literal("callable"),
      params: z.array(type_expr_schema),
      returns: type_expr_schema,
    }),
    z.object({
      kind: z.literal("object"),
      fields: z.record(z.string(), type_expr_schema),
    }),
  ]),
);

const attribute_schema = z.object({
  id: z.string().min(1),
  name_source: z.string().min(1),
  name_python: z.string().regex(snake_case_regex),
  applies_to: z.enum(["global", "element"]),
  type_expr: type_expr_schema,
  required: z.boolean(),
  default: z.union([z.string(), z.number(), z.boolean(), z.null()]).optional(),
  category: z.enum(["standard", "aria", "data"]),
  source: source_provenance_schema,
});

const event_schema = z.object({
  id: z.string().min(1),
  name_source: z.string().min(1),
  name_python: z.string().regex(snake_case_regex),
  handler_signature: z.string().min(1),
  event_payload: z.string().min(1),
  source: source_provenance_schema,
});

const element_schema = z.object({
  namespace: z.enum(["html", "svg", "mathml"]),
  tag_name: z.string().min(1),
  python_name: z.string().regex(/^[A-Z][A-Za-z0-9]*$/),
  is_container: z.boolean(),
  attributes: z.array(z.string()),
  events: z.array(z.string()),
  source: source_provenance_schema,
});

const attribute_pattern_schema = z.object({
  name: z.literal("data"),
  python_param_name: z.literal("data"),
  dom_prefix: z.literal("data-"),
  key_style: z.literal("dom_suffix"),
  value_type_expr: type_expr_schema,
});

export const ir_schema = z.object({
  elements: z.array(element_schema),
  attributes: z.array(attribute_schema),
  events: z.array(event_schema),
  attribute_patterns: z.array(attribute_pattern_schema),
});

export type IrSchema = z.infer<typeof ir_schema>;
