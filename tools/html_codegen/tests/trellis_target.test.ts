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
        attributes: ["html:global:class_name", "html:table:frame"],
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
        tag_name: "style",
        python_name: "StyleTag",
        is_container: false,
        text_behavior: "public_helper",
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
        tag_name: "title",
        python_name: "Title",
        is_container: false,
        text_behavior: "public_helper",
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
        tag_name: "script",
        python_name: "Script",
        is_container: false,
        text_behavior: "public_helper",
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
        tag_name: "rp",
        python_name: "Rp",
        is_container: false,
        text_behavior: "public_helper",
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
        id: "html:table:frame",
        name_source: "frame",
        name_python: "frame",
        applies_to: "element",
        type_expr: {
          kind: "nullable",
          item: {
            kind: "union",
            options: [
              { kind: "literal", value: "void" },
              { kind: "literal", value: "above" },
              { kind: "literal", value: "below" },
              { kind: "literal", value: "hsides" },
              { kind: "literal", value: "vsides" },
              { kind: "literal", value: "lhs" },
              { kind: "literal", value: "rhs" },
              { kind: "literal", value: "box" },
              { kind: "literal", value: "border" },
            ],
          },
        },
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
        "src/trellis/html/_generated_attribute_types.pyi",
        "src/trellis/html/_generated_runtime.py",
        "src/trellis/html/_generated_runtime.pyi",
        "src/trellis/html/_generated_forms.py",
        "src/trellis/html/_generated_forms.pyi",
        "src/trellis/html/_generated_image_and_multimedia.py",
        "src/trellis/html/_generated_image_and_multimedia.pyi",
        "src/trellis/html/_generated_interactive_elements.py",
        "src/trellis/html/_generated_interactive_elements.pyi",
        "src/trellis/html/_generated_sectioning_and_layout.py",
        "src/trellis/html/_generated_sectioning_and_layout.pyi",
        "src/trellis/html/_generated_table_content.py",
        "src/trellis/html/_generated_table_content.pyi",
        "src/trellis/html/_generated_text_blocks.py",
        "src/trellis/html/_generated_text_blocks.pyi",
      ]),
    );
    expect(payloads.map((payload) => payload.path)).not.toContain(
      "src/trellis/html/_generated_text_content.py",
    );

    const runtime = moduleByPath(payloads, "_generated_runtime.py").content;
    expect(runtime).toContain("Generated by html-codegen.");
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
    expect(runtime).not.toContain('    "_A",');

    const runtimeStub = moduleByPath(payloads, "_generated_runtime.pyi").content;
    expect(runtimeStub).toContain("from trellis.html._generated_interactive_elements import (");
    expect(runtimeStub).toContain("    _A,");

    const attributeTypes = moduleByPath(payloads, "_generated_attribute_types.pyi").content;
    expect(attributeTypes).toContain("Generated by html-codegen.");
    expect(attributeTypes).toContain("AriaAutocomplete = Literal[");
    expect(attributeTypes).toContain("InputType = Literal[");

    const layout = moduleByPath(payloads, "_generated_sectioning_and_layout.py").content;
    expect(layout).toContain("Generated HTML sectioning and layout runtime wrappers.");
    expect(layout).toContain("Internal codegen artifact for trellis.html.");
    expect(layout).toContain(
      "Reference: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements",
    );
    expect(layout).toContain("Generated by html-codegen.");
    expect(layout).toContain("from trellis.html._runtime_factory import create_html_element");
    expect(layout).toContain('Div = create_html_element("div", component_name="Div", export_name="Div", is_container=True');
    expect(layout).not.toContain("from trellis.html._generated_attribute_types");

    const layoutStub = moduleByPath(payloads, "_generated_sectioning_and_layout.pyi").content;
    expect(layoutStub).toContain("from trellis.html._generated_attribute_types import AriaAutocomplete");
    expect(layoutStub).toContain("def Div(");
    expect(layoutStub).toContain("aria_autocomplete: AriaAutocomplete | None = None");
    expect(layoutStub).toContain("aria_label: str | None = None");

    const interactive = moduleByPath(payloads, "_generated_interactive_elements.py").content;
    expect(interactive).toContain("Generated by html-codegen.");
    expect(interactive).toContain('create_html_element("a", component_name="A", export_name="_A", is_container=True');
    expect(interactive).not.toContain('    "_A",');

    const interactiveStub = moduleByPath(payloads, "_generated_interactive_elements.pyi").content;
    expect(interactiveStub).toContain("def _A(");
    expect(interactiveStub).toContain("inner_text: str,");

    const media = moduleByPath(payloads, "_generated_image_and_multimedia.py").content;
    expect(media).toContain("Generated by html-codegen.");
    expect(media).toContain('Audio = create_html_element("audio", component_name="Audio", export_name="Audio", is_container=True');

    const mediaStub = moduleByPath(payloads, "_generated_image_and_multimedia.pyi").content;
    expect(mediaStub).toContain("def Audio(");
    expect(mediaStub).toContain("auto_play: bool | None = None");
    expect(mediaStub).toContain("controls: bool | None = None");
    expect(mediaStub).toContain("src: str | None = None");

    const forms = moduleByPath(payloads, "_generated_forms.py").content;
    expect(forms).toContain("Generated by html-codegen.");
    expect(forms).toContain('Input = create_html_element("input", component_name="Input", export_name="Input"');
    expect(forms).not.toContain("from trellis.html._generated_attribute_types import InputType");

    const formsStub = moduleByPath(payloads, "_generated_forms.pyi").content;
    expect(formsStub).toContain("from trellis.html._generated_attribute_types import InputType");
    expect(formsStub).toContain('type: InputType = "text"');
    expect(formsStub).toContain('def Option(\n    inner_text: str | None = None,');

    const tables = moduleByPath(payloads, "_generated_table_content.py").content;
    expect(tables).toContain("Generated by html-codegen.");
    expect(tables).toContain('Table = create_html_element("table", component_name="Table", export_name="Table", is_container=True');

    const tablesStub = moduleByPath(payloads, "_generated_table_content.pyi").content;
    expect(tablesStub).toContain("def Table(");
    expect(tablesStub).toContain("frame: (");
    expect(tablesStub).toContain('        "border",');
    expect(tablesStub).not.toContain("frame: bool | None = None");

    const text = moduleByPath(payloads, "_generated_text_blocks.py").content;
    expect(text).toContain("Generated HTML text blocks runtime wrappers.");

    const documentMetadata = moduleByPath(payloads, "_generated_document_metadata.py").content;
    expect(documentMetadata).toContain('StyleTag = create_html_element("style", component_name="StyleTag", export_name="StyleTag"');
    expect(documentMetadata).toContain('Title = create_html_element("title", component_name="Title", export_name="Title"');

    const scripting = moduleByPath(payloads, "_generated_scripting_and_templates.py").content;
    expect(scripting).toContain('Script = create_html_element("script", component_name="Script", export_name="Script"');

    const textEdits = moduleByPath(payloads, "_generated_text_edits_and_ruby.py").content;
    expect(textEdits).toContain('Rp = create_html_element("rp", component_name="Rp", export_name="Rp"');
  });

  it("does not expose _text or fallback props in generated family modules", () => {
    const payloads = build_trellis_html_modules(sample_ir(), "2026-03-07T12:00:00.000Z");
    const familyModules = payloads.filter((payload) => payload.path.endsWith(".pyi") && payload.path.includes("_generated_") && !payload.path.endsWith("_generated_runtime.pyi") && !payload.path.endsWith("_generated_attribute_types.pyi"));
    const combined = familyModules.map((payload) => payload.content).join("\n");

    expect(combined).not.toContain("**props: tp.Any");
    expect(combined).not.toContain("    _text:");
    expect(combined).toContain("from collections.abc import Mapping");
    expect(combined).toContain("DataValue = str | int | float | bool | None");
  });
});
