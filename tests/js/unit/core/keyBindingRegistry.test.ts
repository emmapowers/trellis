import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { KeyBindingRegistry } from "@common/core/keyBindingRegistry";
import { KeyState } from "@common/core/keyState";

function makeBinding(
  callbackId: string,
  key: string,
  depth: number,
  overrides: Record<string, unknown> = {}
): Record<string, unknown> {
  return {
    filter: {
      key,
      ctrl: false,
      shift: false,
      alt: false,
      meta: false,
      mod: false,
    },
    handler: { __callback__: callbackId },
    event_type: "keydown",
    require_reset: true,
    ignore_in_inputs: false,
    depth,
    ...overrides,
  };
}

describe("KeyBindingRegistry", () => {
  let keyState: KeyState;
  let sendKeyEvent: ReturnType<typeof vi.fn>;
  let registry: KeyBindingRegistry;

  beforeEach(() => {
    keyState = new KeyState();
    sendKeyEvent = vi.fn().mockResolvedValue(true);
    registry = new KeyBindingRegistry(keyState, sendKeyEvent);
  });

  afterEach(() => {
    registry.dispose();
    keyState.dispose();
  });

  it("fires deepest binding first", () => {
    const shallow = makeBinding("cb-shallow", "Escape", 1);
    const deep = makeBinding("cb-deep", "Escape", 3);

    registry.updateElement("el-1", [shallow]);
    registry.updateElement("el-2", [deep]);

    // Dispatch keydown
    const event = new KeyboardEvent("keydown", { key: "Escape", bubbles: true });
    document.dispatchEvent(event);

    // Deep binding should fire first
    expect(sendKeyEvent).toHaveBeenCalledTimes(1);
    expect(sendKeyEvent.mock.calls[0][0]).toBe("cb-deep");
  });

  it("updateElement replaces previous bindings", () => {
    const binding1 = makeBinding("cb-1", "Escape", 1);
    const binding2 = makeBinding("cb-2", "Enter", 1);

    registry.updateElement("el-1", [binding1]);
    registry.updateElement("el-1", [binding2]);

    // Escape should no longer fire
    document.dispatchEvent(
      new KeyboardEvent("keydown", { key: "Escape", bubbles: true })
    );
    expect(sendKeyEvent).not.toHaveBeenCalled();

    // Enter should fire
    document.dispatchEvent(
      new KeyboardEvent("keydown", { key: "Enter", bubbles: true })
    );
    expect(sendKeyEvent).toHaveBeenCalledTimes(1);
    expect(sendKeyEvent.mock.calls[0][0]).toBe("cb-2");
  });

  it("removeElement cleans up", () => {
    const binding = makeBinding("cb-1", "Escape", 1);
    registry.updateElement("el-1", [binding]);
    registry.removeElement("el-1");

    document.dispatchEvent(
      new KeyboardEvent("keydown", { key: "Escape", bubbles: true })
    );
    expect(sendKeyEvent).not.toHaveBeenCalled();
  });

  it("chains to shallower binding on pass", async () => {
    const shallow = makeBinding("cb-shallow", "Escape", 1);
    const deep = makeBinding("cb-deep", "Escape", 3);

    // Deep handler returns false (pass)
    sendKeyEvent.mockResolvedValueOnce(false).mockResolvedValueOnce(true);

    registry.updateElement("el-1", [shallow]);
    registry.updateElement("el-2", [deep]);

    const event = new KeyboardEvent("keydown", { key: "Escape", bubbles: true });
    document.dispatchEvent(event);

    // Wait for async chain
    await vi.waitFor(() => {
      expect(sendKeyEvent).toHaveBeenCalledTimes(2);
    });

    expect(sendKeyEvent.mock.calls[0][0]).toBe("cb-deep");
    expect(sendKeyEvent.mock.calls[1][0]).toBe("cb-shallow");
  });
});
