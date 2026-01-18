/**
 * Shadow DOM utilities for isolating TrellisApp CSS and handling events.
 *
 * Shadow DOM provides CSS encapsulation so Trellis styles don't leak into
 * the host page and vice versa. Event forwarding is required for React Aria
 * compatibility since it registers global listeners on document.
 */

export interface CreateShadowRootOptions {
  theme?: "light" | "dark";
}

export interface ShadowRootResult {
  shadowRoot: ShadowRoot;
  mountPoint: HTMLElement;
}

/**
 * Create a shadow root with a mount point for React.
 *
 * @param container - The host element to attach shadow DOM to
 * @param options - Configuration options
 * @returns Shadow root and mount point element
 */
export function createShadowRoot(
  container: HTMLElement,
  options: CreateShadowRootOptions = {}
): ShadowRootResult {
  const { theme = "light" } = options;

  const shadowRoot = container.attachShadow({ mode: "open" });

  // Create the mount point for React
  const mountPoint = document.createElement("div");
  mountPoint.className = "trellis-root";
  mountPoint.dataset.theme = theme;
  // Ensure mount point fills the shadow host
  mountPoint.style.width = "100%";
  mountPoint.style.height = "100%";
  shadowRoot.appendChild(mountPoint);

  return { shadowRoot, mountPoint };
}

/**
 * Set up event forwarding from shadow DOM to document.
 *
 * React Aria's usePress and other hooks register global event listeners on
 * document. Events from shadow DOM don't bubble to document by default, so
 * we re-dispatch them to ensure React Aria receives the events.
 *
 * See: https://github.com/adobe/react-spectrum/issues/2040
 *
 * @param shadowRoot - The shadow root to forward events from
 * @returns Cleanup function to remove event listeners
 */
export function setupEventForwarding(shadowRoot: ShadowRoot): () => void {
  const eventsToForward = [
    "mouseup",
    "pointerup",
    "pointercancel",
    "keydown",
    "keyup",
  ] as const;

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
    e.stopPropagation();
    const clonedEvent = cloneEvent(e);
    const originalTarget = e.target;
    Object.defineProperty(clonedEvent, "target", {
      get: () => originalTarget,
      configurable: true,
    });
    document.dispatchEvent(clonedEvent);
  };

  eventsToForward.forEach((eventType) => {
    shadowRoot.addEventListener(eventType, forwardEvent);
  });

  return () => {
    eventsToForward.forEach((eventType) => {
      shadowRoot.removeEventListener(eventType, forwardEvent);
    });
  };
}

/**
 * Inject CSS into a shadow root.
 *
 * @param shadowRoot - The shadow root to inject styles into
 * @param css - CSS string to inject
 */
export function injectStyles(shadowRoot: ShadowRoot, css: string): void {
  const style = document.createElement("style");
  style.textContent = css;
  shadowRoot.appendChild(style);
}
