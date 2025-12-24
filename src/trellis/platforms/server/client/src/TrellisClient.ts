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
      this.ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
      this.ws.binaryType = "arraybuffer";

      this.ws.onopen = () => {
        const hello: HelloMessage = {
          type: MessageType.HELLO,
          client_id: this.clientId,
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
        this.handler.setConnectionState("disconnected");
        reject(new Error("WebSocket connection failed"));
      };

      this.ws.onclose = () => {
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
    this.handler.setConnectionState("disconnected");
  }
}
