/** Message types for WebSocket communication. */

export const MessageType = {
  HELLO: "hello",
  HELLO_RESPONSE: "hello_response",
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

export type Message = HelloMessage | HelloResponseMessage;
