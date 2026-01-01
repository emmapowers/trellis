/**
 * Channel-based client for PyTauri desktop communication.
 *
 * Handles PyTauri Channel transport only. Message processing is delegated
 * to ClientMessageHandler for consistency across platforms.
 */

import { Channel } from "@tauri-apps/api/core";
import { pyInvoke } from "tauri-plugin-pytauri-api";
import { encode, decode } from "@msgpack/msgpack";
import {
  Message,
  MessageType,
  HelloMessage,
  HelloResponseMessage,
  EventMessage,
  UrlChangedMessage,
} from "../../../common/client/src/types";
import {
  ClientMessageHandler,
  ClientMessageHandlerCallbacks,
  ConnectionState,
} from "../../../common/client/src/ClientMessageHandler";
import { TrellisClient } from "../../../common/client/src/TrellisClient";
import { TrellisStore } from "../../../common/client/src/core";
import { RouterManager } from "../../../common/client/src/RouterManager";

export type { ConnectionState };

export interface DesktopClientCallbacks extends ClientMessageHandlerCallbacks {}

/**
 * Desktop client using PyTauri channel for bidirectional communication.
 *
 * Uses the same message protocol as WebSocket - constructs identical Message
 * objects (HelloMessage, EventMessage) and receives identical responses
 * (HelloResponseMessage, RenderMessage).
 */
export class DesktopClient implements TrellisClient {
  private channel: Channel<ArrayBuffer> | null = null;
  private clientId: string;
  private handler: ClientMessageHandler;
  private routerManager: RouterManager;
  private connectResolver: ((response: HelloResponseMessage) => void) | null =
    null;

  /**
   * Create a new desktop client.
   *
   * @param callbacks - Optional callbacks for connection events
   * @param store - Optional store instance (defaults to singleton)
   */
  constructor(callbacks: DesktopClientCallbacks = {}, store?: TrellisStore) {
    this.clientId = crypto.randomUUID();

    // Create router manager for embedded mode (desktop has no URL bar)
    this.routerManager = new RouterManager({
      embedded: true,
      sendMessage: (msg: UrlChangedMessage) => this.send(msg),
      initialPath: "/",
    });

    // Merge router callbacks with user callbacks
    const handlerCallbacks: ClientMessageHandlerCallbacks = {
      ...callbacks,
      onHistoryPush: (path: string) => this.routerManager.pushState(path),
      onHistoryBack: () => this.routerManager.back(),
      onHistoryForward: () => this.routerManager.forward(),
    };

    this.handler = new ClientMessageHandler(handlerCallbacks, store);
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

  async connect(): Promise<HelloResponseMessage> {
    return new Promise((resolve, reject) => {
      this.connectResolver = resolve;
      this.handler.setConnectionState("connecting");

      // Create channel for receiving messages from Python
      this.channel = new Channel<ArrayBuffer>();

      // Set up message handler for incoming messages from Python
      this.channel.onmessage = (data: ArrayBuffer) => {
        const msg = decode(new Uint8Array(data)) as Message;
        this.handler.handleMessage(msg);

        // Resolve connect promise on HELLO_RESPONSE
        if (msg.type === MessageType.HELLO_RESPONSE && this.connectResolver) {
          this.connectResolver(msg);
          this.connectResolver = null;
        }
      };

      // Register channel with Python backend
      // Channel serializes to "__CHANNEL__:id" format via toJSON()
      pyInvoke("trellis_connect", {
        channel_id: this.channel,
      })
        .then(() => {
          // Send HelloMessage through the send command
          const systemTheme = window.matchMedia("(prefers-color-scheme: dark)")
            .matches
            ? "dark"
            : "light";
          const hello: HelloMessage = {
            type: MessageType.HELLO,
            client_id: this.clientId,
            system_theme: systemTheme,
            path: this.routerManager.getCurrentPath(),
          };
          this.send(hello);
        })
        .catch((err) => {
          this.handler.setConnectionState("disconnected");
          reject(new Error(`Failed to connect: ${err}`));
        });
    });
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
    this.routerManager.destroy();
    this.handler.setConnectionState("disconnected");
  }
}
