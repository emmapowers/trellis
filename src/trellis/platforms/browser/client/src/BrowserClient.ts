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

import {
  BaseTrellisClient,
  ConnectionState,
} from "@trellis/trellis-core/client/src/TrellisClient";
import {
  Message,
  MessageType,
  HelloMessage,
  EventMessage,
  UrlChangedMessage,
} from "@trellis/trellis-core/client/src/types";
import { ClientMessageHandlerCallbacks } from "@trellis/trellis-core/client/src/ClientMessageHandler";
import { TrellisStore } from "@trellis/trellis-core/client/src/core";
import { RoutingMode } from "@trellis/trellis-core/client/src/RouterManager";

export type { ConnectionState };

export interface BrowserClientCallbacks extends ClientMessageHandlerCallbacks {}

export interface BrowserClientOptions {
  /**
   * Routing mode for URL handling.
   * - HashUrl (default): Uses hash-based URLs (#/path) for browser platform
   * - Standard: Uses pathname-based URLs (requires server-side routing support)
   * - Embedded: Internal history only, no URL changes
   */
  routingMode?: RoutingMode;
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
export class BrowserClient extends BaseTrellisClient {
  private sendCallback: SendCallback | null = null;

  /**
   * Create a new browser client.
   *
   * @param callbacks - Optional callbacks for connection events
   * @param store - Optional store instance (defaults to singleton)
   * @param options - Optional client options
   */
  constructor(
    callbacks: BrowserClientCallbacks = {},
    store?: TrellisStore,
    options: BrowserClientOptions = {}
  ) {
    super(options.routingMode ?? RoutingMode.HashUrl, callbacks, store);
  }

  protected sendUrlChange(msg: UrlChangedMessage): void {
    this.sendCallback?.(msg);
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
   *
   * @param themeMode - Optional host-controlled theme mode override
   */
  sendHello(themeMode?: "system" | "light" | "dark"): void {
    this.handler.setConnectionState("connecting");
    const systemTheme = window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
    const hello: HelloMessage = {
      type: MessageType.HELLO,
      client_id: this.clientId,
      system_theme: systemTheme,
      theme_mode: themeMode,
      path: this.getCurrentPath(),
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
    this.destroyRouter();
    this.handler.setConnectionState("disconnected");
  }
}
