/** WebSocket client for Trellis server communication. */

import { encode, decode } from "@msgpack/msgpack";
import {
  Message,
  MessageType,
  HelloMessage,
  HelloResponseMessage,
  EventMessage,
  SerializedElement,
} from "./types";

export type ConnectionState = "disconnected" | "connecting" | "connected";

export interface TrellisClientCallbacks {
  onConnectionStateChange?: (state: ConnectionState) => void;
  onConnected?: (response: HelloResponseMessage) => void;
  onRender?: (tree: SerializedElement) => void;
}

export class TrellisClient {
  private ws: WebSocket | null = null;
  private clientId: string;
  private sessionId: string | null = null;
  private connectionState: ConnectionState = "disconnected";
  private callbacks: TrellisClientCallbacks;
  private connectResolver: ((response: HelloResponseMessage) => void) | null =
    null;

  constructor(callbacks: TrellisClientCallbacks = {}) {
    this.clientId = crypto.randomUUID();
    this.callbacks = callbacks;
  }

  private setConnectionState(state: ConnectionState): void {
    this.connectionState = state;
    this.callbacks.onConnectionStateChange?.(state);
  }

  getConnectionState(): ConnectionState {
    return this.connectionState;
  }

  getSessionId(): string | null {
    return this.sessionId;
  }

  async connect(): Promise<HelloResponseMessage> {
    return new Promise((resolve, reject) => {
      this.connectResolver = resolve;
      this.setConnectionState("connecting");

      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      this.ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
      this.ws.binaryType = "arraybuffer";

      this.ws.onopen = () => {
        const hello: HelloMessage = {
          type: MessageType.HELLO,
          client_id: this.clientId,
          protocol_version: 1,
        };
        this.send(hello);
      };

      this.ws.onmessage = (event) => {
        const msg = decode(new Uint8Array(event.data)) as Message;
        this.handleMessage(msg);
      };

      this.ws.onerror = () => {
        this.setConnectionState("disconnected");
        reject(new Error("WebSocket connection failed"));
      };

      this.ws.onclose = () => {
        this.setConnectionState("disconnected");
      };
    });
  }

  private handleMessage(msg: Message): void {
    switch (msg.type) {
      case MessageType.HELLO_RESPONSE:
        this.sessionId = msg.session_id;
        this.setConnectionState("connected");
        console.log(`Connected to Trellis server v${msg.server_version}`);
        this.callbacks.onConnected?.(msg);
        if (this.connectResolver) {
          this.connectResolver(msg);
          this.connectResolver = null;
        }
        break;

      case MessageType.RENDER:
        console.log("Received render message:", msg.tree);
        this.callbacks.onRender?.(msg.tree);
        break;
    }
  }

  private send(msg: Message): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(encode(msg));
    }
  }

  /** Send an event to the server to invoke a callback. */
  sendEvent(callbackId: string, args: unknown[] = []): void {
    const msg: EventMessage = {
      type: MessageType.EVENT,
      callback_id: callbackId,
      args,
    };
    this.send(msg);
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.sessionId = null;
    this.setConnectionState("disconnected");
  }
}
