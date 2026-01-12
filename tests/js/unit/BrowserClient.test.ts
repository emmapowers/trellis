import { describe, it, expect, beforeEach, afterEach, vi, Mock } from "vitest";
import { BrowserClient } from "@browser/BrowserClient";
import { RoutingMode } from "@common/RouterManager";

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
    vi.clearAllMocks();
  });

  describe("routing mode", () => {
    it("defaults to HashUrl mode (uses window.location.hash)", () => {
      const client = new BrowserClient();

      // Set up send callback so navigation works
      client.setSendCallback(() => {});

      // In HashUrl mode, pushState should update hash, not call pushState
      // @ts-expect-error - accessing private property for testing
      client.routerManager.pushState("/users");

      expect(mockPushState).not.toHaveBeenCalled();
      expect(window.location.hash).toBe("#/users");

      client.disconnect();
    });

    it("uses Standard mode when routingMode=Standard", () => {
      const client = new BrowserClient({}, undefined, {
        routingMode: RoutingMode.Standard,
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

    it("uses Embedded mode when routingMode=Embedded", () => {
      const client = new BrowserClient({}, undefined, {
        routingMode: RoutingMode.Embedded,
      });

      // Set up send callback so navigation works
      client.setSendCallback(() => {});

      // In Embedded mode, pushState should NOT call window.history.pushState
      // @ts-expect-error - accessing private property for testing
      client.routerManager.pushState("/users");

      expect(mockPushState).not.toHaveBeenCalled();
      expect(window.location.hash).toBe(""); // Hash should not be updated either

      client.disconnect();
    });

    it("reads initial path from hash in HashUrl mode", () => {
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
});
