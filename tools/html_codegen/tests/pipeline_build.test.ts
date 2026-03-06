import { describe, expect, it } from "vitest";

import { build_ir_document } from "../src/pipeline/build.js";

describe("pipeline build", () => {
  it("builds only the first real html slice", async () => {
    const ir = await build_ir_document();

    expect(ir.elements.map((element) => element.python_name)).toEqual(["A", "Div", "Img", "Input"]);
    expect(ir.elements.every((element) => element.namespace === "html")).toBe(true);
    expect(ir.attributes.some((attribute) => attribute.name_python === "href")).toBe(true);
    expect(ir.attributes.some((attribute) => attribute.name_python === "src")).toBe(true);
    expect(ir.attributes.some((attribute) => attribute.name_python === "on_click")).toBe(true);
  });
});
