import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { KeyState } from "@common/core/keyState";
import { SerializedKeyFilter } from "@common/core/keyFilters";

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

describe("KeyState.shouldFire (requireReset)", () => {
  let keyState: KeyState;

  beforeEach(() => {
    keyState = new KeyState();
  });

  afterEach(() => {
    keyState.dispose();
  });

  it("fires on first keydown", () => {
    const event = makeKeyEvent({ key: "s" });
    expect(keyState.shouldFire("binding-1", true, event)).toBe(true);
  });

  it("suppresses repeat keydowns", () => {
    const event = makeKeyEvent({ key: "s" });
    expect(keyState.shouldFire("binding-1", true, event)).toBe(true);
    expect(keyState.shouldFire("binding-1", true, event)).toBe(false);
    expect(keyState.shouldFire("binding-1", true, event)).toBe(false);
  });

  it("resets after keyup", () => {
    const keydown = makeKeyEvent({ key: "s" });
    expect(keyState.shouldFire("binding-1", true, keydown)).toBe(true);
    expect(keyState.shouldFire("binding-1", true, keydown)).toBe(false);

    // Simulate keyup via window event
    window.dispatchEvent(new KeyboardEvent("keyup", { key: "s" }));

    expect(keyState.shouldFire("binding-1", true, keydown)).toBe(true);
  });

  it("modifier keyup clears all non-modifier held keys (macOS)", () => {
    const event = makeKeyEvent({ key: "s", metaKey: true });
    expect(keyState.shouldFire("binding-1", true, event)).toBe(true);

    // Meta keyup should clear held "s" key
    window.dispatchEvent(new KeyboardEvent("keyup", { key: "Meta" }));

    expect(keyState.shouldFire("binding-1", true, event)).toBe(true);
  });

  it("window blur clears all state", () => {
    const event = makeKeyEvent({ key: "s" });
    expect(keyState.shouldFire("binding-1", true, event)).toBe(true);

    window.dispatchEvent(new Event("blur"));

    expect(keyState.shouldFire("binding-1", true, event)).toBe(true);
  });

  it("always fires when requireReset is false", () => {
    const event = makeKeyEvent({ key: "s" });
    expect(keyState.shouldFire("binding-1", false, event)).toBe(true);
    expect(keyState.shouldFire("binding-1", false, event)).toBe(true);
    expect(keyState.shouldFire("binding-1", false, event)).toBe(true);
  });

  it("keyup for F1 does not clear F10 binding (endsWith match)", () => {
    // Fire F10 binding
    const f10Event = makeKeyEvent({ key: "F10" });
    expect(keyState.shouldFire("binding-1", true, f10Event)).toBe(true);
    expect(keyState.shouldFire("binding-1", true, f10Event)).toBe(false);

    // F1 keyup should NOT clear F10 binding — endsWith(":key:F1") must not
    // match a binding tracked as ":key:F10"
    window.dispatchEvent(new KeyboardEvent("keyup", { key: "F1" }));

    // F10 binding should still be suppressed
    expect(keyState.shouldFire("binding-1", true, f10Event)).toBe(false);
  });
});

describe("KeyState.advanceSequence", () => {
  let keyState: KeyState;

  beforeEach(() => {
    keyState = new KeyState();
  });

  afterEach(() => {
    keyState.dispose();
  });

  it("completes a two-step sequence", () => {
    const steps = [makeFilter({ key: "G" }), makeFilter({ key: "G" })];
    const event = makeKeyEvent({ key: "g" });

    expect(keyState.advanceSequence("seq-1", steps, 1000, event)).toBe("advanced");
    expect(keyState.advanceSequence("seq-1", steps, 1000, event)).toBe("complete");
  });

  it("resets on timeout", () => {
    const steps = [makeFilter({ key: "G" }), makeFilter({ key: "G" })];
    const event = makeKeyEvent({ key: "g" });

    const now = Date.now();
    vi.spyOn(Date, "now").mockReturnValue(now);

    // First key press
    expect(keyState.advanceSequence("seq-1", steps, 100, event)).toBe("advanced");

    // Advance past timeout — second press should NOT complete the sequence
    // but it does restart, matching step 0 again
    vi.spyOn(Date, "now").mockReturnValue(now + 200);
    expect(keyState.advanceSequence("seq-1", steps, 100, event)).toBe("advanced");

    // Sequence restarted, so this is step 2 of a fresh attempt
    vi.spyOn(Date, "now").mockReturnValue(now + 250);
    expect(keyState.advanceSequence("seq-1", steps, 100, event)).toBe("complete");

    vi.restoreAllMocks();
  });

  it("resets on wrong key", () => {
    const steps = [makeFilter({ key: "G" }), makeFilter({ key: "G" })];
    const gEvent = makeKeyEvent({ key: "g" });
    const xEvent = makeKeyEvent({ key: "x" });

    expect(keyState.advanceSequence("seq-1", steps, 1000, gEvent)).toBe("advanced");
    expect(keyState.advanceSequence("seq-1", steps, 1000, xEvent)).toBe("none");
    // Should have reset — need to start over
    expect(keyState.advanceSequence("seq-1", steps, 1000, gEvent)).toBe("advanced");
    expect(keyState.advanceSequence("seq-1", steps, 1000, gEvent)).toBe("complete");
  });

  it("restarts from step 0 on partial mismatch", () => {
    const steps = [makeFilter({ key: "G" }), makeFilter({ key: "I" })];
    const gEvent = makeKeyEvent({ key: "g" });

    // G, then another G (wrong for step 2 but valid for step 1)
    expect(keyState.advanceSequence("seq-1", steps, 1000, gEvent)).toBe("advanced");
    // Mismatch at step 2, but G matches step 0 — restarts and advances
    expect(keyState.advanceSequence("seq-1", steps, 1000, gEvent)).toBe("advanced");
    // After restart, we're at step 1 again
    const iEvent = makeKeyEvent({ key: "i" });
    expect(keyState.advanceSequence("seq-1", steps, 1000, iEvent)).toBe("complete");
  });

  it("ignores repeat keydown events", () => {
    const steps = [makeFilter({ key: "G" }), makeFilter({ key: "G" })];
    const event = makeKeyEvent({ key: "g" });
    const repeatEvent = makeKeyEvent({ key: "g", repeat: true });

    // First press advances to step 1
    expect(keyState.advanceSequence("seq-1", steps, 1000, event)).toBe("advanced");
    // Repeat events should be ignored (return "none" without advancing)
    expect(keyState.advanceSequence("seq-1", steps, 1000, repeatEvent)).toBe("none");
    expect(keyState.advanceSequence("seq-1", steps, 1000, repeatEvent)).toBe("none");
    // Real second press completes the sequence
    expect(keyState.advanceSequence("seq-1", steps, 1000, event)).toBe("complete");
  });

  it("returns none for empty steps", () => {
    const event = makeKeyEvent({ key: "g" });
    expect(keyState.advanceSequence("seq-1", [], 1000, event)).toBe("none");
  });

  it("shared prefix advances both sequences independently", () => {
    // Two sequences share the same first step: Ctrl+K
    const stepsA = [makeFilter({ key: "K", ctrl: true }), makeFilter({ key: "S" })];
    const stepsB = [makeFilter({ key: "K", ctrl: true }), makeFilter({ key: "D" })];
    const kEvent = makeKeyEvent({ key: "k", ctrlKey: true });

    // First step advances both
    expect(keyState.advanceSequence("seq-a", stepsA, 1000, kEvent)).toBe("advanced");
    expect(keyState.advanceSequence("seq-b", stepsB, 1000, kEvent)).toBe("advanced");

    // S completes A, resets B
    const sEvent = makeKeyEvent({ key: "s" });
    expect(keyState.advanceSequence("seq-a", stepsA, 1000, sEvent)).toBe("complete");
    expect(keyState.advanceSequence("seq-b", stepsB, 1000, sEvent)).toBe("none");
  });

  it("shared prefix: second sequence still works after first completes", () => {
    const stepsA = [makeFilter({ key: "K", ctrl: true }), makeFilter({ key: "S" })];
    const stepsB = [makeFilter({ key: "K", ctrl: true }), makeFilter({ key: "D" })];
    const kEvent = makeKeyEvent({ key: "k", ctrlKey: true });

    // Advance both
    keyState.advanceSequence("seq-a", stepsA, 1000, kEvent);
    keyState.advanceSequence("seq-b", stepsB, 1000, kEvent);

    // Complete A with S
    const sEvent = makeKeyEvent({ key: "s" });
    expect(keyState.advanceSequence("seq-a", stepsA, 1000, sEvent)).toBe("complete");

    // B was reset by the mismatch. Start fresh for B.
    expect(keyState.advanceSequence("seq-b", stepsB, 1000, kEvent)).toBe("advanced");
    const dEvent = makeKeyEvent({ key: "d" });
    expect(keyState.advanceSequence("seq-b", stepsB, 1000, dEvent)).toBe("complete");
  });

  it("modifier-only keydown returns none without resetting", () => {
    const steps = [makeFilter({ key: "K", ctrl: true }), makeFilter({ key: "S" })];
    const kEvent = makeKeyEvent({ key: "k", ctrlKey: true });
    const ctrlEvent = makeKeyEvent({ key: "Control" });

    // Advance to step 1
    expect(keyState.advanceSequence("seq-1", steps, 1000, kEvent)).toBe("advanced");
    // Bare modifier keydown should be ignored, not reset
    expect(keyState.advanceSequence("seq-1", steps, 1000, ctrlEvent)).toBe("none");
    // Can still complete
    const sEvent = makeKeyEvent({ key: "s" });
    expect(keyState.advanceSequence("seq-1", steps, 1000, sEvent)).toBe("complete");
  });
});
