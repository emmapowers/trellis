/** Message types for WebSocket communication. */

export const MessageType = {
  HELLO: "hello",
  HELLO_RESPONSE: "hello_response",
  RENDER: "render",
  EVENT: "event",
} as const;

export interface HelloMessage {
  type: typeof MessageType.HELLO;
  client_id: string;
  protocol_version: number;
}

export interface HelloResponseMessage {
  type: typeof MessageType.HELLO_RESPONSE;
  session_id: string;
  server_version: string;
}

/** Serialized element tree node from the server. */
export interface SerializedElement {
  type: string;
  name: string; // Python component name for debugging
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

export interface RenderMessage {
  type: typeof MessageType.RENDER;
  tree: SerializedElement;
}

export interface EventMessage {
  type: typeof MessageType.EVENT;
  callback_id: string;
  args: unknown[];
}

export type Message =
  | HelloMessage
  | HelloResponseMessage
  | RenderMessage
  | EventMessage;
