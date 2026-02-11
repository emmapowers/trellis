/**
 * Browser client library entry point.
 *
 * This library bundles its own React instance and provides a mount() API
 * for embedding TrellisApp in any web page without React version conflicts.
 *
 * The mount() function creates a shadow DOM for CSS isolation and sets up
 * event forwarding for React Aria compatibility.
 *
 * Usage:
 *   import { mount } from "@anthropic/trellis";
 *
 *   const instance = mount(container, {
 *     routingMode: "hash",
 *   });
 *
 *   // Update props
 *   instance.update({ themeMode: "dark" });
 *
 *   // Clean up
 *   instance.unmount();
 */

import { initRegistry } from "@trellis/_registry";
import React from "react";
import { createRoot, type Root } from "react-dom/client";
import { TrellisApp } from "@trellis/trellis-browser/client/src/TrellisApp";
import type { TrellisAppProps } from "@trellis/trellis-browser/client/src/TrellisApp";
import { createShadowRoot, setupEventForwarding } from "@trellis/trellis-browser/client/src/shadow-dom";

// Import CSS so esbuild bundles it into index.css
import "@trellis/trellis-core/client/src/theme.css";

// Re-export types for consumers
export type { TrellisAppProps };

/**
 * Options for the mount() function.
 */
export interface MountOptions extends TrellisAppProps {
  /**
   * URL to the Trellis CSS file. If not provided, the CSS must be
   * loaded separately or the component will be unstyled.
   *
   * Example: "/trellis/index.css" or "https://cdn.example.com/trellis.css"
   */
  cssUrl?: string;
}

/**
 * Handle to a mounted TrellisApp instance.
 */
export interface TrellisInstance {
  /** Update props on the mounted instance */
  update(props: Partial<TrellisAppProps>): void;
  /** Unmount and clean up the instance */
  unmount(): void;
}

/**
 * Inject CSS into shadow DOM via a link element.
 */
function injectStylesheet(shadowRoot: ShadowRoot, url: string): void {
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = url;
  shadowRoot.appendChild(link);
}

/**
 * Mount a TrellisApp into a container element.
 *
 * This function creates a shadow DOM for CSS isolation and uses the library's
 * bundled React instance, avoiding conflicts with any React version or styles
 * the host application might use.
 *
 * @param container - DOM element to render into
 * @param options - Props for TrellisApp plus mount options
 * @returns Handle for updating props or unmounting
 */
export function mount(
  container: HTMLElement,
  options: MountOptions
): TrellisInstance {
  // Initialize widget registry before rendering
  initRegistry();

  const { cssUrl, ...props } = options;

  // Create shadow DOM for isolation
  // Resolve "system" theme to actual theme based on user preference
  const resolveTheme = (mode: "light" | "dark" | "system" | undefined): "light" | "dark" => {
    if (mode === "system") {
      return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    return mode ?? "light";
  };
  const theme = resolveTheme(props.themeMode);
  const { shadowRoot, mountPoint } = createShadowRoot(container, { theme });

  // Inject CSS into shadow DOM if URL provided
  if (cssUrl) {
    injectStylesheet(shadowRoot, cssUrl);
  }

  // Set up event forwarding for React Aria
  const cleanupEvents = setupEventForwarding(shadowRoot);

  // Create React root in shadow DOM
  const root: Root = createRoot(mountPoint);
  let currentProps = props;

  const render = () => {
    root.render(
      React.createElement(TrellisApp, { ...currentProps })
    );
  };

  render();

  return {
    update(newProps: Partial<TrellisAppProps>) {
      // Update theme on mount point
      if (newProps.themeMode) {
        mountPoint.dataset.theme = resolveTheme(newProps.themeMode);
      }
      currentProps = { ...currentProps, ...newProps };
      render();
    },
    unmount() {
      cleanupEvents();
      root.unmount();
    },
  };
}

// Also export the component for advanced use cases where consumers
// want to use their own React (at their own risk for version conflicts)
export { TrellisApp };

// Export shadow DOM utilities for advanced use cases
export { createShadowRoot, setupEventForwarding, injectStyles } from "@trellis/trellis-browser/client/src/shadow-dom";
export type { CreateShadowRootOptions, ShadowRootResult } from "@trellis/trellis-browser/client/src/shadow-dom";
