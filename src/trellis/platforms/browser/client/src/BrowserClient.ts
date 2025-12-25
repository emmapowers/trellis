/**
 * Client for Pyodide-based browser platform.
 *
 * Handles Web Worker transport only. Message processing is delegated
 * to ClientMessageHandler for consistency across platforms.
 *
 * Unlike server/desktop clients, this client doesn't manage the connection
 * lifecycle directly. The PyodideWorker manages the worker, and TrellisApp
 * coordinates the handshake.
 */

import { TrellisClient } from "../../../common/client/src/TrellisClient";
import {
  Message,
  MessageType,
  HelloMessage,
  EventMessage,
} from "../../../common/client/src/types";
import {
  ClientMessageHandler,
  ClientMessageHandlerCallbacks,
  ConnectionState,
} from "../../../common/client/src/ClientMessageHandler";
import { TrellisStore } from "../../../common/client/src/core";

export type { ConnectionState };

export interface BrowserClientCallbacks extends ClientMessageHandlerCallbacks {}

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
  private handler: ClientMessageHandler;
  private sendCallback: SendCallback | null = null;

  /**
   * Create a new browser client.
   *
   * @param callbacks - Optional callbacks for connection events
   * @param store - Optional store instance (defaults to singleton)
   */
  constructor(callbacks: BrowserClientCallbacks = {}, store?: TrellisStore) {
    this.clientId = crypto.randomUUID();
    this.handler = new ClientMessageHandler(callbacks, store);
  }

  getConnectionState(): ConnectionState {
    return this.handler.getConnectionState();
  }

  getSessionId(): string | null {
    return this.handler.getSessionId();
  }

  getServerVersion(): string | null {
    return this.handler.getServerVersion();
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
    this.handler.handleMessage(msg);
  }

  /**
   * Send HelloMessage to Python to initiate the handshake.
   *
   * Should be called after Python has started running (handler.run() is waiting).
   */
  sendHello(): void {
    this.handler.setConnectionState("connecting");
    const hello: HelloMessage = {
      type: MessageType.HELLO,
      client_id: this.clientId,
    };
    this.sendCallback?.(hello);
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
    this.sendCallback = null;
    this.handler.setConnectionState("disconnected");
  }
}
