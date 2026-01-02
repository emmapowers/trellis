/**
 * ShadowDomWrapper - Renders children in a shadow DOM for style isolation.
 *
 * This prevents Docusaurus/Infima styles from leaking into Trellis components.
 */

import React, { useRef, useEffect, useState } from "react";
import { createPortal } from "react-dom";

// Import the canonical theme CSS from the source
// The ?raw suffix tells the bundler to import as a string
// @ts-expect-error - raw import
import THEME_CSS from "../../../../src/trellis/platforms/common/client/src/theme.css?raw";

interface ShadowDomWrapperProps {
  children: React.ReactNode;
  className?: string;
  /** Initial theme to apply immediately when container is created */
  initialTheme?: "light" | "dark";
}

export function ShadowDomWrapper({
  children,
  className,
  initialTheme,
}: ShadowDomWrapperProps): React.ReactElement {
  const hostRef = useRef<HTMLDivElement>(null);
  const [shadowContainer, setShadowContainer] = useState<HTMLElement | null>(
    null
  );

  // Create shadow root and container on mount
  useEffect(() => {
    if (!hostRef.current) return;

    // Create shadow root if it doesn't exist
    let shadow = hostRef.current.shadowRoot;
    const isNewShadow = !shadow;

    if (!shadow) {
      shadow = hostRef.current.attachShadow({ mode: "open" });

      // Inject theme CSS
      const style = document.createElement("style");
      style.textContent = THEME_CSS;
      shadow.appendChild(style);

      // Create the trellis-root container
      const container = document.createElement("div");
      container.className = "trellis-root";
      shadow.appendChild(container);
    }

    // Get the container for rendering
    const container = shadow.querySelector(".trellis-root") as HTMLElement;
    setShadowContainer(container);

    // Skip listener setup if shadow root already existed (handles remount)
    // This prevents duplicate listeners in StrictMode or when component remounts
    if (!isNewShadow) {
      return; // No cleanup needed since we didn't add listeners
    }

    // Event forwarding for React Aria compatibility.
    // React Aria's usePress registers global event listeners on document for
    // mouseup/pointerup to complete press interactions. Events from shadow DOM
    // don't bubble to document, so we re-dispatch them.
    // See: https://github.com/adobe/react-spectrum/issues/2040
    //
    // Critical: React Aria checks if event.target is contained within the pressed
    // element. We must preserve the original target, which requires overriding
    // the target getter since it's normally set by dispatchEvent.
    const eventsToForward = [
      "mouseup",
      "pointerup",
      "pointercancel",
      "keydown",
      "keyup",
    ] as const;

    // Clone events properly with their specific constructors
    // Guard against PointerEvent not being defined (e.g., in jsdom)
    const cloneEvent = (e: Event): Event => {
      const base = {
        bubbles: e.bubbles,
        cancelable: e.cancelable,
        composed: e.composed,
      };

      if (typeof PointerEvent !== "undefined" && e instanceof PointerEvent) {
        return new PointerEvent(e.type, {
          ...base,
          clientX: e.clientX,
          clientY: e.clientY,
          screenX: e.screenX,
          screenY: e.screenY,
          button: e.button,
          buttons: e.buttons,
          pointerId: e.pointerId,
          pointerType: e.pointerType,
          isPrimary: e.isPrimary,
          pressure: e.pressure,
          ctrlKey: e.ctrlKey,
          shiftKey: e.shiftKey,
          altKey: e.altKey,
          metaKey: e.metaKey,
        });
      }
      if (e instanceof MouseEvent) {
        return new MouseEvent(e.type, {
          ...base,
          clientX: e.clientX,
          clientY: e.clientY,
          screenX: e.screenX,
          screenY: e.screenY,
          button: e.button,
          buttons: e.buttons,
          ctrlKey: e.ctrlKey,
          shiftKey: e.shiftKey,
          altKey: e.altKey,
          metaKey: e.metaKey,
        });
      }
      if (e instanceof KeyboardEvent) {
        return new KeyboardEvent(e.type, {
          ...base,
          key: e.key,
          code: e.code,
          location: e.location,
          repeat: e.repeat,
          ctrlKey: e.ctrlKey,
          shiftKey: e.shiftKey,
          altKey: e.altKey,
          metaKey: e.metaKey,
        });
      }
      return new Event(e.type, base);
    };

    const forwardEvent = (e: Event) => {
      // Stop the original event from reaching document with retargeted target.
      // Composed events bubble from shadow DOM to light DOM, but the target gets
      // retargeted to the shadow host. React Aria would see the wrong target and
      // fail its containment check. We stop the original and dispatch a corrected one.
      e.stopPropagation();

      // Clone the event with proper constructor for its type
      const clonedEvent = cloneEvent(e);

      // Preserve the original target so React Aria's containment check works
      const originalTarget = e.target;
      Object.defineProperty(clonedEvent, "target", {
        get: () => originalTarget,
        configurable: true,
      });

      document.dispatchEvent(clonedEvent);
    };

    eventsToForward.forEach((eventType) => {
      shadow!.addEventListener(eventType, forwardEvent);
    });

    return () => {
      eventsToForward.forEach((eventType) => {
        shadow!.removeEventListener(eventType, forwardEvent);
      });
    };
  }, []);

  // Keep data-theme in sync with initialTheme (host's color mode)
  // This ensures the theme stays correct even if ThemeProvider has issues
  useEffect(() => {
    if (shadowContainer && initialTheme) {
      shadowContainer.dataset.theme = initialTheme;
    }
  }, [shadowContainer, initialTheme]);

  return (
    <div ref={hostRef} className={className}>
      {shadowContainer && createPortal(children, shadowContainer)}
    </div>
  );
}
