import { describe, expect, it } from "vitest";

import { build_trellis_html_module } from "../src/emit/targets/trellis_html.js";
import type { IrDocument } from "../src/ir/types.js";

describe("trellis target", () => {
  it("builds a real trellis-style python module payload", () => {
    const ir: IrDocument = {
      elements: [
        {
          namespace: "html",
          tag_name: "a",
          python_name: "A",
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
        {
          namespace: "html",
          tag_name: "img",
          python_name: "Img",
          is_container: false,
          attributes: [],
          events: [],
          source: {
            winner: "react_ts",
            contributors: ["react_ts"],
            reason: "runtime_precedence",
            source_version: "@types/react@19.2.14",
          },
        },
        {
          namespace: "html",
          tag_name: "input",
          python_name: "Input",
          is_container: false,
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
    expect(payload.content).toContain('@html_element("a", is_container=True, name="A")');
    expect(payload.content).toContain('@html_element("div", is_container=True)');
    expect(payload.content).toContain('@html_element("img")');
    expect(payload.content).toContain('@html_element("input")');
    expect(payload.content).toContain("InputType =");
    expect(payload.content).toContain('type: InputType = "text"');
    expect(payload.content).toContain("from typing import Literal, overload");
    expect(payload.content).toContain("def _A(");
    expect(payload.content).toContain("def A(");
    expect(payload.content).toContain("def Div(");
    expect(payload.content).toContain("def Img(");
    expect(payload.content).toContain("def Input(");
    expect(payload.content).not.toContain("def Svg(");
    expect(payload.content).not.toContain("def Animate(");
  });
});
