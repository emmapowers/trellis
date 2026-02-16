import { describe, it, expect, vi } from "vitest";
import { installExternalLinkDelegation } from "../../../../src/trellis/platforms/desktop/client/src/externalLinks";

describe("desktop external link delegation", () => {
  it("opens non-router links in external browser", () => {
    const openExternal = vi.fn().mockResolvedValue(undefined);
    const uninstall = installExternalLinkDelegation(openExternal);

    const anchor = document.createElement("a");
    anchor.href = "https://example.com";
    anchor.textContent = "external";
    document.body.appendChild(anchor);

    const event = new MouseEvent("click", { bubbles: true, cancelable: true, button: 0 });
    anchor.dispatchEvent(event);

    expect(openExternal).toHaveBeenCalledWith("https://example.com/");
    expect(event.defaultPrevented).toBe(true);

    uninstall();
    anchor.remove();
  });

  it("does not intercept router-handled links", () => {
    const openExternal = vi.fn().mockResolvedValue(undefined);
    const uninstall = installExternalLinkDelegation(openExternal);

    const anchor = document.createElement("a");
    anchor.href = "#in-app";
    anchor.setAttribute("data-trellis-router-link", "true");
    document.body.appendChild(anchor);

    const event = new MouseEvent("click", { bubbles: true, cancelable: true, button: 0 });
    anchor.dispatchEvent(event);

    expect(openExternal).not.toHaveBeenCalled();
    expect(event.defaultPrevented).toBe(false);

    uninstall();
    anchor.remove();
  });

  it("does not intercept modified clicks", () => {
    const openExternal = vi.fn().mockResolvedValue(undefined);
    const uninstall = installExternalLinkDelegation(openExternal);

    const anchor = document.createElement("a");
    anchor.href = "#external";
    document.body.appendChild(anchor);

    const event = new MouseEvent("click", {
      bubbles: true,
      cancelable: true,
      button: 0,
      ctrlKey: true,
    });
    anchor.dispatchEvent(event);

    expect(openExternal).not.toHaveBeenCalled();
    expect(event.defaultPrevented).toBe(false);

    uninstall();
    anchor.remove();
  });
});
