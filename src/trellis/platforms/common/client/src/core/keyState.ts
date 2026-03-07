/**
 * Shared state for requireReset (held key tracking) and sequence state machines.
 */

import { matchesKeyFilter, SerializedKeyFilter } from "./keyFilters";

const MODIFIER_KEYS = new Set([
  "Control",
  "Shift",
  "Alt",
  "Meta",
]);

export class KeyState {
  private firedBindings = new Set<string>();
  private heldKeys = new Set<string>();
  private sequenceStates = new Map<
    string,
    { currentIndex: number; lastKeyTime: number }
  >();
  private keyupHandler: (e: KeyboardEvent) => void;
  private blurHandler: () => void;

  constructor() {
    this.keyupHandler = (e: KeyboardEvent) => {
      this.heldKeys.delete(e.key);
      // Remove bindings that depended on this key
      for (const bindingId of this.firedBindings) {
        if (bindingId.includes(`key:${e.key}`)) {
          this.firedBindings.delete(bindingId);
        }
      }
      // macOS swallows keyup for non-modifier keys held during modifier combos.
      // On modifier keyup, clear all non-modifier held keys to reset state.
      if (MODIFIER_KEYS.has(e.key)) {
        for (const key of this.heldKeys) {
          if (!MODIFIER_KEYS.has(key)) {
            this.heldKeys.delete(key);
          }
        }
        // Clear all fired bindings since modifier is released
        this.firedBindings.clear();
      }
    };

    this.blurHandler = () => {
      this.heldKeys.clear();
      this.firedBindings.clear();
      this.sequenceStates.clear();
    };

    if (typeof window !== "undefined") {
      window.addEventListener("keyup", this.keyupHandler);
      window.addEventListener("blur", this.blurHandler);
    }
  }

  /**
   * Check whether a binding should fire, respecting requireReset.
   * Returns true if the binding should fire, false if suppressed (repeat).
   */
  shouldFire(
    bindingId: string,
    requireReset: boolean,
    event: KeyboardEvent
  ): boolean {
    const keyId = `${bindingId}:key:${event.key}`;
    this.heldKeys.add(event.key);

    if (!requireReset) return true;

    if (this.firedBindings.has(keyId)) {
      // Key is held, suppress repeat — but still preventDefault
      return false;
    }

    this.firedBindings.add(keyId);
    return true;
  }

  /**
   * Advance a sequence state machine. Returns true if the sequence is complete.
   */
  advanceSequence(
    bindingId: string,
    steps: SerializedKeyFilter[],
    timeoutMs: number,
    event: KeyboardEvent
  ): boolean {
    // Ignore modifier-only keydown events — they don't advance or reset
    // sequences. Without this, chords like Mod+K,Mod+S break because the
    // bare Meta keydown between the two presses resets the state machine.
    if (MODIFIER_KEYS.has(event.key)) return false;

    const now = Date.now();
    let state = this.sequenceStates.get(bindingId);

    if (!state) {
      state = { currentIndex: 0, lastKeyTime: 0 };
      this.sequenceStates.set(bindingId, state);
    }

    // Timeout — reset
    if (state.currentIndex > 0 && now - state.lastKeyTime > timeoutMs) {
      state.currentIndex = 0;
    }

    // Check if current event matches the current step
    if (matchesKeyFilter(event, steps[state.currentIndex])) {
      state.currentIndex++;
      state.lastKeyTime = now;

      if (state.currentIndex >= steps.length) {
        // Sequence complete
        state.currentIndex = 0;
        return true;
      }
      return false;
    }

    // No match at current step — try restarting from step 0
    if (state.currentIndex > 0) {
      state.currentIndex = 0;
      if (matchesKeyFilter(event, steps[0])) {
        state.currentIndex = 1;
        state.lastKeyTime = now;
      }
    }

    return false;
  }

  dispose(): void {
    if (typeof window !== "undefined") {
      window.removeEventListener("keyup", this.keyupHandler);
      window.removeEventListener("blur", this.blurHandler);
    }
    this.firedBindings.clear();
    this.heldKeys.clear();
    this.sequenceStates.clear();
  }
}
