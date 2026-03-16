/**
 * Shared key binding matching logic for both focus-scoped (.on_key)
 * and global (HotKey) key handlers.
 *
 * Owns the two-pass matching algorithm: sequences first, then singles.
 * Callers normalize their bindings into NormalizedBinding[], call
 * matchBindings(), and handle the result with their own dispatch logic.
 */

import {
  isTextInput,
  matchesKeyFilter,
  type SerializedKeyBinding,
  type SerializedSequenceBinding,
} from "./keyFilters";
import type { KeyState } from "./keyState";

export interface NormalizedBinding {
  /** Caller-assigned ID for KeyState tracking (e.g. "global-seq-cb1") */
  id: string;
  /** Handler callback ID returned to the caller for dispatch */
  callbackId: string;
  /** The underlying binding data */
  binding: SerializedKeyBinding | SerializedSequenceBinding;
}

export type MatchResult =
  | { action: "fire"; callbackId: string; bindingIndex: number }
  | { action: "suppress" }
  | { action: "none" };

export function isSequenceBinding(
  b: SerializedKeyBinding | SerializedSequenceBinding
): b is SerializedSequenceBinding {
  return "sequence" in b;
}

export function serializeKeyboardEvent(
  event: KeyboardEvent
): Record<string, unknown> {
  return {
    type: event.type,
    key: event.key,
    code: event.code,
    location: event.location,
    alt_key: event.altKey,
    ctrl_key: event.ctrlKey,
    shift_key: event.shiftKey,
    meta_key: event.metaKey,
    repeat: event.repeat,
    is_composing: event.isComposing,
    timestamp: event.timeStamp,
  };
}

/**
 * Two-pass key binding matcher.
 *
 * Pass 1: Check all sequence bindings. If any completes, return "fire".
 *         If any advances (partial match), return "suppress" after checking all.
 * Pass 2: Check all single-key bindings (only if no sequence advanced).
 *         First match returns "fire" or "suppress" (repeat suppressed).
 */
export function matchBindings(
  bindings: NormalizedBinding[],
  event: KeyboardEvent,
  eventType: "keydown" | "keyup",
  inTextInput: boolean,
  keyState: KeyState
): MatchResult {
  let sequenceAdvanced = false;

  // Pass 1: sequences
  for (let i = 0; i < bindings.length; i++) {
    const { id, callbackId, binding } = bindings[i];
    if (!isSequenceBinding(binding)) continue;
    if (binding.event_type !== eventType) continue;
    if (binding.ignore_in_inputs && inTextInput) continue;

    const result = keyState.advanceSequence(
      id,
      binding.sequence.steps,
      binding.sequence.timeout_ms,
      event
    );
    if (result === "complete") {
      return { action: "fire", callbackId, bindingIndex: i };
    }
    if (result === "advanced") {
      sequenceAdvanced = true;
    }
  }

  if (sequenceAdvanced) {
    return { action: "suppress" };
  }

  // Pass 2: single-key bindings
  for (let i = 0; i < bindings.length; i++) {
    const { id, callbackId, binding } = bindings[i];
    if (isSequenceBinding(binding)) continue;
    if (binding.event_type !== eventType) continue;
    if (binding.ignore_in_inputs && inTextInput) continue;
    if (!matchesKeyFilter(event, binding.filter)) continue;

    const shouldFire = keyState.shouldFire(id, binding.require_reset, event);
    if (!shouldFire) {
      return { action: "suppress" };
    }
    return { action: "fire", callbackId, bindingIndex: i };
  }

  return { action: "none" };
}
