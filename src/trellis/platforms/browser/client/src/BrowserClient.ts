/**
 * Client for Pyodide-based browser platform.
 *
 * Communicates with Python (BrowserMessageHandler) via Web Worker.
 * Uses the same message protocol as server/desktop platforms.
 */

import { TrellisClient } from "../../../common/client/src/TrellisClient";
import {
  Message,
  MessageType,
  HelloMessage,
  HelloResponseMessage,
  EventMessage,
  SerializedElement,
} from "../../../common/client/src/types";

export type ConnectionState = "disconnected" | "connecting" | "connected";

export interface BrowserClientCallbacks {
  onConnectionStateChange?: (state: ConnectionState) => void;
  onConnected?: (response: HelloResponseMessage) => void;
  onRender?: (tree: SerializedElement) => void;
  onError?: (error: string, context: "render" | "callback") => void;
}

type SendCallback = (msg: Record<string, unknown>) => void;

/**
 * Browser client using Web Worker for communication with Python.
 *
 * Uses the same message protocol as WebSocket (server) and Channel (desktop):
 * - Sends HelloMessage on connect
 * - Receives HelloResponseMessage, RenderMessage, ErrorMessage
 * - Sends EventMessage for user interactions
 */
export class BrowserClient implements TrellisClient {
  private clientId: string;
  private sessionId: string | null = null;
  private connectionState: ConnectionState = "disconnected";
  private callbacks: BrowserClientCallbacks;
  private sendCallback: SendCallback | null = null;

  constructor(callbacks: BrowserClientCallbacks = {}) {
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

  /**
   * Register the callback used to send messages to Python.
   *
   * This should be called with the PyodideWorker's sendMessage method.
   */
  setSendCallback(callback: SendCallback): void {
    this.sendCallback = callback;
  }

  /**
   * Handle a message from Python (called by PyodideWorker.onMessage).
   */
  handleMessage(msg: Message): void {
    this.processMessage(msg);
  }

  /**
   * Send HelloMessage to Python to initiate the handshake.
   *
   * Should be called after Python has started running (handler.run() is waiting).
   */
  sendHello(): void {
    this.setConnectionState("connecting");
    const hello: HelloMessage = {
      type: MessageType.HELLO,
      client_id: this.clientId,
    };
    this.sendCallback?.(hello);
  }

  private processMessage(msg: Message): void {
    switch (msg.type) {
      case MessageType.HELLO_RESPONSE:
        this.sessionId = msg.session_id;
        this.setConnectionState("connected");
        console.log(`Connected to Trellis browser v${msg.server_version}`);
        this.callbacks.onConnected?.(msg);
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

  /** Send an event to invoke a callback in Python. */
  sendEvent(callbackId: string, args: unknown[] = []): void {
    const msg: EventMessage = {
      type: MessageType.EVENT,
      callback_id: callbackId,
      args,
    };
    this.sendCallback?.(msg);
  }

  disconnect(): void {
    this.sessionId = null;
    this.sendCallback = null;
    this.setConnectionState("disconnected");
  }
}
