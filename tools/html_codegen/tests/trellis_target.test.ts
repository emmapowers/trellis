import { describe, expect, it } from "vitest";

import { build_trellis_html_module } from "../src/emit/targets/trellis_html.js";
import type { IrDocument } from "../src/ir/types.js";

describe("trellis target", () => {
  it("builds raw generated bindings without custom link policy", () => {
    const ir: IrDocument = {
      elements: [
        {
          namespace: "html",
          tag_name: "a",
          python_name: "_A",
          is_container: true,
          text_behavior: "public_helper",
          attributes: ["html:a:href", "html:global:class_name", "html:global:style"],
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
          text_behavior: "none",
          attributes: ["html:global:class_name", "html:global:style"],
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
          text_behavior: "none",
          attributes: ["html:img:src", "html:global:style"],
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
          text_behavior: "none",
          attributes: ["html:input:type", "html:global:style"],
          events: [],
          source: {
            winner: "react_ts",
            contributors: ["react_ts"],
            reason: "runtime_precedence",
            source_version: "@types/react@19.2.14",
          },
        },
      ],
      attributes: [
        {
          id: "html:a:href",
          name_source: "href",
          name_python: "href",
          applies_to: "element",
          type_expr: { kind: "nullable", item: { kind: "primitive", name: "str" } },
          required: false,
          category: "standard",
          source: {
            winner: "react_ts",
            contributors: ["react_ts"],
            reason: "runtime_precedence",
            source_version: "@types/react@19.2.14",
          },
        },
        {
          id: "html:global:class_name",
          name_source: "className",
          name_python: "class_name",
          applies_to: "global",
          type_expr: { kind: "nullable", item: { kind: "primitive", name: "str" } },
          required: false,
          category: "standard",
          source: {
            winner: "react_ts",
            contributors: ["react_ts"],
            reason: "runtime_precedence",
            source_version: "@types/react@19.2.14",
          },
        },
        {
          id: "html:global:style",
          name_source: "style",
          name_python: "style",
          applies_to: "global",
          type_expr: { kind: "nullable", item: { kind: "style_object" } },
          required: false,
          category: "standard",
          source: {
            winner: "react_ts",
            contributors: ["react_ts"],
            reason: "runtime_precedence",
            source_version: "@types/react@19.2.14",
          },
        },
        {
          id: "html:img:src",
          name_source: "src",
          name_python: "src",
          applies_to: "element",
          type_expr: { kind: "nullable", item: { kind: "primitive", name: "str" } },
          required: false,
          category: "standard",
          source: {
            winner: "react_ts",
            contributors: ["react_ts"],
            reason: "runtime_precedence",
            source_version: "@types/react@19.2.14",
          },
        },
        {
          id: "html:input:type",
          name_source: "type",
          name_python: "type",
          applies_to: "element",
          type_expr: {
            kind: "union",
            options: [
              { kind: "literal", value: "text" },
              { kind: "literal", value: "email" },
            ],
          },
          required: false,
          default: "text",
          category: "standard",
          source: {
            winner: "react_ts",
            contributors: ["react_ts"],
            reason: "runtime_precedence",
            source_version: "@types/react@19.2.14",
          },
        },
      ],
      events: [],
      event_handlers: [],
      dataclasses: [],
      attribute_patterns: [],
    };

    const payload = build_trellis_html_module(ir);
    expect(payload.path).toContain("src/trellis/html");
    expect(payload.content).toContain("from collections.abc import Mapping");
    expect(payload.content).toContain('@html_element("a", is_container=True, name="A")');
    expect(payload.content).toContain('@html_element("div", is_container=True)');
    expect(payload.content).toContain('@html_element("img")');
    expect(payload.content).toContain('@html_element("input")');
    expect(payload.content).toContain("DataValue = str | int | float | bool | None");
    expect(payload.content).toContain("InputType =");
    expect(payload.content).toContain('type: InputType = "text"');
    expect(payload.content).toContain("from typing import Literal, overload");
    expect(payload.content).toContain("data: Mapping[str, DataValue] | None = None");
    expect(payload.content).toContain("def _A(");
    expect(payload.content).toContain("internal_text: str | None = None,");
    expect(payload.content).toContain("def Div(");
    expect(payload.content).toContain("def Img(");
    expect(payload.content).toContain("src: str | None = None");
    expect(payload.content).toContain("def Input(");
    expect(payload.content).toContain("style: Style | None = None");
    expect(payload.content).not.toContain("**props: tp.Any");
    expect(payload.content).not.toContain("def A(");
    expect(payload.content).not.toContain("def _make_a(");
    expect(payload.content).not.toContain("from trellis.routing.state import router");
    expect(payload.content).not.toContain("    _text:");
    expect(payload.content).not.toContain("def Svg(");
    expect(payload.content).not.toContain("def Animate(");
  });

  it("emits public text helpers without exposing _text", () => {
    const ir: IrDocument = {
      elements: [
        {
          namespace: "html",
          tag_name: "p",
          python_name: "P",
          is_container: true,
          text_behavior: "public_helper",
          attributes: ["html:global:class_name", "html:global:style"],
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
          tag_name: "option",
          python_name: "Option",
          is_container: false,
          text_behavior: "public_helper",
          attributes: ["html:option:value"],
          events: [],
          source: {
            winner: "react_ts",
            contributors: ["react_ts"],
            reason: "runtime_precedence",
            source_version: "@types/react@19.2.14",
          },
        },
      ],
      attributes: [
        {
          id: "html:global:class_name",
          name_source: "className",
          name_python: "class_name",
          applies_to: "global",
          type_expr: { kind: "nullable", item: { kind: "primitive", name: "str" } },
          required: false,
          category: "standard",
          source: {
            winner: "react_ts",
            contributors: ["react_ts"],
            reason: "runtime_precedence",
            source_version: "@types/react@19.2.14",
          },
        },
        {
          id: "html:global:style",
          name_source: "style",
          name_python: "style",
          applies_to: "global",
          type_expr: { kind: "nullable", item: { kind: "style_object" } },
          required: false,
          category: "standard",
          source: {
            winner: "react_ts",
            contributors: ["react_ts"],
            reason: "runtime_precedence",
            source_version: "@types/react@19.2.14",
          },
        },
        {
          id: "html:option:value",
          name_source: "value",
          name_python: "value",
          applies_to: "element",
          type_expr: { kind: "nullable", item: { kind: "primitive", name: "str" } },
          required: false,
          category: "standard",
          source: {
            winner: "react_ts",
            contributors: ["react_ts"],
            reason: "runtime_precedence",
            source_version: "@types/react@19.2.14",
          },
        },
      ],
      events: [],
      event_handlers: [],
      dataclasses: [],
      attribute_patterns: [],
    };

    const payload = build_trellis_html_module(ir);
    expect(payload.content).toContain("from typing import Literal, overload");
    expect(payload.content).toContain("def P(");
    expect(payload.content).toContain("internal_text: str,");
    expect(payload.content).toContain(") -> HtmlContainerElement: ...");
    expect(payload.content).toContain('def Option(\n    internal_text: str | None = None,');
    expect(payload.content).not.toContain("def Option(\n    _text:");
    expect(payload.content).not.toContain('def P(\n    _text:');
  });
});
