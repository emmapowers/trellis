import { describe, it, expect, beforeEach, vi, Mock } from "vitest";
import {
  ClientMessageHandler,
  ClientMessageHandlerCallbacks,
  ConnectionState,
} from "@common/ClientMessageHandler";
import { store } from "@common/core/store";
import {
  MessageType,
  HelloResponseMessage,
  PatchMessage,
  ErrorMessage,
} from "@common/types";

// Mock the store
vi.mock("@common/core/store", () => ({
  store: {
    applyPatches: vi.fn(),
  },
}));

describe("ClientMessageHandler", () => {
  let handler: ClientMessageHandler;
  let callbacks: {
    onConnectionStateChange: Mock;
    onConnected: Mock;
    onError: Mock;
  };

  beforeEach(() => {
    vi.clearAllMocks();

    callbacks = {
      onConnectionStateChange: vi.fn(),
      onConnected: vi.fn(),
      onError: vi.fn(),
    };

    handler = new ClientMessageHandler(callbacks);
  });

  describe("initial state", () => {
    it("starts disconnected", () => {
      expect(handler.getConnectionState()).toBe("disconnected");
    });

    it("has no session ID initially", () => {
      expect(handler.getSessionId()).toBeNull();
    });

    it("has no server version initially", () => {
      expect(handler.getServerVersion()).toBeNull();
    });
  });

  describe("setConnectionState", () => {
    it("updates connection state", () => {
      handler.setConnectionState("connecting");
      expect(handler.getConnectionState()).toBe("connecting");
    });

    it("calls onConnectionStateChange callback", () => {
      handler.setConnectionState("connecting");
      expect(callbacks.onConnectionStateChange).toHaveBeenCalledWith(
        "connecting"
      );
    });
  });

  describe("handleMessage - HELLO_RESPONSE", () => {
    const helloResponse: HelloResponseMessage = {
      type: MessageType.HELLO_RESPONSE,
      session_id: "test-session-123",
      server_version: "1.2.3",
    };

    it("sets session ID", () => {
      handler.handleMessage(helloResponse);
      expect(handler.getSessionId()).toBe("test-session-123");
    });

    it("sets server version", () => {
      handler.handleMessage(helloResponse);
      expect(handler.getServerVersion()).toBe("1.2.3");
    });

    it("sets connection state to connected", () => {
      handler.handleMessage(helloResponse);
      expect(handler.getConnectionState()).toBe("connected");
    });

    it("calls onConnected callback", () => {
      handler.handleMessage(helloResponse);
      expect(callbacks.onConnected).toHaveBeenCalledWith(helloResponse);
    });

    it("calls onConnectionStateChange callback", () => {
      handler.handleMessage(helloResponse);
      expect(callbacks.onConnectionStateChange).toHaveBeenCalledWith(
        "connected"
      );
    });
  });

  describe("handleMessage - PATCH", () => {
    it("calls store.applyPatches with patches", () => {
      const patches = [
        { op: "update" as const, id: "e1", props: { text: "Hello" } },
        { op: "remove" as const, id: "e2" },
      ];
      const patchMessage: PatchMessage = {
        type: MessageType.PATCH,
        patches,
      };

      handler.handleMessage(patchMessage);

      expect(store.applyPatches).toHaveBeenCalledWith(patches);
    });
  });

  describe("handleMessage - ERROR", () => {
    let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

    beforeEach(() => {
      consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    });

    afterEach(() => {
      consoleErrorSpy.mockRestore();
    });

    it("logs error to console", () => {
      const errorMessage: ErrorMessage = {
        type: MessageType.ERROR,
        error: "Something went wrong",
        context: "render",
      };

      handler.handleMessage(errorMessage);

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Trellis render error:",
        "Something went wrong"
      );
    });

    it("calls onError callback with error and context", () => {
      const errorMessage: ErrorMessage = {
        type: MessageType.ERROR,
        error: "Callback failed",
        context: "callback",
      };

      handler.handleMessage(errorMessage);

      expect(callbacks.onError).toHaveBeenCalledWith("Callback failed", "callback");
    });
  });

  describe("works without callbacks", () => {
    it("handles messages without errors when no callbacks provided", () => {
      const handlerNoCallbacks = new ClientMessageHandler();

      // Should not throw
      expect(() => {
        handlerNoCallbacks.handleMessage({
          type: MessageType.HELLO_RESPONSE,
          session_id: "test",
          server_version: "1.0.0",
        });
      }).not.toThrow();

      expect(() => {
        handlerNoCallbacks.setConnectionState("connecting");
      }).not.toThrow();
    });
  });
});
