import { describe, expect, it } from "vitest";

import {
  build_trellis_html_modules,
  type TrellisModulePayload,
} from "../src/emit/targets/trellis_html.js";
import type { IrDocument } from "../src/ir/types.js";

function sample_ir(): IrDocument {
  return {
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
        attributes: [
          "html:global:class_name",
          "html:global:style",
          "html:global:aria_autocomplete",
          "html:global:aria_label",
        ],
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
      {
        namespace: "html",
        tag_name: "audio",
        python_name: "Audio",
        is_container: true,
        text_behavior: "none",
        attributes: ["html:audio:auto_play", "html:audio:controls", "html:audio:src"],
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
        tag_name: "p",
        python_name: "P",
        is_container: true,
        text_behavior: "public_helper",
        attributes: [
          "html:global:class_name",
          "html:global:style",
          "html:global:aria_autocomplete",
        ],
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
      {
        namespace: "html",
        tag_name: "table",
        python_name: "Table",
        is_container: true,
        text_behavior: "none",
        attributes: ["html:global:class_name"],
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
        id: "html:global:aria_autocomplete",
        name_source: "aria-autocomplete",
        name_python: "aria_autocomplete",
        applies_to: "global",
        type_expr: {
          kind: "nullable",
          item: {
            kind: "union",
            options: [
              { kind: "literal", value: "none" },
              { kind: "literal", value: "inline" },
              { kind: "literal", value: "list" },
              { kind: "literal", value: "both" },
            ],
          },
        },
        required: false,
        category: "aria",
        source: {
          winner: "react_ts",
          contributors: ["react_ts"],
          reason: "runtime_precedence",
          source_version: "@types/react@19.2.14",
        },
      },
      {
        id: "html:global:aria_label",
        name_source: "aria-label",
        name_python: "aria_label",
        applies_to: "global",
        type_expr: { kind: "nullable", item: { kind: "primitive", name: "str" } },
        required: false,
        category: "aria",
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
      {
        id: "html:audio:auto_play",
        name_source: "autoPlay",
        name_python: "auto_play",
        applies_to: "element",
        type_expr: { kind: "nullable", item: { kind: "primitive", name: "bool" } },
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
        id: "html:audio:controls",
        name_source: "controls",
        name_python: "controls",
        applies_to: "element",
        type_expr: { kind: "nullable", item: { kind: "primitive", name: "bool" } },
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
        id: "html:audio:src",
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
}

function moduleByPath(payloads: TrellisModulePayload[], pathSuffix: string): TrellisModulePayload {
  const payload = payloads.find((candidate) => candidate.path.endsWith(pathSuffix));
  if (!payload) {
    throw new Error(`Missing payload for ${pathSuffix}`);
  }
  return payload;
}

describe("trellis target", () => {
  it("splits generated html bindings into mdn-style family modules", () => {
    const payloads = build_trellis_html_modules(sample_ir(), "2026-03-07T12:00:00.000Z");

    expect(payloads.map((payload) => payload.path)).toEqual(
      expect.arrayContaining([
        "src/trellis/html/_generated_attribute_types.py",
        "src/trellis/html/_generated_runtime.py",
        "src/trellis/html/_generated_forms.py",
        "src/trellis/html/_generated_image_and_multimedia.py",
        "src/trellis/html/_generated_interactive_elements.py",
        "src/trellis/html/_generated_sectioning_and_layout.py",
        "src/trellis/html/_generated_table_content.py",
        "src/trellis/html/_generated_text_blocks.py",
      ]),
    );
    expect(payloads.map((payload) => payload.path)).not.toContain(
      "src/trellis/html/_generated_text_content.py",
    );

    const runtime = moduleByPath(payloads, "_generated_runtime.py").content;
    expect(runtime).toContain("Generated at: 2026-03-07T12:00:00.000Z");
    expect(runtime).toContain("from trellis.html._generated_interactive_elements import (");
    expect(runtime).toContain("    _A,");
    expect(runtime).toContain("from trellis.html._generated_sectioning_and_layout import (");
    expect(runtime).toContain("    Div,");
    expect(runtime).toContain("from trellis.html._generated_forms import (");
    expect(runtime).toContain("    Input,");
    expect(runtime).toContain("    Option,");
    expect(runtime).toContain("from trellis.html._generated_image_and_multimedia import (");
    expect(runtime).toContain("    Audio,");
    expect(runtime).toContain("    Img,");
    expect(runtime).toContain("from trellis.html._generated_table_content import (");
    expect(runtime).toContain("    Table,");
    expect(runtime).not.toContain("def Div(");

    const attributeTypes = moduleByPath(payloads, "_generated_attribute_types.py").content;
    expect(attributeTypes).toContain("Generated at: 2026-03-07T12:00:00.000Z");
    expect(attributeTypes).toContain("AriaAutocomplete = Literal[");
    expect(attributeTypes).toContain("InputType = Literal[");

    const layout = moduleByPath(payloads, "_generated_sectioning_and_layout.py").content;
    expect(layout).toContain("Generated HTML sectioning and layout wrappers.");
    expect(layout).toContain("Internal codegen artifact for trellis.html.");
    expect(layout).toContain(
      "Reference: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements",
    );
    expect(layout).toContain("Generated at: 2026-03-07T12:00:00.000Z");
    expect(layout).toContain("from trellis.html._generated_attribute_types import AriaAutocomplete");
    expect(layout).toContain('@html_element("div", is_container=True)');
    expect(layout).toContain("def Div(");
    expect(layout).toContain("aria_autocomplete: AriaAutocomplete | None = None");
    expect(layout).toContain("aria_label: str | None = None");
    expect(layout).toContain('"""Generated wrapper for `<div>`.');
    expect(layout).toContain(
      "Reference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/div",
    );

    const interactive = moduleByPath(payloads, "_generated_interactive_elements.py").content;
    expect(interactive).toContain("Generated at: 2026-03-07T12:00:00.000Z");
    expect(interactive).toContain('@html_element("a", is_container=True, name="A")');
    expect(interactive).toContain("def _A(");
    expect(interactive).toContain("inner_text: str | None = None,");
    expect(interactive).toContain('"""Generated internal wrapper for `<a>`.');
    expect(interactive).toContain(
      "Reference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/a",
    );

    const media = moduleByPath(payloads, "_generated_image_and_multimedia.py").content;
    expect(media).toContain("Generated at: 2026-03-07T12:00:00.000Z");
    expect(media).toContain("def Audio(");
    expect(media).toContain("auto_play: bool | None = None");
    expect(media).toContain("controls: bool | None = None");
    expect(media).toContain("src: str | None = None");
    expect(media).toContain('"""Generated wrapper for `<audio>`.');

    const forms = moduleByPath(payloads, "_generated_forms.py").content;
    expect(forms).toContain("Generated at: 2026-03-07T12:00:00.000Z");
    expect(forms).toContain("from trellis.html._generated_attribute_types import InputType");
    expect(forms).toContain('type: InputType = "text"');
    expect(forms).toContain('def Option(\n    inner_text: str | None = None,');
    expect(forms).toContain('"""Generated wrapper for `<option>`.');

    const tables = moduleByPath(payloads, "_generated_table_content.py").content;
    expect(tables).toContain("Generated at: 2026-03-07T12:00:00.000Z");
    expect(tables).toContain("def Table(");
    expect(tables).toContain('"""Generated wrapper for `<table>`.');

    const text = moduleByPath(payloads, "_generated_text_blocks.py").content;
    expect(text).toContain("Generated HTML text blocks wrappers.");
  });

  it("does not expose _text or fallback props in generated family modules", () => {
    const payloads = build_trellis_html_modules(sample_ir(), "2026-03-07T12:00:00.000Z");
    const familyModules = payloads.filter((payload) => payload.path.includes("_generated_") && !payload.path.endsWith("_generated_runtime.py"));
    const combined = familyModules.map((payload) => payload.content).join("\n");

    expect(combined).not.toContain("**props: tp.Any");
    expect(combined).not.toContain("    _text:");
    expect(combined).toContain("from collections.abc import Mapping");
    expect(combined).toContain("DataValue = str | int | float | bool | None");
  });
});
