/**
 * Client-side router manager for handling browser history.
 *
 * Manages history based on routing mode:
 * - Standard: Uses real browser history API with pathname URLs
 * - HashUrl: Uses hash-based URLs (#/path) for platforms without server routing
 * - Embedded: Maintains internal history only (no window.history calls)
 */

import { MessageType, UrlChangedMessage } from "./types";

/** Routing mode for the RouterManager */
export enum RoutingMode {
  /** Uses browser history API with pathname URLs (/path) */
  Standard = "standard",
  /** Uses hash-based URLs (#/path) for platforms without server routing */
  HashUrl = "hash_url",
  /** Internal history only, no browser URL changes (e.g., desktop apps) */
  Embedded = "embedded",
}

export interface RouterManagerOptions {
  mode: RoutingMode;
  sendMessage: (message: UrlChangedMessage) => void;
  initialPath?: string;
}

export class RouterManager {
  private mode: RoutingMode;
  private sendMessage: (message: UrlChangedMessage) => void;
  private currentPath: string;

  // Internal history for embedded mode
  private history: string[];
  private historyIndex: number;

  // Event handler references for cleanup
  private popstateHandler: ((event: PopStateEvent) => void) | null = null;
  private hashchangeHandler: ((event: HashChangeEvent) => void) | null = null;

  constructor(options: RouterManagerOptions) {
    this.mode = options.mode;
    this.sendMessage = options.sendMessage;

    // Determine initial path based on mode
    switch (this.mode) {
      case RoutingMode.Embedded:
        this.currentPath = options.initialPath ?? "/";
        break;
      case RoutingMode.HashUrl:
        this.currentPath = this.getPathFromHash();
        break;
      case RoutingMode.Standard:
        this.currentPath = window.location.pathname;
        break;
    }

    // Initialize internal history
    this.history = [this.currentPath];
    this.historyIndex = 0;

    // Set up event listeners based on mode
    switch (this.mode) {
      case RoutingMode.Standard:
        this.popstateHandler = this.handlePopstate.bind(this);
        window.addEventListener("popstate", this.popstateHandler);
        break;
      case RoutingMode.HashUrl:
        this.hashchangeHandler = this.handleHashchange.bind(this);
        window.addEventListener("hashchange", this.hashchangeHandler);
        break;
      case RoutingMode.Embedded:
        // No browser event listeners in embedded mode
        break;
    }
  }

  /** Extract path from hash, e.g., "#/users/123" -> "/users/123" */
  private getPathFromHash(): string {
    const hash = window.location.hash;
    if (!hash || hash === "#") {
      return "/";
    }
    // Remove the leading "#"
    return hash.slice(1);
  }

  private handlePopstate(_event: PopStateEvent): void {
    const newPath = window.location.pathname;
    this.currentPath = newPath;

    this.sendMessage({
      type: MessageType.URL_CHANGED,
      path: newPath,
    });
  }

  private handleHashchange(_event: HashChangeEvent): void {
    const newPath = this.getPathFromHash();
    this.currentPath = newPath;

    this.sendMessage({
      type: MessageType.URL_CHANGED,
      path: newPath,
    });
  }

  pushState(path: string): void {
    this.currentPath = path;

    switch (this.mode) {
      case RoutingMode.Embedded:
        // Manage internal history only, truncate forward history
        this.history = this.history.slice(0, this.historyIndex + 1);
        this.history.push(path);
        this.historyIndex = this.history.length - 1;
        break;
      case RoutingMode.HashUrl:
        // Update hash (browser handles history automatically)
        window.location.hash = "#" + path;
        break;
      case RoutingMode.Standard:
        window.history.pushState({ path }, "", path);
        break;
    }
  }

  back(): void {
    if (this.mode === RoutingMode.Embedded) {
      // Navigate internal history
      if (this.historyIndex > 0) {
        this.historyIndex--;
        this.currentPath = this.history[this.historyIndex];
        this.sendMessage({
          type: MessageType.URL_CHANGED,
          path: this.currentPath,
        });
      }
    } else {
      // Standard and HashUrl both use browser history
      window.history.back();
    }
  }

  forward(): void {
    if (this.mode === RoutingMode.Embedded) {
      // Navigate internal history
      if (this.historyIndex < this.history.length - 1) {
        this.historyIndex++;
        this.currentPath = this.history[this.historyIndex];
        this.sendMessage({
          type: MessageType.URL_CHANGED,
          path: this.currentPath,
        });
      }
    } else {
      // Standard and HashUrl both use browser history
      window.history.forward();
    }
  }

  getCurrentPath(): string {
    return this.currentPath;
  }

  getHistoryLength(): number {
    return this.history.length;
  }

  destroy(): void {
    if (this.popstateHandler) {
      window.removeEventListener("popstate", this.popstateHandler);
      this.popstateHandler = null;
    }
    if (this.hashchangeHandler) {
      window.removeEventListener("hashchange", this.hashchangeHandler);
      this.hashchangeHandler = null;
    }
  }
}
