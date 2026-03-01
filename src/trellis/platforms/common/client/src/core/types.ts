/** Core types for Trellis tree rendering. */

/** Element kind enum - matches Python ElementKind in base.py. */
export enum ElementKind {
  REACT_COMPONENT = "react_component",
  JSX_ELEMENT = "jsx_element",
  TEXT = "text",
}

/** Serialized element tree node. */
export interface SerializedElement {
  kind: ElementKind;
  type: string;
  name: string;
  key: string | null;
  props: Record<string, unknown>;
  children: SerializedElement[];
}

/** Callback reference in props. */
export interface CallbackRef {
  __callback__: string;
}

export function isCallbackRef(value: unknown): value is CallbackRef {
  return (
    typeof value === "object" &&
    value !== null &&
    "__callback__" in value &&
    typeof (value as CallbackRef).__callback__ === "string"
  );
}

/** Mutable binding reference in props - for two-way data binding. */
export interface MutableRef {
  __mutable__: string;
  value: unknown;
  version?: number;
}

export function isMutableRef(value: unknown): value is MutableRef {
  return (
    typeof value === "object" &&
    value !== null &&
    "__mutable__" in value &&
    typeof (value as MutableRef).__mutable__ === "string" &&
    "value" in value
  );
}

/** Event handler function type - called when a callback is triggered. */
export type EventHandler = (callbackId: string, args: unknown[]) => void;

/** Optimistic state for a single mutable binding. */
interface MutableState {
  localVersion: number;
  optimisticValue: unknown;
  hasOptimistic: boolean;
}

/** Module-level registry of optimistic mutable state, keyed by mutable ID. */
const mutableStates = new Map<string, MutableState>();

/** Reset all optimistic mutable state (called on full tree reset). */
export function resetMutableStates(): void {
  mutableStates.clear();
}

/**
 * Client-side Mutable wrapper for two-way data binding with optimistic updates.
 *
 * Tracks a local version counter so the client can apply optimistic updates
 * immediately. Server values are only accepted when their version matches or
 * exceeds the local version, preventing stale server responses from overwriting
 * in-flight user input.
 */
export class Mutable<T> {
  private readonly _ref: MutableRef;
  private readonly _onEvent: EventHandler;
  private readonly _state: MutableState;

  constructor(ref: MutableRef, onEvent: EventHandler) {
    this._ref = ref;
    this._onEvent = onEvent;

    const id = ref.__mutable__;
    let state = mutableStates.get(id);
    if (!state) {
      state = { localVersion: 0, optimisticValue: undefined, hasOptimistic: false };
      mutableStates.set(id, state);
    }
    this._state = state;

    // Server acknowledged our version — clear optimistic state and sync
    // localVersion so subsequent setValue calls start above the server's
    // version (prevents stale renders from passing the >= check).
    const serverVersion = ref.version ?? 0;
    if (serverVersion >= state.localVersion) {
      state.hasOptimistic = false;
      state.localVersion = serverVersion;
    }
  }

  /** Get the current value, preferring optimistic value over server value. */
  get value(): T {
    if (this._state.hasOptimistic) {
      return this._state.optimisticValue as T;
    }
    return this._ref.value as T;
  }

  /** Set a new value optimistically and send the update to the server. */
  setValue(newValue: T): void {
    this._state.localVersion++;
    this._state.optimisticValue = newValue;
    this._state.hasOptimistic = true;
    this._onEvent(this._ref.__mutable__, [newValue, this._state.localVersion]);
  }
}

/** Check if a value is a Mutable wrapper. */
export function isMutable<T>(value: unknown): value is Mutable<T> {
  return value instanceof Mutable;
}

/**
 * Unwrap a value that may be a Mutable or plain value.
 * Returns the underlying value and an optional setValue function.
 */
export function unwrapMutable<T>(
  value: T | Mutable<T>
): { value: T; setValue?: (v: T) => void } {
  if (isMutable<T>(value)) {
    return { value: value.value, setValue: (v: T) => value.setValue(v) };
  }
  return { value };
}
