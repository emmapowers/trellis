import { describe, expect, it } from "vitest";

import { resolve_ir } from "../src/resolve/resolve.js";

describe("resolver precedence", () => {
  it("prefers react types and records provenance reason", () => {
    const ir = resolve_ir({
      elements: [],
      attributes: [
        {
          id: "html:video:auto_play",
          name_source: "autoPlay",
          type_expr: { kind: "primitive", name: "bool" },
          source: "react_ts",
        },
        {
          id: "html:video:auto_play",
          name_source: "autoplay",
          type_expr: { kind: "primitive", name: "str" },
          source: "webref",
        },
      ],
      events: [],
    });

    const attr = ir.attributes.find((item) => item.id === "html:video:auto_play");
    expect(attr?.source.winner).toBe("react_ts");
    expect(attr?.source.reason).toBe("runtime_precedence");
    expect(attr?.name_python).toBe("auto_play");
  });
});
