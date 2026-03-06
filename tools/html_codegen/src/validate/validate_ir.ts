import { ir_schema } from "../ir/schema.js";
import type { IrDocument } from "../ir/types.js";
import { validate_snake_case_names, validate_unique_attribute_ids } from "./policies.js";

export interface ValidationResult {
  ok: boolean;
  errors: string[];
}

export function validate_ir(document: IrDocument): ValidationResult {
  const errors: string[] = [];

  const parsed = ir_schema.safeParse(document);
  if (!parsed.success) {
    for (const issue of parsed.error.issues) {
      errors.push(`schema: ${issue.path.join(".")} ${issue.message}`);
    }
  }

  errors.push(...validate_snake_case_names(document));
  errors.push(...validate_unique_attribute_ids(document));

  return {
    ok: errors.length === 0,
    errors,
  };
}
