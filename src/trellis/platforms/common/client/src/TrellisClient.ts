import {
  ClientMessageHandler,
  ClientMessageHandlerCallbacks,
  ConnectionState,
} from "./ClientMessageHandler";
import { TrellisStore } from "./core";
import { RouterManager, RoutingMode } from "./RouterManager";
import { UrlChangedMessage } from "./types";

export { ConnectionState };

/** Abstract interface for Trellis client implementations.
 *
 * Both WebSocket (server) and Channel (desktop) clients implement this interface.
 * This allows the common TreeRenderer and widgets to work with any transport.
 */
export interface TrellisClient {
  /** Send an event to the backend to invoke a callback. */
  sendEvent(callbackId: string, args: unknown[]): void;
}

/**
 * Base class for Trellis clients with common router management.
 *
 * Provides shared functionality for:
 * - RouterManager creation and callbacks
 * - ClientMessageHandler integration
 * - Connection state management
 *
 * Subclasses implement transport-specific communication and specify
 * their default routing mode.
 */
export abstract class BaseTrellisClient implements TrellisClient {
  protected clientId: string;
  protected handler: ClientMessageHandler;
  protected routerManager: RouterManager;

  /**
   * Create a new client with router management.
   *
   * @param routingMode - The routing mode for this client
   * @param callbacks - Optional callbacks for connection events
   * @param store - Optional store instance (defaults to singleton)
   * @param initialPath - Initial path (for hidden mode)
   */
  constructor(
    routingMode: RoutingMode,
    callbacks: ClientMessageHandlerCallbacks = {},
    store?: TrellisStore,
    initialPath?: string
  ) {
    this.clientId = crypto.randomUUID();

    // Create router manager with configured mode
    this.routerManager = new RouterManager({
      mode: routingMode,
      sendMessage: (msg: UrlChangedMessage) => this.sendUrlChange(msg),
      initialPath,
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

  /** Send a URL change message to the backend. Subclasses implement transport. */
  protected abstract sendUrlChange(msg: UrlChangedMessage): void;

  /** Send an event to invoke a callback. Subclasses implement transport. */
  abstract sendEvent(callbackId: string, args: unknown[]): void;

  getConnectionState(): ConnectionState {
    return this.handler.getConnectionState();
  }

  getSessionId(): string | null {
    return this.handler.getSessionId();
  }

  getServerVersion(): string | null {
    return this.handler.getServerVersion();
  }

  /** Get current path from router manager. */
  getCurrentPath(): string {
    return this.routerManager.getCurrentPath();
  }

  /** Clean up resources. */
  protected destroyRouter(): void {
    this.routerManager.destroy();
  }
}
