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
 * Create a minimal SerializedElement for testing.
 *
 * @example
 * const button = makeElement("btn-1", "Button", { text: "Click" });
 * const app = makeElement("root", "App", {}, [
 *   makeElement("header", "Header"),
 *   makeElement("content", "Content"),
 * ]);
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
 * Create an AddPatch for inserting a new subtree.
 */
export function makeAddPatch(
  element: SerializedElement,
  parentId: string | null = null,
  children: string[] = [element.key]
): AddPatch {
  return {
    op: "add",
    parent_id: parentId,
    children,
    element,
  };
}

/**
 * Create an UpdatePatch for modifying props.
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
 * Create a RemovePatch for deleting a node.
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
 * Create a HelloResponseMessage.
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
 * Create a PatchMessage with the given patches.
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
 * Create an ErrorMessage.
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
 * Create a mock callback set for ClientMessageHandler tests.
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
 * Extract all node keys from a SerializedElement tree (depth-first).
 */
export function getAllKeys(element: SerializedElement): string[] {
  const keys: string[] = [element.key];
  for (const child of element.children ?? []) {
    keys.push(...getAllKeys(child));
  }
  return keys;
}

/**
 * Find a node in a SerializedElement tree by key.
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
