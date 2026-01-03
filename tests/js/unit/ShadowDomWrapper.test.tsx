/**
 * Tests for ShadowDomWrapper component.
 *
 * Verifies that React Aria's usePress works correctly inside shadow DOM.
 * React Aria registers global event listeners on document, but events from
 * shadow DOM don't bubble there by default. This test ensures our fix works.
 *
 * See: https://github.com/adobe/react-spectrum/issues/2040
 */

import { describe, it, expect, vi } from "vitest";
import React from "react";
import { render, waitFor } from "../test-utils";
import userEvent from "@testing-library/user-event";
import { ShadowDomWrapper } from "../../../docs/src/components/TrellisDemo/ShadowDomWrapper";
import { Button } from "../../../src/trellis/platforms/common/client/src/widgets/Button";

describe("ShadowDomWrapper", () => {
  describe("event forwarding", () => {
    it("forwards mouseup events from shadow DOM to document", async () => {
      const documentHandler = vi.fn();
      document.addEventListener("mouseup", documentHandler);

      const { container } = render(
        <ShadowDomWrapper>
          <button>Test</button>
        </ShadowDomWrapper>
      );

      // Wait for shadow DOM
      await waitFor(() => {
        const host = container.firstChild as HTMLElement;
        expect(host.shadowRoot).not.toBeNull();
      });

      const host = container.firstChild as HTMLElement;
      const shadowRoot = host.shadowRoot!;
      const button = shadowRoot.querySelector("button");

      // Dispatch mouseup on the button in shadow DOM
      const event = new MouseEvent("mouseup", { bubbles: true });
      button!.dispatchEvent(event);

      // Verify document received the forwarded event
      expect(documentHandler).toHaveBeenCalled();

      document.removeEventListener("mouseup", documentHandler);
    });
  });

  describe("React Aria compatibility", () => {
    // First verify the Button works without shadow DOM
    it("button clicks work without shadow DOM (baseline)", async () => {
      const user = userEvent.setup();
      const onClick = vi.fn();

      const { container } = render(
        <Button text="Click me" on_click={onClick} />
      );

      const button = container.querySelector("button");
      expect(button).not.toBeNull();

      await user.click(button!);

      expect(onClick).toHaveBeenCalledTimes(1);
    });

    it("button clicks trigger handlers inside shadow DOM (native click)", async () => {
      const onClick = vi.fn();

      const { container } = render(
        <ShadowDomWrapper>
          <Button text="Click me" on_click={onClick} />
        </ShadowDomWrapper>
      );

      // Wait for shadow DOM to be created
      await waitFor(() => {
        const host = container.firstChild as HTMLElement;
        expect(host.shadowRoot).not.toBeNull();
      });

      // Get the button inside shadow DOM
      const host = container.firstChild as HTMLElement;
      const shadowRoot = host.shadowRoot!;
      const button = shadowRoot.querySelector("button");
      expect(button).not.toBeNull();

      // Click the button using native click
      button!.click();

      // Verify handler was called
      expect(onClick).toHaveBeenCalledTimes(1);
    });

    it("button clicks trigger handlers inside shadow DOM (userEvent)", async () => {
      const user = userEvent.setup();
      const onClick = vi.fn();

      const { container } = render(
        <ShadowDomWrapper>
          <Button text="Click me" on_click={onClick} />
        </ShadowDomWrapper>
      );

      // Wait for shadow DOM to be created
      await waitFor(() => {
        const host = container.firstChild as HTMLElement;
        expect(host.shadowRoot).not.toBeNull();
      });

      // Get the button inside shadow DOM
      const host = container.firstChild as HTMLElement;
      const shadowRoot = host.shadowRoot!;
      const button = shadowRoot.querySelector("button");
      expect(button).not.toBeNull();

      // Click the button using userEvent
      await user.click(button!);

      // Verify handler was called
      expect(onClick).toHaveBeenCalledTimes(1);
    });
  });
});
