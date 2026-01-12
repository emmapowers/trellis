/**
 * Tests for the mount() API shadow DOM functionality.
 *
 * The mount() function creates a shadow DOM for CSS isolation and
 * sets up event forwarding for React Aria compatibility.
 *
 * These tests focus on the shadow DOM infrastructure without loading
 * the full TrellisApp component tree.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import React, { act } from "react";
import { createRoot } from "react-dom/client";

// Test the shadow DOM utilities directly
import {
  createShadowRoot,
  setupEventForwarding,
  injectStyles,
} from "@trellis/trellis-browser/client/src/shadow-dom";

describe("Shadow DOM utilities", () => {
  let container: HTMLDivElement;

  beforeEach(() => {
    container = document.createElement("div");
    document.body.appendChild(container);
  });

  afterEach(() => {
    container.remove();
  });

  describe("createShadowRoot()", () => {
    it("creates an open shadow root on the container", () => {
      const { shadowRoot } = createShadowRoot(container);

      expect(shadowRoot).not.toBeNull();
      expect(shadowRoot.mode).toBe("open");
      expect(container.shadowRoot).toBe(shadowRoot);
    });

    it("creates a .trellis-root element inside shadow DOM", () => {
      const { mountPoint } = createShadowRoot(container);

      expect(mountPoint).not.toBeNull();
      expect(mountPoint.className).toBe("trellis-root");
      expect(container.shadowRoot?.contains(mountPoint)).toBe(true);
    });

    it("sets light theme by default", () => {
      const { mountPoint } = createShadowRoot(container);

      expect(mountPoint.dataset.theme).toBe("light");
    });

    it("sets dark theme when specified", () => {
      const { mountPoint } = createShadowRoot(container, { theme: "dark" });

      expect(mountPoint.dataset.theme).toBe("dark");
    });
  });

  describe("setupEventForwarding()", () => {
    it("forwards mouseup events from shadow DOM to document", () => {
      const shadow = container.attachShadow({ mode: "open" });
      const inner = document.createElement("div");
      shadow.appendChild(inner);

      const cleanup = setupEventForwarding(shadow);
      const documentHandler = vi.fn();
      document.addEventListener("mouseup", documentHandler);

      const event = new MouseEvent("mouseup", { bubbles: true });
      inner.dispatchEvent(event);

      expect(documentHandler).toHaveBeenCalled();

      document.removeEventListener("mouseup", documentHandler);
      cleanup();
    });

    it("forwards pointerup events from shadow DOM to document", () => {
      const shadow = container.attachShadow({ mode: "open" });
      const inner = document.createElement("div");
      shadow.appendChild(inner);

      const cleanup = setupEventForwarding(shadow);
      const documentHandler = vi.fn();
      document.addEventListener("pointerup", documentHandler);

      const event = new PointerEvent("pointerup", { bubbles: true });
      inner.dispatchEvent(event);

      expect(documentHandler).toHaveBeenCalled();

      document.removeEventListener("pointerup", documentHandler);
      cleanup();
    });

    it("forwards keydown events from shadow DOM to document", () => {
      const shadow = container.attachShadow({ mode: "open" });
      const inner = document.createElement("div");
      shadow.appendChild(inner);

      const cleanup = setupEventForwarding(shadow);
      const documentHandler = vi.fn();
      document.addEventListener("keydown", documentHandler);

      const event = new KeyboardEvent("keydown", { bubbles: true, key: "Enter" });
      inner.dispatchEvent(event);

      expect(documentHandler).toHaveBeenCalled();

      document.removeEventListener("keydown", documentHandler);
      cleanup();
    });

    it("cleanup removes event listeners", () => {
      const shadow = container.attachShadow({ mode: "open" });
      const inner = document.createElement("div");
      shadow.appendChild(inner);

      const cleanup = setupEventForwarding(shadow);
      cleanup();

      const documentHandler = vi.fn();
      document.addEventListener("mouseup", documentHandler);

      const event = new MouseEvent("mouseup", { bubbles: true });
      inner.dispatchEvent(event);

      // Event should NOT be forwarded after cleanup
      expect(documentHandler).not.toHaveBeenCalled();

      document.removeEventListener("mouseup", documentHandler);
    });
  });

  describe("injectStyles()", () => {
    it("injects a style element into shadow DOM", () => {
      const shadow = container.attachShadow({ mode: "open" });
      const css = ".test { color: red; }";

      injectStyles(shadow, css);

      const style = shadow.querySelector("style");
      expect(style).not.toBeNull();
      expect(style?.textContent).toBe(css);
    });

    it("can inject multiple style elements", () => {
      const shadow = container.attachShadow({ mode: "open" });

      injectStyles(shadow, ".a { color: red; }");
      injectStyles(shadow, ".b { color: blue; }");

      const styles = shadow.querySelectorAll("style");
      expect(styles.length).toBe(2);
    });
  });
});

describe("Shadow DOM React mounting", () => {
  let container: HTMLDivElement;

  beforeEach(() => {
    container = document.createElement("div");
    document.body.appendChild(container);
  });

  afterEach(() => {
    container.remove();
  });

  it("React components render inside shadow DOM", () => {
    const { shadowRoot, mountPoint } = createShadowRoot(container);

    const root = createRoot(mountPoint);
    act(() => {
      root.render(<div data-testid="test">Hello Shadow DOM</div>);
    });

    const testEl = shadowRoot.querySelector("[data-testid='test']");
    expect(testEl).not.toBeNull();
    expect(testEl?.textContent).toBe("Hello Shadow DOM");

    act(() => {
      root.unmount();
    });
  });

  it("theme can be updated on mount point", () => {
    const { mountPoint } = createShadowRoot(container, { theme: "light" });

    expect(mountPoint.dataset.theme).toBe("light");

    mountPoint.dataset.theme = "dark";
    expect(mountPoint.dataset.theme).toBe("dark");
  });
});
