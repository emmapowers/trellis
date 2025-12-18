/** Message types for WebSocket communication. */

// Re-export core types for backward compatibility
export { SerializedElement, CallbackRef, isCallbackRef } from "./core";

export const MessageType = {
  HELLO: "hello",
  HELLO_RESPONSE: "hello_response",
  RENDER: "render",
  EVENT: "event",
  ERROR: "error",
} as const;

export interface HelloMessage {
  type: typeof MessageType.HELLO;
  client_id: string;
}

export interface HelloResponseMessage {
  type: typeof MessageType.HELLO_RESPONSE;
  session_id: string;
  server_version: string;
}

export interface RenderMessage {
  type: typeof MessageType.RENDER;
  tree: import("./core").SerializedElement;
}

export interface EventMessage {
  type: typeof MessageType.EVENT;
  callback_id: string;
  args: unknown[];
}

export interface ErrorMessage {
  type: typeof MessageType.ERROR;
  error: string;
  context: "render" | "callback";
}

export type Message =
  | HelloMessage
  | HelloResponseMessage
  | RenderMessage
  | EventMessage
  | ErrorMessage;
