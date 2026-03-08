import { describe, it, expect, beforeEach, afterEach, vi, Mock } from "vitest";
import { BrowserClient } from "@browser/BrowserClient";
import { RoutingMode } from "@common/RouterManager";
import { MessageType } from "@common/types";
import { registerProxyTarget } from "@common/proxyTargets";

describe("BrowserClient", () => {
  let originalHistory: History;
  let originalLocation: Location;
  let mockPushState: Mock;

  beforeEach(() => {
    // Store originals
    originalHistory = window.history;
    originalLocation = window.location;

    // Mock history
    mockPushState = vi.fn();
    const mockHistory = {
      pushState: mockPushState,
      back: vi.fn(),
      forward: vi.fn(),
      state: null,
      length: 1,
    };
    Object.defineProperty(window, "history", {
      value: mockHistory,
      writable: true,
      configurable: true,
    });

    // Mock location with hash support
    Object.defineProperty(window, "location", {
      value: { pathname: "/", hash: "" },
      writable: true,
      configurable: true,
    });
  });

  afterEach(() => {
    // Restore originals
    Object.defineProperty(window, "history", {
      value: originalHistory,
      writable: true,
      configurable: true,
    });
    Object.defineProperty(window, "location", {
      value: originalLocation,
      writable: true,
      configurable: true,
    });
    delete (window as Window & typeof globalThis & Record<string, unknown>).encoder;
    delete (window.navigator as Navigator & Record<string, unknown>).clipboard;
    vi.clearAllMocks();
  });

  describe("routing mode", () => {
    it("defaults to Hash mode (uses window.location.hash)", () => {
      const client = new BrowserClient();

      // Set up send callback so navigation works
      client.setSendCallback(() => {});

      // In Hash mode, pushState should update hash, not call pushState
      // @ts-expect-error - accessing private property for testing
      client.routerManager.pushState("/users");

      expect(mockPushState).not.toHaveBeenCalled();
      expect(window.location.hash).toBe("#/users");

      client.disconnect();
    });

    it("uses Url mode when routingMode=Url", () => {
      const client = new BrowserClient({}, undefined, {
        routingMode: RoutingMode.Url,
      });

      // Set up send callback so navigation works
      client.setSendCallback(() => {});

      // @ts-expect-error - accessing private property for testing
      client.routerManager.pushState("/users");

      expect(mockPushState).toHaveBeenCalledWith(
        { path: "/users" },
        "",
        "/users"
      );

      client.disconnect();
    });

    it("uses Hidden mode when routingMode=Hidden", () => {
      const client = new BrowserClient({}, undefined, {
        routingMode: RoutingMode.Hidden,
      });

      // Set up send callback so navigation works
      client.setSendCallback(() => {});

      // In Hidden mode, pushState should NOT call window.history.pushState
      // @ts-expect-error - accessing private property for testing
      client.routerManager.pushState("/users");

      expect(mockPushState).not.toHaveBeenCalled();
      expect(window.location.hash).toBe(""); // Hash should not be updated either

      client.disconnect();
    });

    it("reads initial path from hash in Hash mode", () => {
      Object.defineProperty(window, "location", {
        value: { pathname: "/", hash: "#/users/123" },
        writable: true,
        configurable: true,
      });

      const client = new BrowserClient();
      client.setSendCallback(() => {});

      // @ts-expect-error - accessing private property for testing
      expect(client.routerManager.getCurrentPath()).toBe("/users/123");

      client.disconnect();
    });
  });

  describe("proxy requests", () => {
    it("sends method proxy responses through the browser transport", async () => {
      const sentMessages: unknown[] = [];
      const client = new BrowserClient();
      client.setSendCallback((msg) => {
        sentMessages.push(msg);
      });
      registerProxyTarget("demo_api", {
        async greet(name: string) {
          return `hello ${name}`;
        },
      });

      await client.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-1",
        proxy_id: "demo_api",
        operation: "call",
        member: "greet",
        args: ["Emma"],
      });

      expect(sentMessages).toContainEqual({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-1",
        result: "hello Emma",
        error: null,
        error_type: null,
      });

      client.disconnect();
    });

    it("sends function proxy responses through the browser transport", async () => {
      const sentMessages: unknown[] = [];
      const client = new BrowserClient();
      client.setSendCallback((msg) => {
        sentMessages.push(msg);
      });
      registerProxyTarget("formatNow", async (value: number) => `value: ${value}`);

      await client.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-2",
        proxy_id: "formatNow",
        operation: "call",
        member: null,
        args: [3],
      });

      expect(sentMessages).toContainEqual({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-2",
        result: "value: 3",
        error: null,
        error_type: null,
      });

      client.disconnect();
    });

    it("sends global object proxy responses through the browser transport", async () => {
      const sentMessages: unknown[] = [];
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
      const client = new BrowserClient();
      client.setSendCallback((msg) => {
        sentMessages.push(msg);
      });

      await client.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-global-1",
        proxy_id: "__global__:window.localStorage",
        operation: "call",
        member: "getItem",
        args: ["accent"],
      });

      expect(sentMessages).toContainEqual({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-global-1",
        result: "theme:accent",
        error: null,
        error_type: null,
      });

      client.disconnect();
    });

    it("sends callable global responses through the browser transport", async () => {
      const sentMessages: unknown[] = [];
      (window as Window & typeof globalThis & Record<string, unknown>).encoder = {
        prefix: "enc:",
        encode(value: string) {
          return `${this.prefix}${value}`;
        },
      };
      const client = new BrowserClient();
      client.setSendCallback((msg) => {
        sentMessages.push(msg);
      });

      await client.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-global-2",
        proxy_id: "__global__:window.encoder.encode",
        operation: "call",
        member: null,
        args: ["hello world"],
      });

      expect(sentMessages).toContainEqual({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-global-2",
        result: "enc:hello world",
        error: null,
        error_type: null,
      });

      client.disconnect();
    });

    it("sends async clipboard responses through the browser transport", async () => {
      const sentMessages: unknown[] = [];
      Object.defineProperty(window.navigator, "clipboard", {
        value: {
          async readText() {
            return "copied text";
          },
        },
        configurable: true,
      });
      const client = new BrowserClient();
      client.setSendCallback((msg) => {
        sentMessages.push(msg);
      });

      await client.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-clipboard-1",
        proxy_id: "__global__:navigator.clipboard",
        operation: "call",
        member: "readText",
        args: [],
      });

      expect(sentMessages).toContainEqual({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-clipboard-1",
        result: "copied text",
        error: null,
        error_type: null,
      });

      client.disconnect();
    });

    it("sends property get responses through the browser transport", async () => {
      const sentMessages: unknown[] = [];
      Object.defineProperty(window, "document", {
        value: { title: "Original title" },
        writable: true,
        configurable: true,
      });
      const client = new BrowserClient();
      client.setSendCallback((msg) => {
        sentMessages.push(msg);
      });

      await client.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-prop-1",
        proxy_id: "__global__:document",
        operation: "get",
        member: "title",
        args: [],
      });

      expect(sentMessages).toContainEqual({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-prop-1",
        result: "Original title",
        error: null,
        error_type: null,
      });

      client.disconnect();
    });

    it("sends property set responses through the browser transport", async () => {
      const sentMessages: unknown[] = [];
      Object.defineProperty(window, "document", {
        value: { title: "Original title" },
        writable: true,
        configurable: true,
      });
      const client = new BrowserClient();
      client.setSendCallback((msg) => {
        sentMessages.push(msg);
      });

      await client.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-prop-2",
        proxy_id: "__global__:document",
        operation: "set",
        member: "title",
        args: [],
        value: "Updated title",
      });

      expect(sentMessages).toContainEqual({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-prop-2",
        result: true,
        error: null,
        error_type: null,
      });
      expect(window.document.title).toBe("Updated title");

      client.disconnect();
    });

    it("sends callback proxy requests and resolves them through the browser transport", async () => {
      const sentMessages: unknown[] = [];
      registerProxyTarget("invokeCallback", {
        async run(callback: (value: number) => Promise<number>) {
          return await callback(5);
        },
      });
      const client = new BrowserClient();
      client.setSendCallback((msg) => {
        sentMessages.push(msg);
      });

      const requestPromise = client.handleMessage({
        type: MessageType.PROXY_REQUEST,
        request_id: "req-callback-1",
        proxy_id: "invokeCallback",
        operation: "call",
        member: "run",
        args: [{ __proxy_callback__: "callback-1" }],
      });

      await vi.waitFor(() => expect(sentMessages).toHaveLength(1));
      const callbackRequest = sentMessages[0] as {
        type: string;
        request_id: string;
        proxy_id: string;
      };
      expect(callbackRequest.type).toBe(MessageType.PROXY_REQUEST);
      expect(callbackRequest.proxy_id).toBe("__callback__:callback-1");

      await client.handleMessage({
        type: MessageType.PROXY_RESPONSE,
        request_id: callbackRequest.request_id,
        result: 10,
        error: null,
        error_type: null,
      });
      await requestPromise;

      expect(sentMessages).toContainEqual({
        type: MessageType.PROXY_RESPONSE,
        request_id: "req-callback-1",
        result: 10,
        error: null,
        error_type: null,
      });

      client.disconnect();
    });
  });
});
