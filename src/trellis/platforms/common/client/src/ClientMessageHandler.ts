/**
 * Common message handler for all Trellis platform clients.
 *
 * Handles the message protocol (HELLO_RESPONSE, RENDER, PATCH, ERROR)
 * and updates the shared store. Platform-specific clients delegate
 * message processing to this handler, keeping transport logic separate.
 */

import { Message, MessageType, HelloResponseMessage } from "./types";
import { store as defaultStore, TrellisStore } from "./core";

export type ConnectionState = "disconnected" | "connecting" | "connected";

export interface ClientMessageHandlerCallbacks {
  onConnectionStateChange?: (state: ConnectionState) => void;
  onConnected?: (response: HelloResponseMessage) => void;
  onError?: (error: string, context: "render" | "callback") => void;
}

export class ClientMessageHandler {
  private sessionId: string | null = null;
  private serverVersion: string | null = null;
  private connectionState: ConnectionState = "disconnected";
  private callbacks: ClientMessageHandlerCallbacks;
  private store: TrellisStore;

  /**
   * Create a new message handler.
   *
   * @param callbacks - Optional callbacks for connection events
   * @param store - Optional store instance (defaults to singleton for backward compatibility)
   */
  constructor(
    callbacks: ClientMessageHandlerCallbacks = {},
    store: TrellisStore = defaultStore
  ) {
    this.callbacks = callbacks;
    this.store = store;
  }

  /**
   * Process an incoming message from the server.
   * Updates store and notifies callbacks as appropriate.
   */
  handleMessage(msg: Message): void {
    switch (msg.type) {
      case MessageType.HELLO_RESPONSE:
        this.sessionId = msg.session_id;
        this.serverVersion = msg.server_version;
        this.setConnectionState("connected");
        this.callbacks.onConnected?.(msg);
        break;

      case MessageType.RENDER:
        this.store.setTree(msg.tree);
        break;

      case MessageType.PATCH:
        this.store.applyPatches(msg.patches);
        break;

      case MessageType.ERROR:
        console.error(`Trellis ${msg.context} error:`, msg.error);
        this.callbacks.onError?.(msg.error, msg.context);
        break;
    }
  }

  /**
   * Set connection state and notify callback.
   */
  setConnectionState(state: ConnectionState): void {
    this.connectionState = state;
    this.callbacks.onConnectionStateChange?.(state);
  }

  getConnectionState(): ConnectionState {
    return this.connectionState;
  }

  getSessionId(): string | null {
    return this.sessionId;
  }

  getServerVersion(): string | null {
    return this.serverVersion;
  }
}
