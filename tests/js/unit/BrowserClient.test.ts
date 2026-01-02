import { describe, it, expect, beforeEach, afterEach, vi, Mock } from "vitest";
import { BrowserClient } from "@browser/BrowserClient";

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

    // Mock location
    Object.defineProperty(window, "location", {
      value: { pathname: "/" },
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

  describe("embedded mode", () => {
    it("defaults to standalone mode (uses window.history)", () => {
      const client = new BrowserClient();

      // Set up send callback so navigation works
      client.setSendCallback(() => {});

      // In standalone mode, pushState should call window.history.pushState
      // We need to trigger a history push via the handler callback
      // The router callbacks are set up in the constructor
      // @ts-expect-error - accessing private property for testing
      client.routerManager.pushState("/users");

      expect(mockPushState).toHaveBeenCalledWith(
        { path: "/users" },
        "",
        "/users"
      );

      client.disconnect();
    });

    it("uses embedded mode when embedded=true (does not use window.history)", () => {
      const client = new BrowserClient({}, undefined, { embedded: true });

      // Set up send callback so navigation works
      client.setSendCallback(() => {});

      // In embedded mode, pushState should NOT call window.history.pushState
      // @ts-expect-error - accessing private property for testing
      client.routerManager.pushState("/users");

      expect(mockPushState).not.toHaveBeenCalled();

      client.disconnect();
    });
  });
});
