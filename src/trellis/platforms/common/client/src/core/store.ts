/**
 * ID-keyed state store for Trellis nodes.
 *
 * This store holds node data indexed by ID, enabling efficient incremental
 * updates via patches. Components subscribe to specific node IDs and only
 * re-render when their data changes.
 */

import { useCallback, useSyncExternalStore } from "react";
import { SerializedElement } from "./types";
import {
  Patch,
  AddPatch,
  UpdatePatch,
  RemovePatch,
} from "../types";
import { debugLog } from "../debug";

/** Node data stored by ID. */
export interface NodeData {
  kind: string;
  type: string;
  name: string;
  props: Record<string, unknown>;
  childIds: string[];
}

/**
 * Central store for all node data.
 *
 * Provides:
 * - Full tree initialization via setTree()
 * - Incremental updates via applyPatches()
 * - Per-node subscriptions for efficient React re-renders
 */
export class TrellisStore {
  private nodes: Map<string, NodeData> = new Map();
  private nodeListeners: Map<string, Set<() => void>> = new Map();
  private globalListeners: Set<() => void> = new Set();
  private rootId: string | null = null;

  /** Get a node by ID. */
  getNode(id: string): NodeData | undefined {
    return this.nodes.get(id);
  }

  /** Get the root node ID. */
  getRootId(): string | null {
    return this.rootId;
  }

  /**
   * Set the full tree (initial render or resync).
   * Clears existing data and populates from the serialized tree.
   */
  setTree(root: SerializedElement): void {
    this.nodes.clear();
    this.rootId = root.key ?? root.name ?? `unknown-${Math.random().toString(36).slice(2)}`;
    this.addNodeRecursive(root);
    debugLog("store", `setTree: root=${this.rootId}, ${this.nodes.size} total nodes`);
    this.notifyGlobal();
  }

  private addNodeRecursive(node: SerializedElement): void {
    // key should always be present from server, but fall back to name if missing
    const id = node.key ?? node.name ?? `unknown-${Math.random().toString(36).slice(2)}`;
    this.nodes.set(id, {
      kind: node.kind,
      type: node.type,
      name: node.name,
      props: node.props,
      childIds: node.children.map((c) => c.key ?? c.name ?? `unknown-${Math.random().toString(36).slice(2)}`),
    });
    for (const child of node.children) {
      this.addNodeRecursive(child);
    }
  }

  /**
   * Apply patches from the server.
   * Updates only affected nodes and notifies their listeners.
   */
  applyPatches(patches: Patch[]): void {
    debugLog("store", `Applying ${patches.length} patches`);
    const affectedIds = new Set<string>();

    for (const patch of patches) {
      switch (patch.op) {
        case "add":
          this.applyAdd(patch, affectedIds);
          break;
        case "update":
          this.applyUpdate(patch, affectedIds);
          break;
        case "remove":
          this.applyRemove(patch, affectedIds);
          break;
      }
    }

    // Notify affected nodes
    for (const id of affectedIds) {
      this.notifyNode(id);
    }

    // Also notify global listeners if anything changed
    if (affectedIds.size > 0) {
      this.notifyGlobal();
    }
  }

  private applyAdd(patch: AddPatch, affectedIds: Set<string>): void {
    const nodeId = patch.node.key ?? patch.node.name ?? `unknown-${Math.random().toString(36).slice(2)}`;
    debugLog("store", `ADD: ${nodeId} under parent ${patch.parent_id}`);

    // Add the new node and all descendants
    this.addNodeRecursive(patch.node);
    affectedIds.add(nodeId);

    // Update parent's childIds if parent exists
    if (patch.parent_id) {
      const parent = this.nodes.get(patch.parent_id);
      if (!parent) {
        console.warn(`[TrellisStore] Cannot add node ${nodeId} - parent ${patch.parent_id} not found`);
        return;
      }
      parent.childIds = patch.children;
      affectedIds.add(patch.parent_id);
    } else {
      // Adding a new root (shouldn't happen normally, but handle it)
      this.rootId = nodeId;
    }
  }

  private applyUpdate(patch: UpdatePatch, affectedIds: Set<string>): void {
    const node = this.nodes.get(patch.id);
    if (!node) {
      console.warn(`[TrellisStore] Update for unknown node: ${patch.id}`);
      return;
    }

    const propsChanged = patch.props ? Object.keys(patch.props) : [];
    const childrenChanged = patch.children !== undefined;
    debugLog("store", `UPDATE: ${patch.id} props=[${propsChanged.join(",")}] children=${childrenChanged}`);

    // Create new props object with updates applied
    let newProps = node.props;
    if (patch.props) {
      newProps = { ...node.props };
      for (const [key, value] of Object.entries(patch.props)) {
        if (value === null) {
          delete newProps[key];
        } else {
          newProps[key] = value;
        }
      }
    }

    // Create new childIds array if changed
    const newChildIds = patch.children ?? node.childIds;

    // Create new NodeData object (immutable update for React)
    const newNode: NodeData = {
      kind: node.kind,
      type: node.type,
      name: node.name,
      props: newProps,
      childIds: newChildIds,
    };

    this.nodes.set(patch.id, newNode);
    affectedIds.add(patch.id);
  }

  private applyRemove(patch: RemovePatch, affectedIds: Set<string>): void {
    debugLog("store", `REMOVE: ${patch.id}`);
    // Remove node and all descendants
    this.removeNodeRecursive(patch.id);
    affectedIds.add(patch.id);
  }

  private removeNodeRecursive(id: string): void {
    const node = this.nodes.get(id);
    if (!node) return;

    // Remove children first
    for (const childId of node.childIds) {
      this.removeNodeRecursive(childId);
    }

    // Remove this node
    this.nodes.delete(id);
    this.nodeListeners.delete(id);
  }

  // ===========================================================================
  // Subscription API
  // ===========================================================================

  /** Subscribe to changes for a specific node. */
  subscribeToNode(id: string, listener: () => void): () => void {
    if (!this.nodeListeners.has(id)) {
      this.nodeListeners.set(id, new Set());
    }
    this.nodeListeners.get(id)!.add(listener);
    return () => this.nodeListeners.get(id)?.delete(listener);
  }

  /** Subscribe to any store changes (for root ID tracking). */
  subscribeGlobal(listener: () => void): () => void {
    this.globalListeners.add(listener);
    return () => this.globalListeners.delete(listener);
  }

  private notifyNode(id: string): void {
    const listeners = this.nodeListeners.get(id);
    if (listeners && listeners.size > 0) {
      debugLog("store", `Notifying ${listeners.size} listeners for node ${id}`);
      for (const listener of listeners) {
        listener();
      }
    }
  }

  private notifyGlobal(): void {
    if (this.globalListeners.size > 0) {
      debugLog("store", `Notifying ${this.globalListeners.size} global listeners`);
    }
    for (const listener of this.globalListeners) {
      listener();
    }
  }
}

// Singleton store instance
export const store = new TrellisStore();

// ===========================================================================
// React Hooks
// ===========================================================================

/**
 * Hook to subscribe to a specific node's data.
 * Re-renders only when that node's data changes.
 */
export function useNode(id: string): NodeData | undefined {
  const subscribe = useCallback(
    (onStoreChange: () => void) => store.subscribeToNode(id, onStoreChange),
    [id]
  );
  const getSnapshot = useCallback(() => store.getNode(id), [id]);

  return useSyncExternalStore(subscribe, getSnapshot);
}

/**
 * Hook to get the root node ID.
 * Re-renders when root changes (initial render or full tree reset).
 */
export function useRootId(): string | null {
  const subscribe = useCallback(
    (onStoreChange: () => void) => store.subscribeGlobal(onStoreChange),
    []
  );
  const getSnapshot = useCallback(() => store.getRootId(), []);

  return useSyncExternalStore(subscribe, getSnapshot);
}
