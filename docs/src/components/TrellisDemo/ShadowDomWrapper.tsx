/**
 * ShadowDomWrapper - Renders children in a shadow DOM for style isolation.
 *
 * This prevents Docusaurus/Infima styles from leaking into Trellis components.
 */

import React, { useRef, useEffect, useState } from "react";
import { createPortal } from "react-dom";

// Trellis theme CSS inlined for shadow DOM injection
// This is a copy of theme.css - keep in sync!
const THEME_CSS = `
.trellis-root,
.trellis-root[data-theme="light"] {
  --trellis-bg-page: #f8fafc;
  --trellis-bg-surface: #ffffff;
  --trellis-bg-surface-raised: #f8fafc;
  --trellis-bg-surface-hover: #f1f5f9;
  --trellis-bg-input: #ffffff;
  --trellis-border-default: #e2e8f0;
  --trellis-border-subtle: #f1f5f9;
  --trellis-border-strong: #cbd5e1;
  --trellis-border-focus: #6366f1;
  --trellis-text-primary: #0f172a;
  --trellis-text-secondary: #64748b;
  --trellis-text-muted: #94a3b8;
  --trellis-text-inverse: #ffffff;
  --trellis-success: #16a34a;
  --trellis-success-bg: #f0fdf4;
  --trellis-success-border: #bbf7d0;
  --trellis-error: #dc2626;
  --trellis-error-bg: #fef2f2;
  --trellis-error-border: #fecaca;
  --trellis-error-hover: #b91c1c;
  --trellis-warning: #d97706;
  --trellis-warning-bg: #fffbeb;
  --trellis-warning-border: #fde68a;
  --trellis-info: #2563eb;
  --trellis-info-bg: #eff6ff;
  --trellis-info-border: #bfdbfe;
  --trellis-accent-primary: #6366f1;
  --trellis-accent-primary-hover: #4f46e5;
  --trellis-accent-primary-active: #4338ca;
  --trellis-accent-subtle: #eef2ff;
  --trellis-neutral-50: #f8fafc;
  --trellis-neutral-100: #f1f5f9;
  --trellis-neutral-200: #e2e8f0;
  --trellis-neutral-300: #cbd5e1;
  --trellis-neutral-400: #94a3b8;
  --trellis-neutral-500: #64748b;
  --trellis-neutral-600: #475569;
  --trellis-neutral-700: #334155;
  --trellis-neutral-800: #1e293b;
  --trellis-neutral-900: #0f172a;
  --trellis-shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --trellis-shadow-md: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1);
  --trellis-shadow-lg: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
  --trellis-focus-ring-color: #6366f1;
}

.trellis-root[data-theme="dark"] {
  --trellis-bg-page: #0f172a;
  --trellis-bg-surface: #1e293b;
  --trellis-bg-surface-raised: #334155;
  --trellis-bg-surface-hover: #475569;
  --trellis-bg-input: #1e293b;
  --trellis-border-default: #334155;
  --trellis-border-subtle: #1e293b;
  --trellis-border-strong: #475569;
  --trellis-border-focus: #818cf8;
  --trellis-text-primary: #f8fafc;
  --trellis-text-secondary: #94a3b8;
  --trellis-text-muted: #64748b;
  --trellis-text-inverse: #0f172a;
  --trellis-success: #22c55e;
  --trellis-success-bg: #052e16;
  --trellis-success-border: #166534;
  --trellis-error: #ef4444;
  --trellis-error-bg: #450a0a;
  --trellis-error-border: #991b1b;
  --trellis-error-hover: #dc2626;
  --trellis-warning: #f59e0b;
  --trellis-warning-bg: #451a03;
  --trellis-warning-border: #92400e;
  --trellis-info: #3b82f6;
  --trellis-info-bg: #172554;
  --trellis-info-border: #1e40af;
  --trellis-accent-primary: #818cf8;
  --trellis-accent-primary-hover: #6366f1;
  --trellis-accent-primary-active: #4f46e5;
  --trellis-accent-subtle: #1e1b4b;
  --trellis-neutral-50: #0f172a;
  --trellis-neutral-100: #1e293b;
  --trellis-neutral-200: #334155;
  --trellis-neutral-300: #475569;
  --trellis-neutral-400: #64748b;
  --trellis-neutral-500: #94a3b8;
  --trellis-neutral-600: #cbd5e1;
  --trellis-neutral-700: #e2e8f0;
  --trellis-neutral-800: #f1f5f9;
  --trellis-neutral-900: #f8fafc;
  --trellis-shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
  --trellis-shadow-md: 0 1px 3px 0 rgba(0, 0, 0, 0.4), 0 1px 2px -1px rgba(0, 0, 0, 0.4);
  --trellis-shadow-lg: 0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -2px rgba(0, 0, 0, 0.4);
  --trellis-focus-ring-color: #818cf8;
}

.trellis-root {
  box-sizing: border-box;
  background: var(--trellis-bg-page);
  color: var(--trellis-text-primary);
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  line-height: 1.5;
}

.trellis-root *,
.trellis-root *::before,
.trellis-root *::after {
  box-sizing: border-box;
}
`;

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

    const forwardEvent = (e: Event) => {
      // Stop the original event from reaching document with retargeted target.
      // Composed events bubble from shadow DOM to light DOM, but the target gets
      // retargeted to the shadow host. React Aria would see the wrong target and
      // fail its containment check. We stop the original and dispatch a corrected one.
      e.stopPropagation();

      // Re-dispatch the event on document so React Aria's global listeners receive it
      const clonedEvent = new (e.constructor as typeof Event)(e.type, e);

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

    // Get the container for rendering
    const container = shadow.querySelector(".trellis-root") as HTMLElement;
    setShadowContainer(container);

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
