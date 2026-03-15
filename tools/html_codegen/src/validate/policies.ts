import type { IrDocument } from "../ir/types.js";

const snake_case_regex = /^[a-z][a-z0-9_]*$/;

export function validate_snake_case_names(document: IrDocument): string[] {
  const errors: string[] = [];

  for (const attribute of document.attributes) {
    if (!snake_case_regex.test(attribute.name_python)) {
      errors.push(`Attribute ${attribute.id} must use snake_case name_python.`);
    }
  }

  for (const event of document.events) {
    if (!snake_case_regex.test(event.name_python)) {
      errors.push(`Event ${event.id} must use snake_case name_python.`);
    }
  }

  return errors;
}

export function validate_unique_attribute_ids(document: IrDocument): string[] {
  const errors: string[] = [];
  const seen = new Set<string>();
  for (const attribute of document.attributes) {
    if (seen.has(attribute.id)) {
      errors.push(`Duplicate attribute id: ${attribute.id}`);
    }
    seen.add(attribute.id);
  }
  return errors;
}
