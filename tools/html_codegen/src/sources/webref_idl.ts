import { parseAll } from "@webref/idl";

type WebIdlDefinition = {
  name?: string;
};

export async function extract_webref_idl_names(): Promise<Set<string>> {
  const parsed_idl = await parseAll();
  const names = new Set<string>();

  for (const definitions of Object.values(parsed_idl)) {
    for (const definition of definitions as WebIdlDefinition[]) {
      if (definition.name) {
        names.add(definition.name);
      }
    }
  }

  return names;
}
