import { describe, it, expect, beforeEach, afterEach, vi, Mock } from "vitest";
import { RouterManager, RoutingMode } from "@common/RouterManager";
import { MessageType, UrlChangedMessage } from "@common/types";

describe("RouterManager", () => {
  let sendMessage: Mock;
  let originalHistory: History;
  let originalLocation: Location;

  // Mock window.history and window.location
  beforeEach(() => {
    sendMessage = vi.fn();

    // Store originals
    originalHistory = window.history;
    originalLocation = window.location;

    // Mock history
    const mockHistory = {
      pushState: vi.fn(),
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

  describe("url mode", () => {
    let manager: RouterManager;

    beforeEach(() => {
      manager = new RouterManager({ mode: RoutingMode.Url, sendMessage });
    });

    afterEach(() => {
      manager.destroy();
    });

    describe("pushState", () => {
      it("calls window.history.pushState with path", () => {
        manager.pushState("/users");

        expect(window.history.pushState).toHaveBeenCalledWith(
          { path: "/users" },
          "",
          "/users"
        );
      });

      it("updates internal path", () => {
        manager.pushState("/users");

        expect(manager.getCurrentPath()).toBe("/users");
      });
    });

    describe("back", () => {
      it("calls window.history.back", () => {
        manager.back();

        expect(window.history.back).toHaveBeenCalled();
      });
    });

    describe("forward", () => {
      it("calls window.history.forward", () => {
        manager.forward();

        expect(window.history.forward).toHaveBeenCalled();
      });
    });

    describe("popstate handling", () => {
      it("sends UrlChanged message on popstate", () => {
        // Simulate popstate event
        const event = new PopStateEvent("popstate", {
          state: { path: "/about" },
        });
        Object.defineProperty(window, "location", {
          value: { pathname: "/about" },
          writable: true,
          configurable: true,
        });
        window.dispatchEvent(event);

        expect(sendMessage).toHaveBeenCalledWith({
          type: MessageType.URL_CHANGED,
          path: "/about",
        } satisfies UrlChangedMessage);
      });

      it("updates internal path on popstate", () => {
        const event = new PopStateEvent("popstate", {
          state: { path: "/about" },
        });
        Object.defineProperty(window, "location", {
          value: { pathname: "/about" },
          writable: true,
          configurable: true,
        });
        window.dispatchEvent(event);

        expect(manager.getCurrentPath()).toBe("/about");
      });
    });

    describe("initial path", () => {
      it("reads initial path from window.location", () => {
        Object.defineProperty(window, "location", {
          value: { pathname: "/initial" },
          writable: true,
          configurable: true,
        });

        const newManager = new RouterManager({
          mode: RoutingMode.Url,
          sendMessage,
        });
        expect(newManager.getCurrentPath()).toBe("/initial");
        newManager.destroy();
      });
    });
  });

  describe("hidden mode", () => {
    let manager: RouterManager;

    beforeEach(() => {
      manager = new RouterManager({ mode: RoutingMode.Hidden, sendMessage });
    });

    afterEach(() => {
      manager.destroy();
    });

    describe("pushState", () => {
      it("does not call window.history.pushState", () => {
        manager.pushState("/users");

        expect(window.history.pushState).not.toHaveBeenCalled();
      });

      it("updates internal path", () => {
        manager.pushState("/users");

        expect(manager.getCurrentPath()).toBe("/users");
      });

      it("maintains internal history", () => {
        manager.pushState("/users");
        manager.pushState("/users/123");

        expect(manager.getHistoryLength()).toBe(3); // / + /users + /users/123
      });
    });

    describe("back", () => {
      it("does not call window.history.back", () => {
        manager.pushState("/users");
        manager.back();

        expect(window.history.back).not.toHaveBeenCalled();
      });

      it("navigates back in internal history", () => {
        manager.pushState("/users");
        manager.pushState("/users/123");
        manager.back();

        expect(manager.getCurrentPath()).toBe("/users");
      });

      it("sends UrlChanged message", () => {
        manager.pushState("/users");
        manager.pushState("/users/123");
        manager.back();

        expect(sendMessage).toHaveBeenCalledWith({
          type: MessageType.URL_CHANGED,
          path: "/users",
        } satisfies UrlChangedMessage);
      });

      it("does nothing if at start of history", () => {
        manager.back();

        expect(manager.getCurrentPath()).toBe("/");
        expect(sendMessage).not.toHaveBeenCalled();
      });
    });

    describe("forward", () => {
      it("does not call window.history.forward", () => {
        manager.pushState("/users");
        manager.back();
        manager.forward();

        expect(window.history.forward).not.toHaveBeenCalled();
      });

      it("navigates forward in internal history", () => {
        manager.pushState("/users");
        manager.back();
        manager.forward();

        expect(manager.getCurrentPath()).toBe("/users");
      });

      it("sends UrlChanged message", () => {
        manager.pushState("/users");
        manager.back();
        sendMessage.mockClear();
        manager.forward();

        expect(sendMessage).toHaveBeenCalledWith({
          type: MessageType.URL_CHANGED,
          path: "/users",
        } satisfies UrlChangedMessage);
      });

      it("does nothing if at end of history", () => {
        manager.pushState("/users");
        manager.forward();

        // No additional message should be sent
        expect(sendMessage).not.toHaveBeenCalled();
      });
    });

    describe("popstate handling", () => {
      it("does not listen to popstate events", () => {
        const event = new PopStateEvent("popstate", {
          state: { path: "/about" },
        });
        Object.defineProperty(window, "location", {
          value: { pathname: "/about" },
          writable: true,
          configurable: true,
        });
        window.dispatchEvent(event);

        // Internal path should remain unchanged
        expect(manager.getCurrentPath()).toBe("/");
        expect(sendMessage).not.toHaveBeenCalled();
      });
    });

    describe("initial path", () => {
      it("uses provided initial path", () => {
        const newManager = new RouterManager({
          mode: RoutingMode.Hidden,
          sendMessage,
          initialPath: "/start",
        });
        expect(newManager.getCurrentPath()).toBe("/start");
        newManager.destroy();
      });

      it("defaults to / if no initial path provided", () => {
        expect(manager.getCurrentPath()).toBe("/");
      });
    });

    describe("history truncation on push after back", () => {
      it("truncates forward history when pushing after going back", () => {
        manager.pushState("/a");
        manager.pushState("/b");
        manager.pushState("/c");
        manager.back(); // at /b
        manager.back(); // at /a
        manager.pushState("/d"); // should truncate /b and /c

        expect(manager.getHistoryLength()).toBe(3); // / + /a + /d
        manager.back();
        expect(manager.getCurrentPath()).toBe("/a");
      });
    });
  });

  describe("destroy", () => {
    it("removes popstate listener in url mode", () => {
      const manager = new RouterManager({
        mode: RoutingMode.Url,
        sendMessage,
      });
      manager.destroy();

      // After destroy, popstate should not trigger sendMessage
      const event = new PopStateEvent("popstate", {
        state: { path: "/about" },
      });
      Object.defineProperty(window, "location", {
        value: { pathname: "/about" },
        writable: true,
        configurable: true,
      });
      window.dispatchEvent(event);

      expect(sendMessage).not.toHaveBeenCalled();
    });
  });

  describe("hash URL mode", () => {
    let manager: RouterManager;

    beforeEach(() => {
      // Set up hash in location mock
      Object.defineProperty(window, "location", {
        value: { pathname: "/", hash: "" },
        writable: true,
        configurable: true,
      });
    });

    afterEach(() => {
      manager?.destroy();
    });

    describe("initial path", () => {
      it("reads initial path from window.location.hash", () => {
        Object.defineProperty(window, "location", {
          value: { pathname: "/", hash: "#/users/123" },
          writable: true,
          configurable: true,
        });

        manager = new RouterManager({
          mode: RoutingMode.Hash,
          sendMessage,
        });
        expect(manager.getCurrentPath()).toBe("/users/123");
      });

      it("defaults to / when hash is empty", () => {
        Object.defineProperty(window, "location", {
          value: { pathname: "/", hash: "" },
          writable: true,
          configurable: true,
        });

        manager = new RouterManager({
          mode: RoutingMode.Hash,
          sendMessage,
        });
        expect(manager.getCurrentPath()).toBe("/");
      });

      it("defaults to / when hash is just #", () => {
        Object.defineProperty(window, "location", {
          value: { pathname: "/", hash: "#" },
          writable: true,
          configurable: true,
        });

        manager = new RouterManager({
          mode: RoutingMode.Hash,
          sendMessage,
        });
        expect(manager.getCurrentPath()).toBe("/");
      });
    });

    describe("pushState", () => {
      beforeEach(() => {
        manager = new RouterManager({
          mode: RoutingMode.Hash,
          sendMessage,
        });
      });

      it("updates window.location.hash", () => {
        manager.pushState("/users");

        expect(window.location.hash).toBe("#/users");
      });

      it("does not call window.history.pushState", () => {
        manager.pushState("/users");

        expect(window.history.pushState).not.toHaveBeenCalled();
      });

      it("updates internal path", () => {
        manager.pushState("/users");

        expect(manager.getCurrentPath()).toBe("/users");
      });
    });

    describe("hashchange handling", () => {
      beforeEach(() => {
        manager = new RouterManager({
          mode: RoutingMode.Hash,
          sendMessage,
        });
      });

      it("sends UrlChanged message on hashchange", () => {
        // Simulate hashchange event
        Object.defineProperty(window, "location", {
          value: { pathname: "/", hash: "#/about" },
          writable: true,
          configurable: true,
        });
        window.dispatchEvent(new HashChangeEvent("hashchange"));

        expect(sendMessage).toHaveBeenCalledWith({
          type: MessageType.URL_CHANGED,
          path: "/about",
        } satisfies UrlChangedMessage);
      });

      it("updates internal path on hashchange", () => {
        Object.defineProperty(window, "location", {
          value: { pathname: "/", hash: "#/about" },
          writable: true,
          configurable: true,
        });
        window.dispatchEvent(new HashChangeEvent("hashchange"));

        expect(manager.getCurrentPath()).toBe("/about");
      });

      it("does not respond to popstate events", () => {
        const event = new PopStateEvent("popstate", {
          state: { path: "/about" },
        });
        Object.defineProperty(window, "location", {
          value: { pathname: "/about", hash: "" },
          writable: true,
          configurable: true,
        });
        window.dispatchEvent(event);

        // Should not send message from popstate
        expect(sendMessage).not.toHaveBeenCalled();
      });
    });

    describe("back and forward", () => {
      beforeEach(() => {
        manager = new RouterManager({
          mode: RoutingMode.Hash,
          sendMessage,
        });
      });

      it("calls window.history.back for back()", () => {
        manager.back();

        expect(window.history.back).toHaveBeenCalled();
      });

      it("calls window.history.forward for forward()", () => {
        manager.forward();

        expect(window.history.forward).toHaveBeenCalled();
      });
    });

    describe("destroy", () => {
      it("removes hashchange listener", () => {
        manager = new RouterManager({
          mode: RoutingMode.Hash,
          sendMessage,
        });
        manager.destroy();

        // After destroy, hashchange should not trigger sendMessage
        Object.defineProperty(window, "location", {
          value: { pathname: "/", hash: "#/about" },
          writable: true,
          configurable: true,
        });
        window.dispatchEvent(new HashChangeEvent("hashchange"));

        expect(sendMessage).not.toHaveBeenCalled();
      });
    });
  });
});
