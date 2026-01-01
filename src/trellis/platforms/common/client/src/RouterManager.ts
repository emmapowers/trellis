/**
 * Client-side router manager for handling browser history.
 *
 * Manages history based on embedded mode:
 * - Standalone: Uses real browser history API
 * - Embedded: Maintains internal history only (no window.history calls)
 */

import { MessageType, UrlChangedMessage } from "./types";

export interface RouterManagerOptions {
  embedded: boolean;
  sendMessage: (message: UrlChangedMessage) => void;
  initialPath?: string;
}

export class RouterManager {
  private embedded: boolean;
  private sendMessage: (message: UrlChangedMessage) => void;
  private currentPath: string;

  // Internal history for embedded mode
  private history: string[];
  private historyIndex: number;

  // Popstate handler reference for cleanup
  private popstateHandler: ((event: PopStateEvent) => void) | null = null;

  constructor(options: RouterManagerOptions) {
    this.embedded = options.embedded;
    this.sendMessage = options.sendMessage;

    if (this.embedded) {
      // Embedded mode: use provided initial path or default to "/"
      this.currentPath = options.initialPath ?? "/";
    } else {
      // Standalone mode: read from window.location
      this.currentPath = window.location.pathname;
    }

    // Initialize internal history
    this.history = [this.currentPath];
    this.historyIndex = 0;

    // Set up popstate listener for standalone mode
    if (!this.embedded) {
      this.popstateHandler = this.handlePopstate.bind(this);
      window.addEventListener("popstate", this.popstateHandler);
    }
  }

  private handlePopstate(_event: PopStateEvent): void {
    // Read path from location (more reliable than event.state)
    const newPath = window.location.pathname;
    this.currentPath = newPath;

    // Send UrlChanged message to server
    this.sendMessage({
      type: MessageType.URL_CHANGED,
      path: newPath,
    });
  }

  pushState(path: string): void {
    this.currentPath = path;

    if (this.embedded) {
      // Embedded mode: manage internal history only
      // Truncate any forward history
      this.history = this.history.slice(0, this.historyIndex + 1);
      this.history.push(path);
      this.historyIndex = this.history.length - 1;
    } else {
      // Standalone mode: use real browser history
      window.history.pushState({ path }, "", path);
    }
  }

  back(): void {
    if (this.embedded) {
      // Embedded mode: navigate internal history
      if (this.historyIndex > 0) {
        this.historyIndex--;
        this.currentPath = this.history[this.historyIndex];
        this.sendMessage({
          type: MessageType.URL_CHANGED,
          path: this.currentPath,
        });
      }
      // Do nothing if at start of history
    } else {
      // Standalone mode: use real browser history
      window.history.back();
    }
  }

  forward(): void {
    if (this.embedded) {
      // Embedded mode: navigate internal history
      if (this.historyIndex < this.history.length - 1) {
        this.historyIndex++;
        this.currentPath = this.history[this.historyIndex];
        this.sendMessage({
          type: MessageType.URL_CHANGED,
          path: this.currentPath,
        });
      }
      // Do nothing if at end of history
    } else {
      // Standalone mode: use real browser history
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
  }
}
