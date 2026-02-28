import { openUrl } from "@tauri-apps/plugin-opener";

function isRouterHandled(anchor: HTMLAnchorElement): boolean {
  return anchor.dataset.trellisRouterLink === "true";
}

function toAnchor(target: EventTarget | null): HTMLAnchorElement | null {
  if (target instanceof HTMLAnchorElement && target.hasAttribute("href")) {
    return target;
  }
  if (!(target instanceof Element)) {
    return null;
  }
  const anchor = target.closest("a[href]");
  return anchor instanceof HTMLAnchorElement ? anchor : null;
}

function getAnchorFromEvent(event: MouseEvent): HTMLAnchorElement | null {
  const directAnchor = toAnchor(event.target);
  if (directAnchor !== null) {
    return directAnchor;
  }
  for (const pathTarget of event.composedPath()) {
    const pathAnchor = toAnchor(pathTarget);
    if (pathAnchor !== null) {
      return pathAnchor;
    }
  }
  return null;
}

function isExternalUrl(href: string): boolean {
  const resolved = new URL(href, window.location.href);
  return resolved.origin !== window.location.origin;
}

function isModifiedClick(event: MouseEvent): boolean {
  return event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0;
}

export function installExternalLinkDelegation(): () => void {
  const handleClick = (event: MouseEvent): void => {
    if (event.defaultPrevented) {
      return;
    }

    const anchor = getAnchorFromEvent(event);
    if (anchor === null) {
      return;
    }

    if (isRouterHandled(anchor)) {
      return;
    }

    const href = anchor.getAttribute("href");
    if (!href || href.startsWith("#")) {
      return;
    }

    if (!isExternalUrl(href)) {
      return;
    }

    // Modifier clicks and target=_blank are handled by the opener plugin
    if (isModifiedClick(event) || anchor.target === "_blank") {
      return;
    }

    const resolvedUrl = new URL(href, window.location.href).toString();
    event.preventDefault();
    void openUrl(resolvedUrl).catch((error) => {
      console.error("Failed to open external link:", error);
    });
  };

  document.addEventListener("click", handleClick, true);
  return () => {
    document.removeEventListener("click", handleClick, true);
  };
}
