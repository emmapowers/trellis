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
  ProxyRequestMessage,
  ProxyResponseMessage,
} from "./types";
import { store as defaultStore, TrellisStore } from "./core";
import { debugLog, setDebugCategories } from "./debug";
import { resolveProxyTarget } from "./proxyTargets";

export type ConnectionState = "disconnected" | "connecting" | "connected";

export interface ClientMessageHandlerCallbacks {
  onConnectionStateChange?: (state: ConnectionState) => void;
  onConnected?: (response: HelloResponseMessage) => void;
  onError?: (error: string, context: "render" | "callback") => void;
  onHistoryPush?: (path: string) => void;
  onHistoryBack?: () => void;
  onHistoryForward?: () => void;
}

type MessageSender = (msg: Message) => void | Promise<void>;

function normalizeProxyError(error: unknown): { message: string; name: string } {
  if (error instanceof Error) {
    return {
      message: error.message,
      name: error.name,
    };
  }

  if (error && typeof error === "object") {
    const record = error as Record<string, unknown>;
    return {
      message:
        typeof record.message === "string" ? record.message : String(error),
      name: typeof record.name === "string" ? record.name : "Error",
    };
  }

  return {
    message: String(error),
    name: "Error",
  };
}

export class ClientMessageHandler {
  private sessionId: string | null = null;
  private serverVersion: string | null = null;
  private connectionState: ConnectionState = "disconnected";
  private callbacks: ClientMessageHandlerCallbacks;
  private store: TrellisStore;
  private sendMessageCallback?: MessageSender;

  /**
   * Create a new message handler.
   *
   * @param callbacks - Optional callbacks for connection events
   * @param store - Optional store instance (defaults to singleton for backward compatibility)
   */
  constructor(
    callbacks: ClientMessageHandlerCallbacks = {},
    store: TrellisStore = defaultStore,
    sendMessage?: MessageSender
  ) {
    this.callbacks = callbacks;
    this.store = store;
    this.sendMessageCallback = sendMessage;
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

      case MessageType.PROXY_REQUEST:
        await this.handleProxyRequest(msg);
        break;

      case MessageType.PROXY_RESPONSE:
        break;

      case MessageType.RELOAD:
        debugLog("messages", "Reload requested, refreshing page");
        window.location.reload();
        break;
    }
  }

  private async handleProxyRequest(msg: ProxyRequestMessage): Promise<void> {
    if (!this.sendMessageCallback) {
      return;
    }

    try {
      const resolved = resolveProxyTarget(msg.proxy_id);
      if (!resolved.found) {
        if (resolved.isGlobal) {
          throw new Error(`Global target not found: ${resolved.path}`);
        }
        throw new Error(`Proxy target not found: ${msg.proxy_id}`);
      }

      let result: unknown;

      switch (msg.operation) {
        case "call":
          result = await this.dispatchCall(msg, resolved);
          break;
        case "get":
          result = this.dispatchGet(msg, resolved);
          break;
        case "set":
          result = this.dispatchSet(msg, resolved);
          break;
        case "delete":
          result = this.dispatchDelete(msg, resolved);
          break;
      }

      if (result === undefined) {
        result = null;
      }
      encode(result);
      await this.sendMessageCallback({
        type: MessageType.PROXY_RESPONSE,
        request_id: msg.request_id,
        result,
        error: null,
        error_type: null,
      });
    } catch (error) {
      const errorObj = normalizeProxyError(error);
      await this.sendMessageCallback({
        type: MessageType.PROXY_RESPONSE,
        request_id: msg.request_id,
        result: null,
        error: errorObj.message,
        error_type: errorObj.name,
      });
    }
  }

  private dispatchCall(
    msg: ProxyRequestMessage,
    resolved: ReturnType<typeof resolveProxyTarget>
  ): unknown {
    if (msg.member === null) {
      if (typeof resolved.target !== "function") {
        if (resolved.isGlobal) {
          throw new Error(`Global target is not callable: ${resolved.path}`);
        }
        throw new Error(`Proxy target is not callable: ${msg.proxy_id}`);
      }
      return Reflect.apply(resolved.target, resolved.receiver, msg.args);
    }

    const objectTarget = this.requireObjectTarget(msg, resolved);
    const method = objectTarget[msg.member];
    if (typeof method !== "function") {
      if (resolved.isGlobal) {
        throw new Error(`Global method not found or not callable: ${resolved.path}.${msg.member}`);
      }
      throw new Error(`Proxy method not found or not callable: ${msg.proxy_id}.${msg.member}`);
    }

    return Reflect.apply(method, resolved.target, msg.args);
  }

  private dispatchGet(
    msg: ProxyRequestMessage,
    resolved: ReturnType<typeof resolveProxyTarget>
  ): unknown {
    const objectTarget = this.requireObjectTarget(msg, resolved);
    return Reflect.get(objectTarget, this.requireMember(msg), resolved.target);
  }

  private dispatchSet(
    msg: ProxyRequestMessage,
    resolved: ReturnType<typeof resolveProxyTarget>
  ): boolean {
    const objectTarget = this.requireObjectTarget(msg, resolved);
    return Reflect.set(objectTarget, this.requireMember(msg), msg.value, resolved.target);
  }

  private dispatchDelete(
    msg: ProxyRequestMessage,
    resolved: ReturnType<typeof resolveProxyTarget>
  ): boolean {
    const objectTarget = this.requireObjectTarget(msg, resolved);
    return Reflect.deleteProperty(objectTarget, this.requireMember(msg));
  }

  private requireMember(msg: ProxyRequestMessage): string {
    if (msg.member === null) {
      throw new Error(`Proxy member is required for ${msg.operation}: ${msg.proxy_id}`);
    }
    return msg.member;
  }

  private requireObjectTarget(
    msg: ProxyRequestMessage,
    resolved: ReturnType<typeof resolveProxyTarget>
  ): Record<string, unknown> {
    if (
      resolved.target === null ||
      resolved.target === undefined ||
      (typeof resolved.target !== "object" && typeof resolved.target !== "function")
    ) {
      if (resolved.isGlobal) {
        throw new Error(`Global target not found: ${resolved.path}`);
      }
      throw new Error(`Proxy target not found: ${msg.proxy_id}`);
    }
    return resolved.target as Record<string, unknown>;
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
