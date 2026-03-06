import { describe, expect, it } from "vitest";

import { build_trellis_html_module } from "../src/emit/targets/trellis_html.js";
import type { IrDocument } from "../src/ir/types.js";

describe("trellis target", () => {
  it("builds a python module payload", () => {
    const ir: IrDocument = {
      elements: [
        {
          namespace: "html",
          tag_name: "div",
          python_name: "Div",
          is_container: true,
          attributes: [],
          events: [],
          source: {
            winner: "react_ts",
            contributors: ["react_ts"],
            reason: "runtime_precedence",
            source_version: "@types/react@19.2.14",
          },
        },
      ],
      attributes: [],
      events: [],
      attribute_patterns: [],
    };

    const payload = build_trellis_html_module(ir);
    expect(payload.path).toContain("src/trellis/html");
    expect(payload.content).toContain("def Div(");
  });
});
