/**
 * Shared test utilities for Trellis JavaScript tests.
 *
 * Import these helpers to reduce boilerplate in test files:
 *
 *   import { makeElement, makePatch } from "../test-utils";
 */

import { vi, Mock } from "vitest";
import { SerializedElement } from "@common/core/types";
import {
  MessageType,
  HelloResponseMessage,
  PatchMessage,
  ErrorMessage,
  AddPatch,
  UpdatePatch,
  RemovePatch,
} from "@common/types";

// =============================================================================
// Element Factories
// =============================================================================

/**
 * Create a minimal SerializedElement representing a React component for tests.
 *
 * @param key - The unique key for the element
 * @param type - The component type/name
 * @param props - Props to attach to the element; defaults to an empty object
 * @param children - Child SerializedElement nodes; defaults to an empty array
 * @returns A SerializedElement representing a react_component node with the given key, type, props, and children
 */
export function makeElement(
  key: string,
  type: string,
  props: Record<string, unknown> = {},
  children: SerializedElement[] = []
): SerializedElement {
  return {
    kind: "react_component",
    type,
    name: type,
    key,
    props,
    children,
  };
}

// =============================================================================
// Patch Factories
// =============================================================================

/**
 * Create an AddPatch that inserts a subtree rooted at `node` under a parent.
 *
 * @param node - Root element of the subtree to insert
 * @param parentId - ID of the parent node to attach to, or `null` to indicate no parent
 * @param children - Array of child node keys for the parent; defaults to an array containing `node.key`
 * @returns An AddPatch describing the add operation
 */
export function makeAddPatch(
  node: SerializedElement,
  parentId: string | null = null,
  children: string[] = [node.key]
): AddPatch {
  return {
    op: "add",
    parent_id: parentId,
    children,
    node,
  };
}

/**
 * Create an UpdatePatch that replaces the props of the specified node.
 *
 * @param id - The target node's id to update
 * @param props - The props to apply to the node
 * @returns An UpdatePatch object with `op` set to `"update"`, the target `id`, and the provided `props`
 */
export function makeUpdatePatch(
  id: string,
  props: Record<string, unknown>
): UpdatePatch {
  return {
    op: "update",
    id,
    props,
  };
}

/**
 * Create a patch that removes a node from a tree.
 *
 * @param id - The identifier of the node to remove
 * @returns A patch object that describes removing the node with the given `id`
 */
export function makeRemovePatch(id: string): RemovePatch {
  return {
    op: "remove",
    id,
  };
}

// =============================================================================
// Message Factories
// =============================================================================

/**
 * Construct a Hello response message for tests.
 *
 * @param sessionId - Session identifier to include in the message; defaults to `"test-session"`.
 * @param serverVersion - Server version string to include; defaults to `"1.0.0"`.
 * @returns A `HelloResponseMessage` containing `type: MessageType.HELLO_RESPONSE`, `session_id`, and `server_version`.
 */
export function makeHelloResponse(
  sessionId: string = "test-session",
  serverVersion: string = "1.0.0"
): HelloResponseMessage {
  return {
    type: MessageType.HELLO_RESPONSE,
    session_id: sessionId,
    server_version: serverVersion,
  };
}

/**
 * Creates a patch message containing the provided patches.
 *
 * @param patches - The patches to include in the message
 * @returns The PatchMessage with `type` set to MessageType.PATCH and the given `patches`
 */
export function makePatchMessage(
  patches: Array<AddPatch | UpdatePatch | RemovePatch>
): PatchMessage {
  return {
    type: MessageType.PATCH,
    patches,
  };
}

/**
 * Create an error message object for the protocol.
 *
 * @param message - Human-readable error description
 * @param code - Error code identifier (defaults to "ERROR")
 * @returns An ErrorMessage with `type` set to MessageType.ERROR, and the provided `message` and `code`
 */
export function makeErrorMessage(
  message: string,
  code: string = "ERROR"
): ErrorMessage {
  return {
    type: MessageType.ERROR,
    message,
    code,
  };
}

// =============================================================================
// Mock Factories
// =============================================================================

/**
 * Creates a set of vi mock callbacks used by ClientMessageHandler tests.
 *
 * @returns An object containing `onConnectionStateChange`, `onConnected`, and `onError` mock functions.
 */
export function makeHandlerCallbacks(): {
  onConnectionStateChange: Mock;
  onConnected: Mock;
  onError: Mock;
} {
  return {
    onConnectionStateChange: vi.fn(),
    onConnected: vi.fn(),
    onError: vi.fn(),
  };
}

// =============================================================================
// Assertion Helpers
// =============================================================================

/**
 * Collects all node keys from a SerializedElement tree in depth-first order.
 *
 * @returns An array of node keys in depth-first order, starting with the root element's key.
 */
export function getAllKeys(element: SerializedElement): string[] {
  const keys: string[] = [element.key];
  for (const child of element.children ?? []) {
    keys.push(...getAllKeys(child));
  }
  return keys;
}

/**
 * Searches a SerializedElement tree for a node with the given key.
 *
 * @param element - The root element to search
 * @param key - The node key to locate
 * @returns The node with the matching key, or `undefined` if not found
 */
export function findByKey(
  element: SerializedElement,
  key: string
): SerializedElement | undefined {
  if (element.key === key) return element;
  for (const child of element.children ?? []) {
    const found = findByKey(child, key);
    if (found) return found;
  }
  return undefined;
}