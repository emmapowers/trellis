import { describe, it, expect } from "vitest";
import { matchesKeyFilter, isTextInput, SerializedKeyFilter } from "@common/core/keyFilters";

function makeKeyEvent(overrides: Partial<KeyboardEvent> = {}): KeyboardEvent {
  return {
    key: "",
    code: "",
    ctrlKey: false,
    shiftKey: false,
    altKey: false,
    metaKey: false,
    isComposing: false,
    ...overrides,
  } as unknown as KeyboardEvent;
}

function makeFilter(overrides: Partial<SerializedKeyFilter> = {}): SerializedKeyFilter {
  return {
    key: "S",
    ctrl: false,
    shift: false,
    alt: false,
    meta: false,
    mod: false,
    ...overrides,
  };
}

describe("matchesKeyFilter", () => {
  it("matches exact key", () => {
    const event = makeKeyEvent({ key: "S" });
    expect(matchesKeyFilter(event, makeFilter({ key: "S" }))).toBe(true);
  });

  it("matches case-insensitive single letter", () => {
    const event = makeKeyEvent({ key: "s" });
    expect(matchesKeyFilter(event, makeFilter({ key: "S" }))).toBe(true);
  });

  it("rejects extra modifier", () => {
    const event = makeKeyEvent({ key: "S", ctrlKey: true });
    expect(matchesKeyFilter(event, makeFilter({ key: "S" }))).toBe(false);
  });

  it("rejects missing modifier", () => {
    const event = makeKeyEvent({ key: "S" });
    expect(matchesKeyFilter(event, makeFilter({ key: "S", ctrl: true }))).toBe(false);
  });

  it("matches Enter key", () => {
    const event = makeKeyEvent({ key: "Enter" });
    expect(matchesKeyFilter(event, makeFilter({ key: "Enter" }))).toBe(true);
  });

  it("matches Escape key", () => {
    const event = makeKeyEvent({ key: "Escape" });
    expect(matchesKeyFilter(event, makeFilter({ key: "Escape" }))).toBe(true);
  });

  it("skips when isComposing", () => {
    const event = makeKeyEvent({ key: "S", isComposing: true });
    expect(matchesKeyFilter(event, makeFilter({ key: "S" }))).toBe(false);
  });

  it("falls back to event.code for dead keys", () => {
    const event = makeKeyEvent({ key: "Dead", code: "KeyS" });
    expect(matchesKeyFilter(event, makeFilter({ key: "S" }))).toBe(true);
  });

  it("falls back to event.code for modifier combo producing wrong key", () => {
    // Cmd+Option+T produces "†" on macOS
    const event = makeKeyEvent({
      key: "†",
      code: "KeyT",
      metaKey: true,
      altKey: true,
    });
    expect(
      matchesKeyFilter(event, makeFilter({ key: "T", meta: true, alt: true }))
    ).toBe(true);
  });

  it("does NOT fall back to event.code for bare key (non-QWERTY protection)", () => {
    // On AZERTY, pressing physical "Q" key produces "A" as event.key
    // We should trust event.key, not event.code
    const event = makeKeyEvent({ key: "A", code: "KeyQ" });
    expect(matchesKeyFilter(event, makeFilter({ key: "Q" }))).toBe(false);
    expect(matchesKeyFilter(event, makeFilter({ key: "A" }))).toBe(true);
  });

  it("handles undefined event.code gracefully", () => {
    const event = makeKeyEvent({ key: "Dead" });
    // No code property at all — should not crash
    expect(matchesKeyFilter(event, makeFilter({ key: "S" }))).toBe(false);
  });

  it("matches mod key (resolves to ctrlKey in jsdom/non-Mac)", () => {
    // In jsdom, navigator.platform is not Mac, so mod resolves to ctrlKey
    const event = makeKeyEvent({ key: "S", ctrlKey: true });
    expect(matchesKeyFilter(event, makeFilter({ key: "S", mod: true }))).toBe(true);
  });

  it("rejects mod key without the correct modifier", () => {
    // metaKey on non-Mac shouldn't match mod
    const event = makeKeyEvent({ key: "S", metaKey: true });
    expect(matchesKeyFilter(event, makeFilter({ key: "S", mod: true }))).toBe(false);
  });
});

describe("isTextInput", () => {
  it("returns true for textarea", () => {
    const el = document.createElement("textarea");
    expect(isTextInput(el)).toBe(true);
  });

  it("returns true for text input", () => {
    const el = document.createElement("input");
    el.type = "text";
    expect(isTextInput(el)).toBe(true);
  });

  it("returns false for button input", () => {
    const el = document.createElement("input");
    el.type = "button";
    expect(isTextInput(el)).toBe(false);
  });

  it("returns false for submit input", () => {
    const el = document.createElement("input");
    el.type = "submit";
    expect(isTextInput(el)).toBe(false);
  });

  it("returns false for reset input", () => {
    const el = document.createElement("input");
    el.type = "reset";
    expect(isTextInput(el)).toBe(false);
  });

  it("returns true for contentEditable=true", () => {
    const el = document.createElement("div");
    el.contentEditable = "true";
    expect(isTextInput(el)).toBe(true);
  });

  it("returns false for contentEditable=false", () => {
    const el = document.createElement("div");
    el.contentEditable = "false";
    expect(isTextInput(el)).toBe(false);
  });

  it("returns true for select", () => {
    const el = document.createElement("select");
    expect(isTextInput(el)).toBe(true);
  });

  it("returns false for null", () => {
    expect(isTextInput(null)).toBe(false);
  });

  it("returns false for div", () => {
    const el = document.createElement("div");
    expect(isTextInput(el)).toBe(false);
  });
});
