import { describe, it, expect, beforeEach, vi } from "vitest";
import { TrellisStore, NodeData } from "@common/core/store";
import { SerializedElement } from "@common/core/types";
import { AddPatch, UpdatePatch, RemovePatch } from "@common/types";

describe("TrellisStore", () => {
  let store: TrellisStore;

  beforeEach(() => {
    store = new TrellisStore();
  });

  // Helper to create a minimal serialized element
  function makeElement(
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

  describe("setTree", () => {
    it("sets root ID from tree", () => {
      const tree = makeElement("root", "App");
      store.setTree(tree);
      expect(store.getRootId()).toBe("root");
    });

    it("populates node data for single node", () => {
      const tree = makeElement("e1", "Button", { text: "Click me" });
      store.setTree(tree);

      const node = store.getNode("e1");
      expect(node).toBeDefined();
      expect(node?.type).toBe("Button");
      expect(node?.props).toEqual({ text: "Click me" });
      expect(node?.childIds).toEqual([]);
    });

    it("populates node data recursively", () => {
      const tree = makeElement("root", "App", {}, [
        makeElement("e1", "Header", { title: "Hello" }),
        makeElement("e2", "Content", {}, [
          makeElement("e3", "Button", { text: "OK" }),
        ]),
      ]);
      store.setTree(tree);

      expect(store.getNode("root")).toBeDefined();
      expect(store.getNode("e1")?.props).toEqual({ title: "Hello" });
      expect(store.getNode("e2")?.childIds).toEqual(["e3"]);
      expect(store.getNode("e3")?.type).toBe("Button");
    });

    it("clears previous data on new tree", () => {
      store.setTree(makeElement("old", "OldApp"));
      expect(store.getNode("old")).toBeDefined();

      store.setTree(makeElement("new", "NewApp"));
      expect(store.getNode("old")).toBeUndefined();
      expect(store.getNode("new")).toBeDefined();
      expect(store.getRootId()).toBe("new");
    });
  });

  describe("applyPatches - update", () => {
    beforeEach(() => {
      store.setTree(
        makeElement("root", "App", {}, [
          makeElement("e1", "Label", { text: "Hello", color: "red" }),
        ])
      );
    });

    it("updates props on existing node", () => {
      const patch: UpdatePatch = {
        op: "update",
        id: "e1",
        props: { text: "World" },
      };
      store.applyPatches([patch]);

      const node = store.getNode("e1");
      expect(node?.props.text).toBe("World");
      expect(node?.props.color).toBe("red"); // unchanged
    });

    it("removes props when set to null", () => {
      const patch: UpdatePatch = {
        op: "update",
        id: "e1",
        props: { color: null },
      };
      store.applyPatches([patch]);

      const node = store.getNode("e1");
      expect(node?.props.color).toBeUndefined();
      expect(node?.props.text).toBe("Hello");
    });

    it("updates childIds when provided", () => {
      // First add more children
      store.setTree(
        makeElement("root", "App", {}, [
          makeElement("e1", "Container", {}, [
            makeElement("e2", "Child1"),
            makeElement("e3", "Child2"),
          ]),
        ])
      );

      const patch: UpdatePatch = {
        op: "update",
        id: "e1",
        children: ["e3", "e2"], // reorder
      };
      store.applyPatches([patch]);

      expect(store.getNode("e1")?.childIds).toEqual(["e3", "e2"]);
    });

    it("creates new object reference on update (immutability)", () => {
      const nodeBefore = store.getNode("e1");
      const patch: UpdatePatch = {
        op: "update",
        id: "e1",
        props: { text: "Changed" },
      };
      store.applyPatches([patch]);
      const nodeAfter = store.getNode("e1");

      // Must be different object reference for React to detect change
      expect(nodeAfter).not.toBe(nodeBefore);
      expect(nodeAfter?.props.text).toBe("Changed");
    });

    it("creates new props object on update", () => {
      const nodeBefore = store.getNode("e1");
      const propsBefore = nodeBefore?.props;

      const patch: UpdatePatch = {
        op: "update",
        id: "e1",
        props: { text: "Changed" },
      };
      store.applyPatches([patch]);

      const nodeAfter = store.getNode("e1");
      expect(nodeAfter?.props).not.toBe(propsBefore);
    });

    it("warns but continues on unknown node", () => {
      const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

      const patch: UpdatePatch = {
        op: "update",
        id: "unknown",
        props: { text: "test" },
      };
      store.applyPatches([patch]);

      expect(warnSpy).toHaveBeenCalledWith(
        expect.stringContaining("unknown node")
      );
      warnSpy.mockRestore();
    });
  });

  describe("applyPatches - add", () => {
    beforeEach(() => {
      store.setTree(makeElement("root", "App", {}, []));
    });

    it("adds new node to store", () => {
      const patch: AddPatch = {
        op: "add",
        parent_id: "root",
        children: ["e1"],
        node: makeElement("e1", "Button", { text: "New" }),
      };
      store.applyPatches([patch]);

      expect(store.getNode("e1")).toBeDefined();
      expect(store.getNode("e1")?.props.text).toBe("New");
    });

    it("updates parent childIds", () => {
      const patch: AddPatch = {
        op: "add",
        parent_id: "root",
        children: ["e1", "e2"],
        node: makeElement("e1", "Button"),
      };
      store.applyPatches([patch]);

      expect(store.getNode("root")?.childIds).toEqual(["e1", "e2"]);
    });

    it("adds nested subtree recursively", () => {
      const patch: AddPatch = {
        op: "add",
        parent_id: "root",
        children: ["container"],
        node: makeElement("container", "Container", {}, [
          makeElement("child1", "Label", { text: "First" }),
          makeElement("child2", "Label", { text: "Second" }),
        ]),
      };
      store.applyPatches([patch]);

      expect(store.getNode("container")?.childIds).toEqual([
        "child1",
        "child2",
      ]);
      expect(store.getNode("child1")?.props.text).toBe("First");
      expect(store.getNode("child2")?.props.text).toBe("Second");
    });
  });

  describe("applyPatches - remove", () => {
    beforeEach(() => {
      store.setTree(
        makeElement("root", "App", {}, [
          makeElement("e1", "Container", {}, [
            makeElement("e2", "Child"),
            makeElement("e3", "Child"),
          ]),
        ])
      );
    });

    it("removes node from store", () => {
      expect(store.getNode("e2")).toBeDefined();

      const patch: RemovePatch = { op: "remove", id: "e2" };
      store.applyPatches([patch]);

      expect(store.getNode("e2")).toBeUndefined();
    });

    it("removes descendants recursively", () => {
      expect(store.getNode("e1")).toBeDefined();
      expect(store.getNode("e2")).toBeDefined();
      expect(store.getNode("e3")).toBeDefined();

      const patch: RemovePatch = { op: "remove", id: "e1" };
      store.applyPatches([patch]);

      expect(store.getNode("e1")).toBeUndefined();
      expect(store.getNode("e2")).toBeUndefined();
      expect(store.getNode("e3")).toBeUndefined();
    });
  });

  describe("subscriptions", () => {
    beforeEach(() => {
      store.setTree(
        makeElement("root", "App", {}, [makeElement("e1", "Label", { text: "Hello" })])
      );
    });

    it("notifies node listener on update", () => {
      const listener = vi.fn();
      store.subscribeToNode("e1", listener);

      store.applyPatches([{ op: "update", id: "e1", props: { text: "World" } }]);

      expect(listener).toHaveBeenCalledTimes(1);
    });

    it("does not notify unrelated node listeners", () => {
      const e1Listener = vi.fn();
      const rootListener = vi.fn();
      store.subscribeToNode("e1", e1Listener);
      store.subscribeToNode("root", rootListener);

      store.applyPatches([{ op: "update", id: "e1", props: { text: "World" } }]);

      expect(e1Listener).toHaveBeenCalledTimes(1);
      expect(rootListener).not.toHaveBeenCalled();
    });

    it("unsubscribes correctly", () => {
      const listener = vi.fn();
      const unsubscribe = store.subscribeToNode("e1", listener);
      unsubscribe();

      store.applyPatches([{ op: "update", id: "e1", props: { text: "World" } }]);

      expect(listener).not.toHaveBeenCalled();
    });

    it("notifies global listeners on setTree", () => {
      const listener = vi.fn();
      store.subscribeGlobal(listener);

      store.setTree(makeElement("new", "NewApp"));

      expect(listener).toHaveBeenCalled();
    });

    it("notifies global listeners on patches", () => {
      const listener = vi.fn();
      store.subscribeGlobal(listener);

      store.applyPatches([{ op: "update", id: "e1", props: { text: "World" } }]);

      expect(listener).toHaveBeenCalled();
    });

    it("cleans up node listeners on remove", () => {
      const listener = vi.fn();
      store.subscribeToNode("e1", listener);

      // Remove the node
      store.applyPatches([{ op: "remove", id: "e1" }]);
      listener.mockClear();

      // Try updating removed node - should not call listener
      store.applyPatches([{ op: "update", id: "e1", props: { text: "test" } }]);
      expect(listener).not.toHaveBeenCalled();
    });
  });
});
