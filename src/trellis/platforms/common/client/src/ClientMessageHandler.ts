/**
 * Common message handler for all Trellis platform clients.
 *
 * Handles the message protocol (HELLO_RESPONSE, PATCH, ERROR)
 * and updates the shared store. Platform-specific clients delegate
 * message processing to this handler, keeping transport logic separate.
 */

import { encode } from "@msgpack/msgpack";
import {
  Message,
  MessageType,
  HelloResponseMessage,
  Patch,
  ProxyCallMessage,
  ProxyCallResponseMessage,
} from "./types";
import { store as defaultStore, TrellisStore } from "./core";
import { debugLog, setDebugCategories } from "./debug";
import { getProxyTarget } from "./proxyTargets";

export type ConnectionState = "disconnected" | "connecting" | "connected";

export interface ClientMessageHandlerCallbacks {
  onConnectionStateChange?: (state: ConnectionState) => void;
  onConnected?: (response: HelloResponseMessage) => void;
  onError?: (error: string, context: "render" | "callback") => void;
  onHistoryPush?: (path: string) => void;
  onHistoryBack?: () => void;
  onHistoryForward?: () => void;
}

type ProxyResponseSender = (
  msg: ProxyCallResponseMessage
) => void | Promise<void>;

export class ClientMessageHandler {
  private sessionId: string | null = null;
  private serverVersion: string | null = null;
  private connectionState: ConnectionState = "disconnected";
  private callbacks: ClientMessageHandlerCallbacks;
  private store: TrellisStore;
  private sendProxyResponse?: ProxyResponseSender;

  /**
   * Create a new message handler.
   *
   * @param callbacks - Optional callbacks for connection events
   * @param store - Optional store instance (defaults to singleton for backward compatibility)
   */
  constructor(
    callbacks: ClientMessageHandlerCallbacks = {},
    store: TrellisStore = defaultStore,
    sendProxyResponse?: ProxyResponseSender
  ) {
    this.callbacks = callbacks;
    this.store = store;
    this.sendProxyResponse = sendProxyResponse;
  }

  /**
   * Process an incoming message from the server.
   * Updates store and notifies callbacks as appropriate.
   */
  async handleMessage(msg: Message): Promise<void> {
    debugLog("messages", `Received ${msg.type}`);

    switch (msg.type) {
      case MessageType.HELLO_RESPONSE:
        // Set up debug categories before other logging
        if (msg.debug?.categories) {
          setDebugCategories(msg.debug.categories);
        }
        this.sessionId = msg.session_id;
        this.serverVersion = msg.server_version;
        debugLog("messages", `Connected: session=${msg.session_id}, version=${msg.server_version}`);
        this.setConnectionState("connected");
        this.callbacks.onConnected?.(msg);
        break;

      case MessageType.PATCH: {
        const patchCounts = this.countPatches(msg.patches);
        debugLog("messages", `PATCH: ${msg.patches.length} patches (${patchCounts.add} add, ${patchCounts.update} update, ${patchCounts.remove} remove)`);
        this.store.applyPatches(msg.patches);
        break;
      }

      case MessageType.ERROR:
        console.error(`Trellis ${msg.context} error:`, msg.error);
        this.callbacks.onError?.(msg.error, msg.context);
        break;

      case MessageType.HISTORY_PUSH:
        debugLog("messages", `HISTORY_PUSH: ${msg.path}`);
        this.callbacks.onHistoryPush?.(msg.path);
        break;

      case MessageType.HISTORY_BACK:
        debugLog("messages", "HISTORY_BACK");
        this.callbacks.onHistoryBack?.();
        break;

      case MessageType.HISTORY_FORWARD:
        debugLog("messages", "HISTORY_FORWARD");
        this.callbacks.onHistoryForward?.();
        break;

      case MessageType.PROXY_CALL:
        await this.handleProxyCall(msg);
        break;

      case MessageType.RELOAD:
        debugLog("messages", "Reload requested, refreshing page");
        window.location.reload();
        break;
    }
  }

  private async handleProxyCall(msg: ProxyCallMessage): Promise<void> {
    if (!this.sendProxyResponse) {
      return;
    }

    try {
      const target = getProxyTarget(msg.proxy_id);
      if (!target) {
        throw new Error(`Proxy target not found: ${msg.proxy_id}`);
      }

      const method = target[msg.method];
      if (typeof method !== "function") {
        throw new Error(
          `Proxy method not found or not callable: ${msg.proxy_id}.${msg.method}`
        );
      }

      const result = await (method as (...args: unknown[]) => unknown)(...msg.args);
      encode(result);
      await this.sendProxyResponse({
        type: MessageType.PROXY_CALL_RESPONSE,
        request_id: msg.request_id,
        result,
        error: null,
        error_type: null,
      });
    } catch (error) {
      const errorObj = error instanceof Error ? error : new Error(String(error));
      await this.sendProxyResponse({
        type: MessageType.PROXY_CALL_RESPONSE,
        request_id: msg.request_id,
        result: null,
        error: errorObj.message,
        error_type: errorObj.name,
      });
    }
  }

  /** Count patches by type for debug logging. */
  private countPatches(patches: Patch[]): { add: number; update: number; remove: number } {
    let add = 0, update = 0, remove = 0;
    for (const p of patches) {
      if (p.op === "add") add++;
      else if (p.op === "update") update++;
      else if (p.op === "remove") remove++;
    }
    return { add, update, remove };
  }

  /**
   * Set connection state and notify callback.
   */
  setConnectionState(state: ConnectionState): void {
    const oldState = this.connectionState;
    this.connectionState = state;
    debugLog("messages", `Connection: ${oldState} → ${state}`);
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
