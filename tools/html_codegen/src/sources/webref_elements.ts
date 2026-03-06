import { listAll } from "@webref/elements";

export async function extract_webref_element_surface(): Promise<Set<string>> {
  const specs = await listAll();
  const elements = new Set<string>();

  for (const value of Object.values(specs)) {
    const spec = value as { elements?: Array<{ name?: string }> };
    for (const element of spec.elements ?? []) {
      if (element.name) {
        elements.add(element.name);
      }
    }
  }

  return elements;
}
