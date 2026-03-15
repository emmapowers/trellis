import { describe, expect, it } from "vitest";

import { build_ir_document } from "../src/pipeline/build.js";

describe("pipeline build", () => {
  it("builds the full html element policy surface", async () => {
    const ir = await build_ir_document();

    expect(ir.elements).toHaveLength(116);
    expect(ir.elements.every((element) => element.namespace === "html")).toBe(true);
    expect(ir.elements.some((element) => element.tag_name === "webview")).toBe(false);
    expect(ir.elements.some((element) => element.tag_name === "noindex")).toBe(false);
    expect(ir.elements.some((element) => element.python_name === "P")).toBe(true);
    expect(ir.elements.some((element) => element.python_name === "Option")).toBe(true);
    expect(ir.elements.some((element) => element.python_name === "Script")).toBe(true);
    expect(ir.elements.some((element) => element.python_name === "StyleTag")).toBe(true);
    expect(ir.elements.some((element) => element.python_name === "Textarea")).toBe(true);
    expect(ir.attributes.some((attribute) => attribute.name_python === "href")).toBe(true);
    expect(ir.attributes.some((attribute) => attribute.name_python === "src")).toBe(true);
    expect(ir.attributes.some((attribute) => attribute.name_python === "aria_label")).toBe(true);
    expect(ir.attributes.some((attribute) => attribute.name_python === "on_click")).toBe(true);
    expect(ir.events.some((event) => event.name_python === "on_click")).toBe(true);
    expect(
      ir.event_handlers.some((event_handler) => event_handler.handler_name === "MouseEventHandler"),
    ).toBe(true);
    expect(ir.dataclasses.some((dataclass_def) => dataclass_def.name === "Event")).toBe(true);
    expect(ir.dataclasses.some((dataclass_def) => dataclass_def.name === "UIEvent")).toBe(true);
    expect(ir.dataclasses.some((dataclass_def) => dataclass_def.name === "SubmitEvent")).toBe(
      true,
    );
    expect(ir.dataclasses.some((dataclass_def) => dataclass_def.name === "DataTransfer")).toBe(
      true,
    );
    expect(ir.dataclasses.some((dataclass_def) => dataclass_def.name === "File")).toBe(true);
    expect(ir.dataclasses.some((dataclass_def) => dataclass_def.name === "MouseEvent")).toBe(true);
    expect(ir.dataclasses.some((dataclass_def) => dataclass_def.name === "DragEvent")).toBe(true);

    const image_src = ir.attributes.find((attribute) => attribute.id === "html:img:src");
    expect(image_src?.required).toBe(false);
    expect(image_src?.type_expr.kind).toBe("nullable");

    const click_event = ir.events.find((event) => event.id === "html:global:on_click");
    expect(click_event).toMatchObject({
      dom_event_name: "click",
      payload_name: "MouseEvent",
      handler_name: "MouseEventHandler",
    });

    const change_event = ir.events.find((event) => event.id === "html:global:on_change");
    expect(change_event).toMatchObject({
      dom_event_name: "change",
      payload_name: "Event",
      handler_name: "EventHandler",
    });

    const style_attribute = ir.attributes.find((attribute) => attribute.id === "html:global:style");
    expect(style_attribute?.type_expr).toEqual({
      kind: "nullable",
      item: { kind: "style_object" },
    });

    const aria_label_attribute = ir.attributes.find(
      (attribute) => attribute.id === "html:global:aria_label",
    );
    expect(aria_label_attribute).toMatchObject({
      name_source: "aria-label",
      name_python: "aria_label",
      applies_to: "global",
      category: "aria",
    });

    const audio_auto_play = ir.attributes.find((attribute) => attribute.id === "html:audio:auto_play");
    expect(audio_auto_play?.name_source).toBe("autoPlay");
    expect(audio_auto_play?.type_expr.kind).toBe("nullable");

    const input_type = ir.attributes.find((attribute) => attribute.id === "html:input:type");
    expect(input_type?.required).toBe(false);
    expect(input_type?.default).toBe("text");
    expect(input_type?.type_expr.kind).toBe("union");

    expect(ir.attributes.find((attribute) => attribute.id === "html:link:as_")?.name_source).toBe("as");
    expect(ir.attributes.find((attribute) => attribute.id === "html:script:async_")?.name_source).toBe(
      "async",
    );
    expect(ir.attributes.find((attribute) => attribute.id === "html:div:is_")?.name_source).toBe("is");
    expect(ir.attributes.find((attribute) => attribute.id === "html:object:data_")?.name_source).toBe(
      "data",
    );

    function find_element(tag_name: string) {
      return ir.elements.find((element) => element.tag_name === tag_name);
    }

    expect(find_element("a")).toMatchObject({
      python_name: "_A",
      is_container: true,
      text_behavior: "public_helper",
    });
    expect(find_element("div")).toMatchObject({
      python_name: "Div",
      is_container: true,
      text_behavior: "public_helper",
    });
    expect(find_element("img")).toMatchObject({
      python_name: "Img",
      is_container: false,
      text_behavior: "none",
    });
    expect(find_element("option")).toMatchObject({
      python_name: "Option",
      is_container: false,
      text_behavior: "public_helper",
    });
    expect(find_element("textarea")).toMatchObject({
      python_name: "Textarea",
      is_container: false,
      text_behavior: "public_helper",
    });
    expect(find_element("iframe")).toMatchObject({
      python_name: "Iframe",
      is_container: false,
      text_behavior: "public_helper",
    });
    expect(find_element("script")).toMatchObject({
      python_name: "Script",
      is_container: false,
      text_behavior: "public_helper",
    });
    expect(find_element("style")).toMatchObject({
      python_name: "StyleTag",
      is_container: false,
      text_behavior: "public_helper",
    });
    expect(find_element("title")).toMatchObject({
      python_name: "Title",
      is_container: false,
      text_behavior: "public_helper",
    });
    expect(find_element("rp")).toMatchObject({
      python_name: "Rp",
      is_container: false,
      text_behavior: "public_helper",
    });
    expect(find_element("picture")).toMatchObject({
      python_name: "Picture",
      is_container: true,
      text_behavior: "none",
    });
    expect(find_element("progress")).toMatchObject({
      python_name: "Progress",
      is_container: true,
      text_behavior: "none",
    });

    const table_frame = ir.attributes.find((attribute) => attribute.id === "html:table:frame");
    expect(table_frame?.type_expr).toEqual({
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
    });

    expect(ir.events.find((event) => event.id === "html:global:on_load")).toMatchObject({
      dom_event_name: "load",
      payload_name: "Event",
      handler_name: "EventHandler",
    });
    expect(ir.events.find((event) => event.id === "html:global:on_play")).toMatchObject({
      dom_event_name: "play",
      payload_name: "Event",
      handler_name: "EventHandler",
    });

    const focus_event = ir.dataclasses.find((dataclass_def) => dataclass_def.name === "FocusEvent");
    expect(focus_event?.base).toBe("UIEvent");
    expect(focus_event?.fields.some((field) => field.name_python === "related_target")).toBe(true);

    const input_event = ir.dataclasses.find((dataclass_def) => dataclass_def.name === "InputEvent");
    expect(input_event?.base).toBe("UIEvent");
    expect(input_event?.fields.some((field) => field.name_python === "data_transfer")).toBe(true);

    const submit_event = ir.dataclasses.find((dataclass_def) => dataclass_def.name === "SubmitEvent");
    expect(submit_event?.fields.some((field) => field.name_python === "submitter")).toBe(true);
  });
});
