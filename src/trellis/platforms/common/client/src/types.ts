/** Message types for WebSocket communication. */

// Re-export core types for backward compatibility
export type { SerializedElement, CallbackRef } from "./core";
export { isCallbackRef } from "./core";

export const MessageType = {
  HELLO: "hello",
  HELLO_RESPONSE: "hello_response",
  PATCH: "patch",
  EVENT: "event",
  ERROR: "error",
  HISTORY_PUSH: "history_push",
  HISTORY_BACK: "history_back",
  HISTORY_FORWARD: "history_forward",
  URL_CHANGED: "url_changed",
  RELOAD: "reload",
} as const;

// ============================================================================
// Patch types for incremental updates
// ============================================================================

/** Add a new node to the tree. */
export interface AddPatch {
  op: "add";
  parent_id: string | null;
  children: string[]; // Parent's new children list (for positioning)
  element: import("./core").SerializedElement; // Full subtree for the new node
}

/** Update an existing node's props and/or children order. */
export interface UpdatePatch {
  op: "update";
  id: string;
  props?: Record<string, unknown>; // Changed props only (omit if unchanged)
  children?: string[]; // New children order (omit if unchanged)
}

/** Remove a node from the tree. */
export interface RemovePatch {
  op: "remove";
  id: string;
}

/** Union of all patch types. */
export type Patch = AddPatch | UpdatePatch | RemovePatch;

export interface HelloMessage {
  type: typeof MessageType.HELLO;
  client_id: string;
  system_theme: "light" | "dark"; // Detected from OS preference
  theme_mode?: "system" | "light" | "dark"; // Host-controlled theme mode override
  path?: string;
}

/** Debug configuration from the server. */
export interface DebugConfig {
  categories: string[];
}

export interface HelloResponseMessage {
  type: typeof MessageType.HELLO_RESPONSE;
  session_id: string;
  server_version: string;
  debug?: DebugConfig;
}

export interface EventMessage {
  type: typeof MessageType.EVENT;
  callback_id: string;
  args: unknown[];
}

export interface ErrorMessage {
  type: typeof MessageType.ERROR;
  error: string;
  context: "render" | "callback";
}

/** Incremental update message with patches. */
export interface PatchMessage {
  type: typeof MessageType.PATCH;
  patches: Patch[];
}

// ============================================================================
// Router messages for client-side navigation
// ============================================================================

/** Push a new path to browser history. Sent from server to client. */
export interface HistoryPushMessage {
  type: typeof MessageType.HISTORY_PUSH;
  path: string;
}

/** Navigate back in browser history. Sent from server to client. */
export interface HistoryBackMessage {
  type: typeof MessageType.HISTORY_BACK;
}

/** Navigate forward in browser history. Sent from server to client. */
export interface HistoryForwardMessage {
  type: typeof MessageType.HISTORY_FORWARD;
}

/** URL changed in browser (e.g., popstate). Sent from client to server. */
export interface UrlChangedMessage {
  type: typeof MessageType.URL_CHANGED;
  path: string;
}

/** Reload message sent when bundle is rebuilt. */
export interface ReloadMessage {
  type: typeof MessageType.RELOAD;
}

export type Message =
  | HelloMessage
  | HelloResponseMessage
  | PatchMessage
  | EventMessage
  | ErrorMessage
  | HistoryPushMessage
  | HistoryBackMessage
  | HistoryForwardMessage
  | UrlChangedMessage
  | ReloadMessage;
