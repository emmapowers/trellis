/** Channel-based client for PyTauri desktop communication. */

import { Channel } from "@tauri-apps/api/core";
import { pyInvoke } from "tauri-plugin-pytauri-api";
import { encode, decode } from "@msgpack/msgpack";
import {
  Message,
  MessageType,
  HelloMessage,
  HelloResponseMessage,
  EventMessage,
  SerializedElement,
} from "../../../common/client/src/types";

export type ConnectionState = "disconnected" | "connecting" | "connected";

export interface DesktopClientCallbacks {
  onConnectionStateChange?: (state: ConnectionState) => void;
  onConnected?: (response: HelloResponseMessage) => void;
  onRender?: (tree: SerializedElement) => void;
  onError?: (error: string, context: "render" | "callback") => void;
}

/**
 * Desktop client using PyTauri channel for bidirectional communication.
 *
 * Uses the same message protocol as WebSocket - constructs identical Message
 * objects (HelloMessage, EventMessage) and receives identical responses
 * (HelloResponseMessage, RenderMessage).
 */
export class DesktopClient {
  private channel: Channel<ArrayBuffer> | null = null;
  private clientId: string;
  private sessionId: string | null = null;
  private connectionState: ConnectionState = "disconnected";
  private callbacks: DesktopClientCallbacks;
  private connectResolver: ((response: HelloResponseMessage) => void) | null =
    null;

  constructor(callbacks: DesktopClientCallbacks = {}) {
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

      // Create channel for receiving messages from Python
      this.channel = new Channel<ArrayBuffer>();

      // Set up message handler for incoming messages from Python
      this.channel.onmessage = (data: ArrayBuffer) => {
        const msg = decode(new Uint8Array(data)) as Message;
        this.handleMessage(msg);
      };

      // Register channel with Python backend
      // Channel serializes to "__CHANNEL__:id" format via toJSON()
      pyInvoke("trellis_connect", {
        channel_id: this.channel,
      })
        .then(() => {
          // Send HelloMessage through the send command
          const hello: HelloMessage = {
            type: MessageType.HELLO,
            client_id: this.clientId,
          };
          this.send(hello);
        })
        .catch((err) => {
          this.setConnectionState("disconnected");
          reject(new Error(`Failed to connect: ${err}`));
        });
    });
  }

  private handleMessage(msg: Message): void {
    switch (msg.type) {
      case MessageType.HELLO_RESPONSE:
        this.sessionId = msg.session_id;
        this.setConnectionState("connected");
        console.log(`Connected to Trellis desktop v${msg.server_version}`);
        this.callbacks.onConnected?.(msg);
        if (this.connectResolver) {
          this.connectResolver(msg);
          this.connectResolver = null;
        }
        break;

      case MessageType.RENDER:
        this.callbacks.onRender?.(msg.tree);
        break;

      case MessageType.ERROR:
        console.error(`Trellis ${msg.context} error:`, msg.error);
        this.callbacks.onError?.(msg.error, msg.context);
        break;
    }
  }

  private send(msg: Message): void {
    // Send msgpack-encoded message through the send command
    const encoded = encode(msg);
    pyInvoke("trellis_send", {
      data: Array.from(encoded),
    }).catch((err) => {
      console.error("Failed to send message:", err);
    });
  }

  /** Send an event to the backend to invoke a callback. */
  sendEvent(callbackId: string, args: unknown[] = []): void {
    const msg: EventMessage = {
      type: MessageType.EVENT,
      callback_id: callbackId,
      args,
    };
    this.send(msg);
  }

  disconnect(): void {
    this.channel = null;
    this.sessionId = null;
    this.setConnectionState("disconnected");
  }
}
