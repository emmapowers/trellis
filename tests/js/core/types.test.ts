import { describe, it, expect } from "vitest";
import { isCallbackRef, ElementKind } from "@common/core/types";

describe("isCallbackRef", () => {
  it("returns true for valid callback refs", () => {
    expect(isCallbackRef({ __callback__: "cb_123" })).toBe(true);
    expect(isCallbackRef({ __callback__: "" })).toBe(true);
  });

  it("returns false for non-objects", () => {
    expect(isCallbackRef(null)).toBe(false);
    expect(isCallbackRef(undefined)).toBe(false);
    expect(isCallbackRef("string")).toBe(false);
    expect(isCallbackRef(123)).toBe(false);
    expect(isCallbackRef(true)).toBe(false);
  });

  it("returns false for objects without __callback__", () => {
    expect(isCallbackRef({})).toBe(false);
    expect(isCallbackRef({ callback: "cb_123" })).toBe(false);
    expect(isCallbackRef({ other: "value" })).toBe(false);
  });

  it("returns false when __callback__ is not a string", () => {
    expect(isCallbackRef({ __callback__: 123 })).toBe(false);
    expect(isCallbackRef({ __callback__: null })).toBe(false);
    expect(isCallbackRef({ __callback__: {} })).toBe(false);
  });
});

describe("ElementKind", () => {
  it("has expected values matching Python ElementKind", () => {
    expect(ElementKind.REACT_COMPONENT).toBe("react_component");
    expect(ElementKind.JSX_ELEMENT).toBe("jsx_element");
    expect(ElementKind.TEXT).toBe("text");
  });
});
