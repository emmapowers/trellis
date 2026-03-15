import { describe, expect, it } from "vitest";

import { encode_data_attributes } from "../src/runtime/data_attr_encoder.js";

describe("data mapping", () => {
  it("maps data key suffixes to data-* dom attributes", () => {
    const dom = encode_data_attributes({ "test-id": "abc", enabled: true });
    expect(dom["data-test-id"]).toBe("abc");
    expect(dom["data-enabled"]).toBe(true);
  });

  it("rejects invalid suffix keys", () => {
    expect(() => encode_data_attributes({ "bad key": "x" })).toThrow(/Invalid data key/);
  });
});
