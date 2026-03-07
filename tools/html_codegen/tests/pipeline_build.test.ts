import { describe, expect, it } from "vitest";

import { build_ir_document } from "../src/pipeline/build.js";

describe("pipeline build", () => {
  it("builds only the first real html slice", async () => {
    const ir = await build_ir_document();

    expect(ir.elements.map((element) => element.python_name)).toEqual(["_A", "Div", "Img", "Input"]);
    expect(ir.elements.every((element) => element.namespace === "html")).toBe(true);
    expect(ir.attributes.some((attribute) => attribute.name_python === "href")).toBe(true);
    expect(ir.attributes.some((attribute) => attribute.name_python === "src")).toBe(true);
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

    const input_type = ir.attributes.find((attribute) => attribute.id === "html:input:type");
    expect(input_type?.required).toBe(false);
    expect(input_type?.default).toBe("text");
    expect(input_type?.type_expr.kind).toBe("union");
  });
});
