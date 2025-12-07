/** WebSocket client for Trellis server communication. */

import { encode, decode } from "@msgpack/msgpack";
import {
  Message,
  MessageType,
  HelloMessage,
  HelloResponseMessage,
} from "./types";

export type ConnectionState = "disconnected" | "connecting" | "connected";

export interface TrellisClientCallbacks {
  onStateChange?: (state: ConnectionState) => void;
  onConnected?: (response: HelloResponseMessage) => void;
}

export class TrellisClient {
  private ws: WebSocket | null = null;
  private clientId: string;
  private sessionId: string | null = null;
  private state: ConnectionState = "disconnected";
  private callbacks: TrellisClientCallbacks;

  constructor(callbacks: TrellisClientCallbacks = {}) {
    this.clientId = crypto.randomUUID();
    this.callbacks = callbacks;
  }

  private setState(state: ConnectionState): void {
    this.state = state;
    this.callbacks.onStateChange?.(state);
  }

  getState(): ConnectionState {
    return this.state;
  }

  getSessionId(): string | null {
    return this.sessionId;
  }

  async connect(): Promise<HelloResponseMessage> {
    return new Promise((resolve, reject) => {
      this.setState("connecting");

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
        this.handleMessage(msg, resolve);
      };

      this.ws.onerror = () => {
        this.setState("disconnected");
        reject(new Error("WebSocket connection failed"));
      };

      this.ws.onclose = () => {
        this.setState("disconnected");
      };
    });
  }

  private handleMessage(
    msg: Message,
    onFirstResponse: (response: HelloResponseMessage) => void
  ): void {
    switch (msg.type) {
      case MessageType.HELLO_RESPONSE:
        this.sessionId = msg.session_id;
        this.setState("connected");
        console.log(`Connected to Trellis server v${msg.server_version}`);
        this.callbacks.onConnected?.(msg);
        onFirstResponse(msg);
        break;
      // Future: handle tree diffs, etc.
    }
  }

  private send(msg: Message): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(encode(msg));
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.sessionId = null;
    this.setState("disconnected");
  }
}
