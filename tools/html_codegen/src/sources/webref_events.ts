import { listAll } from "@webref/events";

export async function extract_webref_event_names(): Promise<Set<string>> {
  const event_defs = await listAll();
  const names = new Set<string>();

  for (const event_def of event_defs) {
    if (event_def.type) {
      names.add(event_def.type);
    }
  }

  return names;
}
