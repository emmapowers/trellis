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

/**
 * Client-side Mutable wrapper for two-way data binding.
 *
 * Components that support mutable bindings can check if a prop is a Mutable
 * and use `.value` to read and `.setValue()` to write.
 */
export class Mutable<T> {
  private readonly _ref: MutableRef;
  private readonly _onEvent: EventHandler;

  constructor(ref: MutableRef, onEvent: EventHandler) {
    this._ref = ref;
    this._onEvent = onEvent;
  }

  /** Get the current value. */
  get value(): T {
    return this._ref.value as T;
  }

  /** Set a new value, sending the update to the server. */
  setValue(newValue: T): void {
    this._onEvent(this._ref.__mutable__, [newValue]);
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
