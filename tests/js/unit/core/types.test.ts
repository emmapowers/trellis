import { describe, it, expect, vi } from "vitest";
import { isCallbackRef, ElementKind, Mutable, resetMutableStates } from "@common/core/types";

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

describe("Mutable", () => {
  beforeEach(() => {
    resetMutableStates();
  });

  it("setValue sends value and version", () => {
    const onEvent = vi.fn();
    const m = new Mutable<string>(
      { __mutable__: "test-id", value: "initial", version: 0 },
      onEvent
    );

    m.setValue("x");
    expect(onEvent).toHaveBeenCalledWith("test-id", ["x", 1]);

    m.setValue("y");
    expect(onEvent).toHaveBeenCalledWith("test-id", ["y", 2]);
  });

  it("value returns optimistic value after setValue", () => {
    const onEvent = vi.fn();
    const m = new Mutable<string>(
      { __mutable__: "test-id", value: "initial", version: 0 },
      onEvent
    );

    m.setValue("new");
    expect(m.value).toBe("new");
  });

  it("value returns server value when version matches", () => {
    const onEvent = vi.fn();

    // Simulate: client sends version 1, server echoes version 1
    const m1 = new Mutable<string>(
      { __mutable__: "test-id", value: "old", version: 0 },
      onEvent
    );
    m1.setValue("new"); // localVersion becomes 1

    // Server responds with version 1 (acknowledging client's update)
    const m2 = new Mutable<string>(
      { __mutable__: "test-id", value: "server-new", version: 1 },
      onEvent
    );
    expect(m2.value).toBe("server-new");
  });

  it("ignores stale server value", () => {
    const onEvent = vi.fn();

    const m1 = new Mutable<string>(
      { __mutable__: "test-id", value: "old", version: 0 },
      onEvent
    );
    m1.setValue("new"); // localVersion becomes 1

    // Server responds with stale version 0 (hasn't seen client's update yet)
    const m2 = new Mutable<string>(
      { __mutable__: "test-id", value: "stale-server", version: 0 },
      onEvent
    );
    expect(m2.value).toBe("new"); // optimistic value preserved
  });

  it("state persists across instances with same id", () => {
    const onEvent = vi.fn();

    const m1 = new Mutable<string>(
      { __mutable__: "shared-id", value: "v1", version: 0 },
      onEvent
    );
    m1.setValue("optimistic");

    // New instance with same id shares the state
    const m2 = new Mutable<string>(
      { __mutable__: "shared-id", value: "v1", version: 0 },
      onEvent
    );
    expect(m2.value).toBe("optimistic");
  });
});
