/**
 * WebSocket client for Trellis server communication.
 *
 * Handles WebSocket transport only. Message processing is delegated
 * to ClientMessageHandler for consistency across platforms.
 */

import { encode, decode } from "@msgpack/msgpack";
import {
  Message,
  MessageType,
  HelloMessage,
  HelloResponseMessage,
  EventMessage,
} from "../../../common/client/src/types";
import {
  ClientMessageHandler,
  ClientMessageHandlerCallbacks,
  ConnectionState,
} from "../../../common/client/src/ClientMessageHandler";
import { TrellisClient } from "../../../common/client/src/TrellisClient";
import { TrellisStore } from "../../../common/client/src/core";
import { debugLog } from "../../../common/client/src/debug";

export type { ConnectionState };

export interface TrellisClientCallbacks extends ClientMessageHandlerCallbacks {}

export class ServerTrellisClient implements TrellisClient {
  private ws: WebSocket | null = null;
  private clientId: string;
  private handler: ClientMessageHandler;
  private connectResolver: ((response: HelloResponseMessage) => void) | null =
    null;

  /**
   * Create a new server client.
   *
   * @param callbacks - Optional callbacks for connection events
   * @param store - Optional store instance (defaults to singleton)
   */
  constructor(callbacks: TrellisClientCallbacks = {}, store?: TrellisStore) {
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

  async connect(): Promise<HelloResponseMessage> {
    return new Promise((resolve, reject) => {
      this.connectResolver = resolve;
      this.handler.setConnectionState("connecting");

      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsUrl = `${protocol}//${window.location.host}/ws`;
      debugLog("client", `Connecting to ${wsUrl}`);
      this.ws = new WebSocket(wsUrl);
      this.ws.binaryType = "arraybuffer";

      this.ws.onopen = () => {
        debugLog("client", "WebSocket opened, sending HELLO");
        const systemTheme = window.matchMedia("(prefers-color-scheme: dark)")
          .matches
          ? "dark"
          : "light";
        const hello: HelloMessage = {
          type: MessageType.HELLO,
          client_id: this.clientId,
          system_theme: systemTheme,
        };
        this.send(hello);
      };

      this.ws.onmessage = (event) => {
        const msg = decode(new Uint8Array(event.data)) as Message;
        this.handler.handleMessage(msg);

        // Resolve connect promise on HELLO_RESPONSE
        if (msg.type === MessageType.HELLO_RESPONSE && this.connectResolver) {
          this.connectResolver(msg);
          this.connectResolver = null;
        }
      };

      this.ws.onerror = () => {
        debugLog("client", "WebSocket error");
        this.handler.setConnectionState("disconnected");
        reject(new Error("WebSocket connection failed"));
      };

      this.ws.onclose = () => {
        debugLog("client", "WebSocket closed");
        this.handler.setConnectionState("disconnected");
      };
    });
  }

  private send(msg: Message): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(encode(msg));
    }
  }

  /** Send an event to the server to invoke a callback. */
  sendEvent(callbackId: string, args: unknown[] = []): void {
    debugLog("client", `sendEvent: ${callbackId} args=${JSON.stringify(args)}`);
    const msg: EventMessage = {
      type: MessageType.EVENT,
      callback_id: callbackId,
      args,
    };
    this.send(msg);
  }

  disconnect(): void {
    debugLog("client", "Disconnecting");
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.handler.setConnectionState("disconnected");
  }
}
