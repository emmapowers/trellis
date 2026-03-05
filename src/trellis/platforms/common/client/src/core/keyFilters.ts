/**
 * Shared key filter matching logic for both .on_key() and HotKey().
 */

export interface SerializedKeyFilter {
  key: string;
  ctrl: boolean;
  shift: boolean;
  alt: boolean;
  meta: boolean;
  mod: boolean;
}

export interface SerializedSequence {
  steps: SerializedKeyFilter[];
  timeout_ms: number;
}

export interface SerializedKeyBinding {
  filter: SerializedKeyFilter;
  handler: { __callback__: string };
  event_type: "keydown" | "keyup";
  require_reset: boolean;
  ignore_in_inputs: boolean;
}

export interface SerializedSequenceBinding {
  sequence: SerializedSequence;
  handler: { __callback__: string };
  event_type: "keydown" | "keyup";
  require_reset: boolean;
  ignore_in_inputs: boolean;
}

const IS_MAC =
  typeof navigator !== "undefined" && /Mac|iPhone|iPad/.test(navigator.platform);

/**
 * Check if a KeyboardEvent matches a serialized key filter.
 */
export function matchesKeyFilter(
  event: KeyboardEvent,
  filter: SerializedKeyFilter
): boolean {
  if (event.isComposing) return false;

  // Modifier matching
  if (filter.mod) {
    if (!(IS_MAC ? event.metaKey : event.ctrlKey)) return false;
    // When mod is active, don't also require the platform key to be false
    // (it IS pressed), so skip the explicit ctrl/meta checks for mod bindings.
  } else {
    if (filter.ctrl !== event.ctrlKey) return false;
    if (filter.meta !== event.metaKey) return false;
  }
  if (filter.shift !== event.shiftKey) return false;
  if (filter.alt !== event.altKey) return false;

  return matchesKey(event, filter.key);
}

function matchesKey(event: KeyboardEvent, key: string): boolean {
  // Direct match on event.key (correct on all keyboard layouts)
  if (key.length === 1) {
    if (event.key.toUpperCase() === key.toUpperCase()) return true;
  } else {
    if (event.key === key) return true;
  }

  // Fall back to event.code ONLY when event.key is unreliable:
  // - Dead keys (international compose, event.key === "Dead")
  // - Modifier combos producing wrong characters (Cmd+Option+T → "†")
  // Guard with hasModifier to avoid double-match on non-QWERTY layouts
  const hasModifier = event.ctrlKey || event.metaKey || event.altKey;
  const unreliableKey =
    event.key === "Dead" || (hasModifier && key.length === 1);

  if (unreliableKey) {
    if (event.code?.startsWith("Key")) {
      const codeLetter = event.code.slice(3);
      if (codeLetter.length === 1) {
        return codeLetter.toUpperCase() === key.toUpperCase();
      }
    }
    if (event.code?.startsWith("Digit")) {
      const codeDigit = event.code.slice(5);
      if (codeDigit.length === 1) return codeDigit === key;
    }
  }

  return false;
}

/**
 * Check if the focused element is a text input (where bare keys should be ignored).
 */
export function isTextInput(element: EventTarget | null): boolean {
  if (!(element instanceof HTMLElement)) return false;
  if (
    element.contentEditable === "true" ||
    element.contentEditable === ""
  )
    return true;
  if (element instanceof HTMLTextAreaElement) return true;
  if (element instanceof HTMLSelectElement) return true;
  if (element instanceof HTMLInputElement) {
    return !["button", "submit", "reset"].includes(element.type);
  }
  return false;
}
