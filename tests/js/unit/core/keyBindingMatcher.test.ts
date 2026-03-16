import { describe, it, expect, beforeEach, afterEach } from "vitest";
import {
  matchBindings,
  isSequenceBinding,
  serializeKeyboardEvent,
  type NormalizedBinding,
} from "@common/core/keyBindingMatcher";
import type { SerializedKeyBinding, SerializedSequenceBinding } from "@common/core/keyFilters";
import { KeyState } from "@common/core/keyState";

function makeKeyEvent(overrides: Partial<KeyboardEvent> = {}): KeyboardEvent {
  return {
    key: "",
    code: "",
    ctrlKey: false,
    shiftKey: false,
    altKey: false,
    metaKey: false,
    isComposing: false,
    type: "keydown",
    location: 0,
    repeat: false,
    timeStamp: 0,
    ...overrides,
  } as unknown as KeyboardEvent;
}

function makeSingleBinding(
  callbackId: string,
  key: string,
  overrides: Partial<SerializedKeyBinding> = {}
): NormalizedBinding {
  return {
    id: `test-${callbackId}`,
    callbackId,
    binding: {
      filter: { key, ctrl: false, shift: false, alt: false, meta: false, mod: false },
      handler: { __callback__: callbackId },
      event_type: "keydown",
      require_reset: true,
      ignore_in_inputs: false,
      ...overrides,
    },
  };
}

function makeSequenceBinding(
  callbackId: string,
  keys: string[],
  overrides: Partial<SerializedSequenceBinding> = {}
): NormalizedBinding {
  return {
    id: `test-seq-${callbackId}`,
    callbackId,
    binding: {
      sequence: {
        steps: keys.map((key) => ({
          key,
          ctrl: false,
          shift: false,
          alt: false,
          meta: false,
          mod: false,
        })),
        timeout_ms: 1000,
      },
      handler: { __callback__: callbackId },
      event_type: "keydown",
      require_reset: true,
      ignore_in_inputs: false,
      ...overrides,
    },
  };
}

describe("matchBindings", () => {
  let keyState: KeyState;

  beforeEach(() => {
    keyState = new KeyState();
  });

  afterEach(() => {
    keyState.dispose();
  });

  it("returns none when no bindings match", () => {
    const bindings = [makeSingleBinding("cb-1", "Escape")];
    const event = makeKeyEvent({ key: "a" });
    expect(matchBindings(bindings, event, "keydown", false, keyState)).toEqual({
      action: "none",
    });
  });

  it("returns fire for matching single binding", () => {
    const bindings = [makeSingleBinding("cb-1", "Escape")];
    const event = makeKeyEvent({ key: "Escape" });
    const result = matchBindings(bindings, event, "keydown", false, keyState);
    expect(result).toEqual({ action: "fire", callbackId: "cb-1", bindingIndex: 0 });
  });

  it("returns correct bindingIndex", () => {
    const bindings = [
      makeSingleBinding("cb-1", "Enter"),
      makeSingleBinding("cb-2", "Escape"),
    ];
    const event = makeKeyEvent({ key: "Escape" });
    const result = matchBindings(bindings, event, "keydown", false, keyState);
    expect(result).toEqual({ action: "fire", callbackId: "cb-2", bindingIndex: 1 });
  });

  it("returns fire for completed sequence", () => {
    const bindings = [makeSequenceBinding("cb-seq", ["G", "G"])];
    const event = makeKeyEvent({ key: "g" });

    // First key — advances
    const r1 = matchBindings(bindings, event, "keydown", false, keyState);
    expect(r1).toEqual({ action: "suppress" });

    // Second key — completes
    const r2 = matchBindings(bindings, event, "keydown", false, keyState);
    expect(r2).toEqual({ action: "fire", callbackId: "cb-seq", bindingIndex: 0 });
  });

  it("sequence complete takes priority over single match", () => {
    const bindings = [
      makeSequenceBinding("cb-seq", ["G", "G"]),
      makeSingleBinding("cb-single", "G"),
    ];
    const event = makeKeyEvent({ key: "g" });

    // First G — sequence advances, single suppressed
    expect(matchBindings(bindings, event, "keydown", false, keyState)).toEqual({
      action: "suppress",
    });

    // Second G — sequence completes, fires sequence not single
    const result = matchBindings(bindings, event, "keydown", false, keyState);
    expect(result).toEqual({ action: "fire", callbackId: "cb-seq", bindingIndex: 0 });
  });

  it("sequence advanced suppresses single bindings", () => {
    const bindings = [
      makeSequenceBinding("cb-seq", ["G", "I"]),
      makeSingleBinding("cb-single", "G"),
    ];
    const event = makeKeyEvent({ key: "g" });

    // G advances the sequence — single binding should not fire
    const result = matchBindings(bindings, event, "keydown", false, keyState);
    expect(result).toEqual({ action: "suppress" });
  });

  it("skips bindings with wrong eventType", () => {
    const bindings = [makeSingleBinding("cb-1", "Escape", { event_type: "keyup" })];
    const event = makeKeyEvent({ key: "Escape" });
    expect(matchBindings(bindings, event, "keydown", false, keyState)).toEqual({
      action: "none",
    });
  });

  it("skips bindings with ignore_in_inputs when in text input", () => {
    const bindings = [makeSingleBinding("cb-1", "K", { ignore_in_inputs: true })];
    const event = makeKeyEvent({ key: "k" });
    expect(matchBindings(bindings, event, "keydown", true, keyState)).toEqual({
      action: "none",
    });
  });

  it("fires ignore_in_inputs binding when not in text input", () => {
    const bindings = [makeSingleBinding("cb-1", "K", { ignore_in_inputs: true })];
    const event = makeKeyEvent({ key: "k" });
    const result = matchBindings(bindings, event, "keydown", false, keyState);
    expect(result.action).toBe("fire");
  });

  it("returns suppress for repeat when require_reset is true", () => {
    const bindings = [makeSingleBinding("cb-1", "Escape")];
    const event = makeKeyEvent({ key: "Escape" });

    // First press fires
    expect(matchBindings(bindings, event, "keydown", false, keyState).action).toBe("fire");
    // Second press (repeat) is suppressed
    expect(matchBindings(bindings, event, "keydown", false, keyState)).toEqual({
      action: "suppress",
    });
  });

  it("returns empty bindings as none", () => {
    expect(matchBindings([], makeKeyEvent(), "keydown", false, keyState)).toEqual({
      action: "none",
    });
  });
});

describe("isSequenceBinding", () => {
  it("returns true for sequence binding", () => {
    const b = {
      sequence: { steps: [], timeout_ms: 1000 },
      handler: { __callback__: "cb" },
      event_type: "keydown" as const,
      require_reset: true,
      ignore_in_inputs: false,
    };
    expect(isSequenceBinding(b)).toBe(true);
  });

  it("returns false for single binding", () => {
    const b = {
      filter: { key: "A", ctrl: false, shift: false, alt: false, meta: false, mod: false },
      handler: { __callback__: "cb" },
      event_type: "keydown" as const,
      require_reset: true,
      ignore_in_inputs: false,
    };
    expect(isSequenceBinding(b)).toBe(false);
  });
});

describe("serializeKeyboardEvent", () => {
  it("includes all fields with snake_case keys", () => {
    const event = {
      type: "keydown",
      key: "a",
      code: "KeyA",
      location: 0,
      altKey: false,
      ctrlKey: true,
      shiftKey: false,
      metaKey: false,
      repeat: false,
      isComposing: false,
      timeStamp: 12345,
    } as unknown as KeyboardEvent;

    const result = serializeKeyboardEvent(event);
    expect(result).toEqual({
      type: "keydown",
      key: "a",
      code: "KeyA",
      location: 0,
      alt_key: false,
      ctrl_key: true,
      shift_key: false,
      meta_key: false,
      repeat: false,
      is_composing: false,
      timestamp: 12345,
    });
  });
});
