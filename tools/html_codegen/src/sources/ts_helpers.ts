import { createRequire } from "node:module";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";

const require = createRequire(import.meta.url);

export function resolve_react_types_path(): string {
  const package_json_path = require.resolve("@types/react/package.json");
  return join(dirname(package_json_path), "index.d.ts");
}

export async function read_source(path: string): Promise<string> {
  return readFile(path, "utf-8");
}
