/**
 * Document-level registry for HotKey() bindings.
 *
 * Single document.addEventListener("keydown"/"keyup") pair.
 * Bindings sorted by tree depth (deepest first) for priority resolution.
 */

import {
  isTextInput,
  matchesKeyFilter,
  type SerializedKeyBinding,
  type SerializedSequenceBinding,
} from "./keyFilters";
import {
  isSequenceBinding,
  matchBindings,
  serializeKeyboardEvent,
  type NormalizedBinding,
} from "./keyBindingMatcher";
import type { KeyState } from "./keyState";

interface RegisteredBinding {
  elementId: string;
  depth: number;
  binding: SerializedKeyBinding | SerializedSequenceBinding;
}

type SendKeyEvent = (
  callbackId: string,
  requestId: string,
  args: unknown[]
) => Promise<boolean>;

export class KeyBindingRegistry {
  private bindings: RegisteredBinding[] = [];
  private keyState: KeyState;
  private sendKeyEvent: SendKeyEvent;
  private keydownListener: ((event: KeyboardEvent) => void) | null = null;
  private keyupListener: ((event: KeyboardEvent) => void) | null = null;

  constructor(keyState: KeyState, sendKeyEvent: SendKeyEvent) {
    this.keyState = keyState;
    this.sendKeyEvent = sendKeyEvent;
  }

  /**
   * Update bindings for an element. Replaces any previous bindings for that element.
   */
  updateElement(elementId: string, rawGlobalKeyFilters: unknown[]): void {
    // Remove existing bindings for this element
    this.bindings = this.bindings.filter((b) => b.elementId !== elementId);

    for (const raw of rawGlobalKeyFilters) {
      const entry = raw as Record<string, unknown>;
      const depth = (entry.depth as number) ?? 0;
      const binding = entry as unknown as
        | SerializedKeyBinding
        | SerializedSequenceBinding;
      this.bindings.push({ elementId, depth, binding });
    }

    // Sort by depth descending (deepest first)
    this.bindings.sort((a, b) => b.depth - a.depth);

    this.ensureListeners();
  }

  /**
   * Remove all bindings for an element.
   */
  removeElement(elementId: string): void {
    this.bindings = this.bindings.filter((b) => b.elementId !== elementId);
    if (this.bindings.length === 0) {
      this.removeListeners();
    }
  }

  private ensureListeners(): void {
    if (this.keydownListener) return;

    this.keydownListener = (event: KeyboardEvent) =>
      this.handleKeyEvent(event, "keydown");
    this.keyupListener = (event: KeyboardEvent) =>
      this.handleKeyEvent(event, "keyup");

    document.addEventListener("keydown", this.keydownListener);
    document.addEventListener("keyup", this.keyupListener);
  }

  private removeListeners(): void {
    if (this.keydownListener) {
      document.removeEventListener("keydown", this.keydownListener);
      this.keydownListener = null;
    }
    if (this.keyupListener) {
      document.removeEventListener("keyup", this.keyupListener);
      this.keyupListener = null;
    }
  }

  private handleKeyEvent(
    event: KeyboardEvent,
    eventType: "keydown" | "keyup"
  ): void {
    if (event.isComposing) return;

    const inTextInput = isTextInput(document.activeElement);
    const normalized: NormalizedBinding[] = this.bindings.map((rb) => {
      const callbackId = rb.binding.handler.__callback__;
      const isSeq = isSequenceBinding(rb.binding);
      return {
        id: isSeq ? `global-seq-${callbackId}` : `global-${callbackId}`,
        callbackId,
        binding: rb.binding,
      };
    });

    const result = matchBindings(normalized, event, eventType, inTextInput, this.keyState);

    if (result.action === "fire") {
      event.preventDefault();
      event.stopPropagation();
      this.fireAndChain(result.callbackId, event, result.bindingIndex);
    } else if (result.action === "suppress") {
      event.preventDefault();
      event.stopPropagation();
    }
  }

  private async fireAndChain(
    callbackId: string,
    event: KeyboardEvent,
    fromIndex: number
  ): Promise<void> {
    const requestId = crypto.randomUUID();
    const handled = await this.sendKeyEvent(callbackId, requestId, [
      serializeKeyboardEvent(event),
    ]);
    if (handled) return;

    // Handler passed — try next matching binding at shallower depth
    const fromDepth = this.bindings[fromIndex]?.depth ?? 0;
    for (let i = fromIndex + 1; i < this.bindings.length; i++) {
      const { binding, depth } = this.bindings[i];
      if (depth >= fromDepth) continue; // Must be shallower

      if (isSequenceBinding(binding)) continue; // Sequences don't chain

      if (binding.event_type !== event.type) continue;
      if (
        binding.ignore_in_inputs &&
        isTextInput(document.activeElement)
      )
        continue;
      if (!matchesKeyFilter(event, binding.filter)) continue;

      const bindingId = `global-${binding.handler.__callback__}`;
      if (!this.keyState.shouldFire(bindingId, binding.require_reset, event)) return;

      await this.fireAndChain(binding.handler.__callback__, event, i);
      return;
    }
  }

  dispose(): void {
    this.removeListeners();
    this.bindings = [];
  }
}
