import { describe, it, expect, beforeEach, afterEach, vi, Mock } from "vitest";
import {
  ClientMessageHandler,
  ClientMessageHandlerCallbacks,
  ConnectionState,
} from "@common/ClientMessageHandler";
import { store } from "@common/core/store";
import { registerProxyTarget } from "@common/proxyTargets";
import {
  MessageType,
  HelloResponseMessage,
  PatchMessage,
  ErrorMessage,
  HistoryPushMessage,
  HistoryBackMessage,
  HistoryForwardMessage,
  ReloadMessage,
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
    onHistoryPush: Mock;
    onHistoryBack: Mock;
    onHistoryForward: Mock;
  };

  beforeEach(() => {
    vi.clearAllMocks();

    callbacks = {
      onConnectionStateChange: vi.fn(),
      onConnected: vi.fn(),
      onError: vi.fn(),
      onHistoryPush: vi.fn(),
      onHistoryBack: vi.fn(),
      onHistoryForward: vi.fn(),
    };

    handler = new ClientMessageHandler(callbacks);
  });

  afterEach(() => {
    delete (window as Window & typeof globalThis & Record<string, unknown>).encoder;
    delete (window as Window & typeof globalThis & Record<string, unknown>).nestedGlobal;
    delete (window.navigator as Navigator & Record<string, unknown>).clipboard;
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

    it("sets session ID", async () => {
      await handler.handleMessage(helloResponse);
      expect(handler.getSessionId()).toBe("test-session-123");
    });

    it("sets server version", async () => {
      await handler.handleMessage(helloResponse);
      expect(handler.getServerVersion()).toBe("1.2.3");
    });

    it("sets connection state to connected", async () => {
      await handler.handleMessage(helloResponse);
      expect(handler.getConnectionState()).toBe("connected");
    });

    it("calls onConnected callback", async () => {
      await handler.handleMessage(helloResponse);
      expect(callbacks.onConnected).toHaveBeenCalledWith(helloResponse);
    });

    it("calls onConnectionStateChange callback", async () => {
      await handler.handleMessage(helloResponse);
      expect(callbacks.onConnectionStateChange).toHaveBeenCalledWith(
        "connected"
      );
    });
  });

  describe("handleMessage - PATCH", () => {
    it("calls store.applyPatches with patches", async () => {
      const patches = [
        { op: "update" as const, id: "e1", props: { text: "Hello" } },
        { op: "remove" as const, id: "e2" },
      ];
      const patchMessage: PatchMessage = {
        type: MessageType.PATCH,
        patches,
      };

      await handler.handleMessage(patchMessage);

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

    it("logs error to console", async () => {
      const errorMessage: ErrorMessage = {
        type: MessageType.ERROR,
        error: "Something went wrong",
        context: "render",
      };

      await handler.handleMessage(errorMessage);

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Trellis render error:",
        "Something went wrong"
      );
    });

    it("calls onError callback with error and context", async () => {
      const errorMessage: ErrorMessage = {
        type: MessageType.ERROR,
        error: "Callback failed",
        context: "callback",
      };

      await handler.handleMessage(errorMessage);

      expect(callbacks.onError).toHaveBeenCalledWith("Callback failed", "callback");
    });
  });

  describe("handleMessage - HISTORY_PUSH", () => {
    it("calls onHistoryPush callback with path", async () => {
      const historyPush: HistoryPushMessage = {
        type: MessageType.HISTORY_PUSH,
        path: "/users/123",
      };

      await handler.handleMessage(historyPush);

      expect(callbacks.onHistoryPush).toHaveBeenCalledWith("/users/123");
    });
  });

  describe("handleMessage - HISTORY_BACK", () => {
    it("calls onHistoryBack callback", async () => {
      const historyBack: HistoryBackMessage = {
        type: MessageType.HISTORY_BACK,
      };

      await handler.handleMessage(historyBack);

      expect(callbacks.onHistoryBack).toHaveBeenCalled();
    });
  });

  describe("handleMessage - HISTORY_FORWARD", () => {
    it("calls onHistoryForward callback", async () => {
      const historyForward: HistoryForwardMessage = {
        type: MessageType.HISTORY_FORWARD,
      };

      await handler.handleMessage(historyForward);

      expect(callbacks.onHistoryForward).toHaveBeenCalled();
    });
  });

  describe("handleMessage - RELOAD", () => {
    let locationReloadSpy: ReturnType<typeof vi.spyOn>;
    let originalLocation: Location;

    beforeEach(() => {
      // Mock window.location.reload
      originalLocation = window.location;
      locationReloadSpy = vi.fn();
      Object.defineProperty(window, "location", {
        value: { reload: locationReloadSpy },
        writable: true,
      });
    });

    afterEach(() => {
      Object.defineProperty(window, "location", {
        value: originalLocation,
        writable: true,
      });
    });

    it("calls window.location.reload", async () => {
      const reloadMessage: ReloadMessage = {
        type: MessageType.RELOAD,
      };

      await handler.handleMessage(reloadMessage);

      expect(locationReloadSpy).toHaveBeenCalled();
    });
  });

  describe("handleMessage - PROXY_REQUEST", () => {
    it("dispatches proxy calls to registered targets", async () => {
      const sendMessage = vi.fn();
      registerProxyTarget("demo_api", {
        greet(name: string) {
          return `hello ${name}`;
        },
      });
      handler = new ClientMessageHandler(callbacks, store, sendMessage);

      await handler.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-1",
        proxy_id: "demo_api",
        operation: "call",
        member: "greet",
        args: ["Emma"],
      });

      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-1",
        result: "hello Emma",
        error: null,
        error_type: null,
      });
    });

    it("dispatches function proxy calls to callable targets", async () => {
      const sendMessage = vi.fn();
      registerProxyTarget("formatNow", (value: number) => `value: ${value}`);
      handler = new ClientMessageHandler(callbacks, store, sendMessage);

      await handler.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-fn-1",
        proxy_id: "formatNow",
        operation: "call",
        member: null,
        args: [3],
      });

      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-fn-1",
        result: "value: 3",
        error: null,
        error_type: null,
      });
    });

    it("dispatches async function proxy calls to callable targets", async () => {
      const sendMessage = vi.fn();
      registerProxyTarget("loadValue", async (value: number) => `value: ${value}`);
      handler = new ClientMessageHandler(callbacks, store, sendMessage);

      await handler.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-fn-2",
        proxy_id: "loadValue",
        operation: "call",
        member: null,
        args: [5],
      });

      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-fn-2",
        result: "value: 5",
        error: null,
        error_type: null,
      });
    });

    it("returns proxy dispatch errors without throwing", async () => {
      const sendMessage = vi.fn();
      registerProxyTarget("explode_api", {
        explode() {
          throw new TypeError("bad input");
        },
      });
      handler = new ClientMessageHandler(callbacks, store, sendMessage);

      await handler.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-2",
        proxy_id: "explode_api",
        operation: "call",
        member: "explode",
        args: [],
      });

      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-2",
        result: null,
        error: "bad input",
        error_type: "TypeError",
      });
    });

    it("returns an error for missing proxy targets", async () => {
      const sendMessage = vi.fn();
      handler = new ClientMessageHandler(callbacks, store, sendMessage);

      await handler.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-3",
        proxy_id: "missing_api",
        operation: "call",
        member: "greet",
        args: [],
      });

      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-3",
        result: null,
        error: "Proxy target not found: missing_api",
        error_type: "Error",
      });
    });

    it("returns an error for non-callable function targets", async () => {
      const sendMessage = vi.fn();
      registerProxyTarget("bad_function", { answer: 42 });
      handler = new ClientMessageHandler(callbacks, store, sendMessage);

      await handler.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-fn-3",
        proxy_id: "bad_function",
        operation: "call",
        member: null,
        args: [],
      });

      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-fn-3",
        result: null,
        error: "Proxy target is not callable: bad_function",
        error_type: "Error",
      });
    });

    it("returns an error for non-callable proxy methods", async () => {
      const sendMessage = vi.fn();
      registerProxyTarget("bad_api", {
        answer: 42,
      });
      handler = new ClientMessageHandler(callbacks, store, sendMessage);

      await handler.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-4",
        proxy_id: "bad_api",
        operation: "call",
        member: "answer",
        args: [],
      });

      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-4",
        result: null,
        error: "Proxy method not found or not callable: bad_api.answer",
        error_type: "Error",
      });
    });

    it("dispatches global object proxy calls with the resolved object as this", async () => {
      const sendMessage = vi.fn();
      Object.defineProperty(window, "localStorage", {
        value: {
          prefix: "theme:",
          getItem(key: string) {
            return `${this.prefix}${key}`;
          },
        },
        writable: true,
        configurable: true,
      });
      handler = new ClientMessageHandler(callbacks, store, sendMessage);

      await handler.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-global-1",
        proxy_id: "__global__:window.localStorage",
        operation: "call",
        member: "getItem",
        args: ["accent"],
      });

      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-global-1",
        result: "theme:accent",
        error: null,
        error_type: null,
      });
    });

    it("dispatches callable globals with the parent object as receiver", async () => {
      const sendMessage = vi.fn();
      (window as Window & typeof globalThis & Record<string, unknown>).encoder = {
        prefix: "enc:",
        encode(value: string) {
          return `${this.prefix}${value}`;
        },
      };
      handler = new ClientMessageHandler(callbacks, store, sendMessage);

      await handler.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-global-2",
        proxy_id: "__global__:window.encoder.encode",
        operation: "call",
        member: null,
        args: ["hello world"],
      });

      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-global-2",
        result: "enc:hello world",
        error: null,
        error_type: null,
      });
    });

    it("returns a global-not-found error for missing global paths", async () => {
      const sendMessage = vi.fn();
      handler = new ClientMessageHandler(callbacks, store, sendMessage);

      await handler.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-global-3",
        proxy_id: "__global__:window.missingThing",
        operation: "call",
        member: "call",
        args: [],
      });

      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-global-3",
        result: null,
        error: "Global target not found: window.missingThing",
        error_type: "Error",
      });
    });

    it("returns a global-method error for missing methods on global objects", async () => {
      const sendMessage = vi.fn();
      Object.defineProperty(window, "localStorage", {
        value: { answer: 42 },
        writable: true,
        configurable: true,
      });
      handler = new ClientMessageHandler(callbacks, store, sendMessage);

      await handler.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-global-4",
        proxy_id: "__global__:window.localStorage",
        operation: "call",
        member: "getItem",
        args: ["accent"],
      });

      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-global-4",
        result: null,
        error: "Global method not found or not callable: window.localStorage.getItem",
        error_type: "Error",
      });
    });

    it("returns a global-callable error for non-callable callable globals", async () => {
      const sendMessage = vi.fn();
      (window as Window & typeof globalThis & Record<string, unknown>).nestedGlobal = {
        value: 42,
      };
      handler = new ClientMessageHandler(callbacks, store, sendMessage);

      await handler.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-global-5",
        proxy_id: "__global__:window.nestedGlobal.value",
        operation: "call",
        member: null,
        args: [],
      });

      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-global-5",
        result: null,
        error: "Global target is not callable: window.nestedGlobal.value",
        error_type: "Error",
      });
    });

    it("dispatches async clipboard writes through navigator.clipboard", async () => {
      const sendMessage = vi.fn();
      Object.defineProperty(window.navigator, "clipboard", {
        value: {
          async writeText(text: string) {
            return `wrote:${text}`;
          },
        },
        configurable: true,
      });
      handler = new ClientMessageHandler(callbacks, store, sendMessage);

      await handler.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-clipboard-1",
        proxy_id: "__global__:navigator.clipboard",
        operation: "call",
        member: "writeText",
        args: ["copied text"],
      });

      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-clipboard-1",
        result: "wrote:copied text",
        error: null,
        error_type: null,
      });
    });

    it("dispatches async clipboard reads through navigator.clipboard", async () => {
      const sendMessage = vi.fn();
      Object.defineProperty(window.navigator, "clipboard", {
        value: {
          async readText() {
            return "copied text";
          },
        },
        configurable: true,
      });
      handler = new ClientMessageHandler(callbacks, store, sendMessage);

      await handler.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-clipboard-2",
        proxy_id: "__global__:navigator.clipboard",
        operation: "call",
        member: "readText",
        args: [],
      });

      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-clipboard-2",
        result: "copied text",
        error: null,
        error_type: null,
      });
    });

    it("surfaces rejected clipboard promises as proxy errors", async () => {
      const sendMessage = vi.fn();
      Object.defineProperty(window.navigator, "clipboard", {
        value: {
          async writeText() {
            throw new DOMException("Write blocked", "NotAllowedError");
          },
        },
        configurable: true,
      });
      handler = new ClientMessageHandler(callbacks, store, sendMessage);

      await handler.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-clipboard-3",
        proxy_id: "__global__:navigator.clipboard",
        operation: "call",
        member: "writeText",
        args: ["copied text"],
      });

      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-clipboard-3",
        result: null,
        error: "Write blocked",
        error_type: "NotAllowedError",
      });
    });

    it("returns a missing-path error when navigator.clipboard is unavailable", async () => {
      const sendMessage = vi.fn();
      handler = new ClientMessageHandler(callbacks, store, sendMessage);

      await handler.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-clipboard-4",
        proxy_id: "__global__:navigator.clipboard",
        operation: "call",
        member: "readText",
        args: [],
      });

      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-clipboard-4",
        result: null,
        error: "Global target not found: navigator.clipboard",
        error_type: "Error",
      });
    });

    it("gets properties from proxy targets", async () => {
      const sendMessage = vi.fn();
      registerProxyTarget("document_api", { title: "Original title" });
      handler = new ClientMessageHandler(callbacks, store, sendMessage);

      await handler.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-prop-1",
        proxy_id: "document_api",
        operation: "get",
        member: "title",
        args: [],
      });

      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-prop-1",
        result: "Original title",
        error: null,
        error_type: null,
      });
    });

    it("sets properties on global targets with the resolved object as receiver", async () => {
      const sendMessage = vi.fn();
      Object.defineProperty(window, "document", {
        value: { title: "Before" },
        writable: true,
        configurable: true,
      });
      handler = new ClientMessageHandler(callbacks, store, sendMessage);

      await handler.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-prop-2",
        proxy_id: "__global__:document",
        operation: "set",
        member: "title",
        args: [],
        value: "After",
      });

      expect(window.document.title).toBe("After");
      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-prop-2",
        result: true,
        error: null,
        error_type: null,
      });
    });

    it("deletes properties on global targets", async () => {
      const sendMessage = vi.fn();
      (window as Window & typeof globalThis & Record<string, unknown>).__trellisProxyDemoFlag =
        "demo";
      handler = new ClientMessageHandler(callbacks, store, sendMessage);

      await handler.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-prop-3",
        proxy_id: "__global__:window",
        operation: "delete",
        member: "__trellisProxyDemoFlag",
        args: [],
      });

      expect(
        "__trellisProxyDemoFlag" in
          (window as Window & typeof globalThis & Record<string, unknown>)
      ).toBe(false);
      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-prop-3",
        result: true,
        error: null,
        error_type: null,
      });
    });

    it("normalizes missing property gets to null", async () => {
      const sendMessage = vi.fn();
      Object.defineProperty(window, "document", {
        value: {},
        writable: true,
        configurable: true,
      });
      handler = new ClientMessageHandler(callbacks, store, sendMessage);

      await handler.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-prop-4",
        proxy_id: "__global__:document",
        operation: "get",
        member: "missingValue",
        args: [],
      });

      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-prop-4",
        result: null,
        error: null,
        error_type: null,
      });
    });

    it("materializes callback sentinels and resolves their returned values", async () => {
      const sendMessage = vi.fn();
      registerProxyTarget("invokeCallback", {
        async run(callback: (value: number) => Promise<number>, value: number) {
          return await callback(value + 1);
        },
      });
      handler = new ClientMessageHandler(callbacks, store, sendMessage);

      const requestPromise = handler.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-callback-1",
        proxy_id: "invokeCallback",
        operation: "call",
        member: "run",
        args: [{ __proxy_callback__: "callback-1" }, 3],
      });

      await vi.waitFor(() => expect(sendMessage).toHaveBeenCalledTimes(1));
      const callbackRequest = sendMessage.mock.calls[0][0];
      expect(callbackRequest).toMatchObject({
        type: MessageType.PROXY_REQUEST,
        proxy_id: "__callback__:callback-1",
        operation: "call",
        member: null,
        args: [4],
      });

      await handler.handleMessage({
        type: MessageType.PROXY_RESPONSE,
        request_id: callbackRequest.request_id,
        result: 8,
        error: null,
        error_type: null,
      });
      await requestPromise;

      expect(sendMessage).toHaveBeenLastCalledWith({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-callback-1",
        result: 8,
        error: null,
        error_type: null,
      });
    });

    it("rejects callback wrappers using proxy response error_type as Error.name", async () => {
      const sendMessage = vi.fn();
      registerProxyTarget("invokeCallbackError", {
        async run(callback: (value: number) => Promise<number>) {
          return await callback(7);
        },
      });
      handler = new ClientMessageHandler(callbacks, store, sendMessage);

      const requestPromise = handler.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-callback-2",
        proxy_id: "invokeCallbackError",
        operation: "call",
        member: "run",
        args: [{ __proxy_callback__: "callback-2" }],
      });

      await vi.waitFor(() => expect(sendMessage).toHaveBeenCalledTimes(1));
      const callbackRequest = sendMessage.mock.calls[0][0];

      await handler.handleMessage({
        type: MessageType.PROXY_RESPONSE,
        request_id: callbackRequest.request_id,
        result: null,
        error: "callback failed",
        error_type: "TypeError",
      });
      await requestPromise;

      expect(sendMessage).toHaveBeenLastCalledWith({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-callback-2",
        result: null,
        error: "callback failed",
        error_type: "TypeError",
      });
    });
  });

  describe("works without callbacks", () => {
    it("handles messages without errors when no callbacks provided", async () => {
      const handlerNoCallbacks = new ClientMessageHandler();

      await expect(
        handlerNoCallbacks.handleMessage({
          type: MessageType.HELLO_RESPONSE,
          session_id: "test",
          server_version: "1.0.0",
        })
      ).resolves.toBeUndefined();

      expect(() => {
        handlerNoCallbacks.setConnectionState("connecting");
      }).not.toThrow();
    });

    it("handles router messages without errors when no callbacks provided", async () => {
      const handlerNoCallbacks = new ClientMessageHandler();

      await expect(
        handlerNoCallbacks.handleMessage({
          type: MessageType.HISTORY_PUSH,
          path: "/test",
        })
      ).resolves.toBeUndefined();

      await expect(
        handlerNoCallbacks.handleMessage({
          type: MessageType.HISTORY_BACK,
        })
      ).resolves.toBeUndefined();

      await expect(
        handlerNoCallbacks.handleMessage({
          type: MessageType.HISTORY_FORWARD,
        })
      ).resolves.toBeUndefined();
    });
  });
});
