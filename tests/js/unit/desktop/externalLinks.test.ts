import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("@tauri-apps/plugin-opener", () => ({
  openUrl: vi.fn().mockResolvedValue(undefined),
}));

import { openUrl } from "@tauri-apps/plugin-opener";
import { installExternalLinkDelegation } from "../../../../src/trellis/platforms/desktop/client/src/externalLinks";

const mockedOpenUrl = vi.mocked(openUrl);

describe("desktop external link delegation", () => {
  beforeEach(() => {
    mockedOpenUrl.mockClear();
  });

  it("opens external-origin links via opener plugin", () => {
    const uninstall = installExternalLinkDelegation();

    const anchor = document.createElement("a");
    anchor.href = "https://example.com";
    anchor.textContent = "external";
    document.body.appendChild(anchor);

    const event = new MouseEvent("click", { bubbles: true, cancelable: true, button: 0 });
    anchor.dispatchEvent(event);

    expect(mockedOpenUrl).toHaveBeenCalledWith("https://example.com/");
    expect(event.defaultPrevented).toBe(true);

    uninstall();
    anchor.remove();
  });

  it("does not intercept same-origin links", () => {
    const uninstall = installExternalLinkDelegation();

    const anchor = document.createElement("a");
    anchor.href = "/about";
    document.body.appendChild(anchor);

    const event = new MouseEvent("click", { bubbles: true, cancelable: true, button: 0 });
    anchor.dispatchEvent(event);

    expect(mockedOpenUrl).not.toHaveBeenCalled();
    expect(event.defaultPrevented).toBe(false);

    uninstall();
    anchor.remove();
  });

  it("does not intercept router-handled links", () => {
    const uninstall = installExternalLinkDelegation();

    const anchor = document.createElement("a");
    anchor.href = "https://example.com";
    anchor.setAttribute("data-trellis-router-link", "true");
    document.body.appendChild(anchor);

    const event = new MouseEvent("click", { bubbles: true, cancelable: true, button: 0 });
    anchor.dispatchEvent(event);

    expect(mockedOpenUrl).not.toHaveBeenCalled();
    expect(event.defaultPrevented).toBe(false);

    uninstall();
    anchor.remove();
  });

  it("skips modifier clicks", () => {
    const uninstall = installExternalLinkDelegation();

    const anchor = document.createElement("a");
    anchor.href = "https://example.com";
    document.body.appendChild(anchor);

    const event = new MouseEvent("click", {
      bubbles: true,
      cancelable: true,
      button: 0,
      ctrlKey: true,
    });
    anchor.dispatchEvent(event);

    expect(mockedOpenUrl).not.toHaveBeenCalled();
    expect(event.defaultPrevented).toBe(false);

    uninstall();
    anchor.remove();
  });

  it("skips target=_blank links", () => {
    const uninstall = installExternalLinkDelegation();

    const anchor = document.createElement("a");
    anchor.href = "https://example.com";
    anchor.target = "_blank";
    document.body.appendChild(anchor);

    const event = new MouseEvent("click", { bubbles: true, cancelable: true, button: 0 });
    anchor.dispatchEvent(event);

    expect(mockedOpenUrl).not.toHaveBeenCalled();
    expect(event.defaultPrevented).toBe(false);

    uninstall();
    anchor.remove();
  });

  it("intercepts external links in shadow DOM", () => {
    const uninstall = installExternalLinkDelegation();

    const host = document.createElement("div");
    const shadowRoot = host.attachShadow({ mode: "open" });
    const anchor = document.createElement("a");
    anchor.href = "https://example.com";
    anchor.textContent = "external";
    shadowRoot.appendChild(anchor);
    document.body.appendChild(host);

    const event = new MouseEvent("click", {
      bubbles: true,
      cancelable: true,
      composed: true,
      button: 0,
    });
    anchor.dispatchEvent(event);

    expect(mockedOpenUrl).toHaveBeenCalledWith("https://example.com/");
    expect(event.defaultPrevented).toBe(true);

    uninstall();
    host.remove();
  });
});
