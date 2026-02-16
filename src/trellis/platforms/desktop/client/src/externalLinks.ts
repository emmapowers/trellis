type OpenExternalFn = (url: string) => Promise<void>;

function isModifiedClick(event: MouseEvent): boolean {
  return event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0;
}

function isRouterHandled(anchor: HTMLAnchorElement): boolean {
  return anchor.dataset.trellisRouterLink === "true";
}

export function installExternalLinkDelegation(openExternal: OpenExternalFn): () => void {
  const handleClick = (event: MouseEvent): void => {
    if (event.defaultPrevented || isModifiedClick(event)) {
      return;
    }

    const target = event.target;
    if (!(target instanceof Element)) {
      return;
    }

    const anchor = target.closest("a[href]");
    if (!(anchor instanceof HTMLAnchorElement)) {
      return;
    }

    if (isRouterHandled(anchor)) {
      return;
    }

    const href = anchor.getAttribute("href");
    if (!href || href.startsWith("#")) {
      return;
    }

    const resolvedUrl = new URL(href, window.location.href).toString();
    event.preventDefault();
    void openExternal(resolvedUrl).catch((error) => {
      console.error("Failed to open external link:", error);
    });
  };

  document.addEventListener("click", handleClick, true);
  return () => {
    document.removeEventListener("click", handleClick, true);
  };
}
