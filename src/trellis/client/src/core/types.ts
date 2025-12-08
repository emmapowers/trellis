/** Core types for Trellis tree rendering. */

/** Serialized element tree node. */
export interface SerializedElement {
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

/** Event handler function type - called when a callback is triggered. */
export type EventHandler = (callbackId: string) => void;
