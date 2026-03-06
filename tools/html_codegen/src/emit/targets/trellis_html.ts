import type { IrDocument } from "../../ir/types.js";
import { emit_python_module } from "../python/render_module.js";

export interface TrellisModulePayload {
  path: string;
  content: string;
}

export function build_trellis_html_module(document: IrDocument): TrellisModulePayload {
  return {
    path: "src/trellis/html/_generated_runtime.py",
    content: emit_python_module(document),
  };
}
