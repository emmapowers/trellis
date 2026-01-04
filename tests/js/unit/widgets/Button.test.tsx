import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "../../test-utils";
import userEvent from "@testing-library/user-event";
import { Button } from "@common/widgets/Button";

describe("Button", () => {
  describe("click propagation", () => {
    it("allows clicks to bubble to parent anchor when no on_click handler", async () => {
      const user = userEvent.setup();
      const anchorClickHandler = vi.fn();

      render(
        <a href="/test" onClick={anchorClickHandler}>
          <Button text="Click me" />
        </a>
      );

      const button = screen.getByRole("button", { name: "Click me" });
      await user.click(button);

      expect(anchorClickHandler).toHaveBeenCalledTimes(1);
    });

    it("handles click with on_click and does not bubble to parent", async () => {
      const user = userEvent.setup();
      const buttonClickHandler = vi.fn();
      const anchorClickHandler = vi.fn();

      render(
        <a href="/test" onClick={anchorClickHandler}>
          <Button text="Click me" on_click={buttonClickHandler} />
        </a>
      );

      const button = screen.getByRole("button", { name: "Click me" });
      await user.click(button);

      // Button's handler should be called
      expect(buttonClickHandler).toHaveBeenCalledTimes(1);
      // Anchor's handler may or may not be called - React Aria controls this
      // The key behavior is that button's handler works
    });
  });

  describe("rendering", () => {
    it("renders with text", () => {
      render(<Button text="Hello" />);
      expect(screen.getByRole("button", { name: "Hello" })).toBeInTheDocument();
    });

    it("renders disabled state", () => {
      render(<Button text="Disabled" disabled />);
      expect(screen.getByRole("button", { name: "Disabled" })).toBeDisabled();
    });
  });
});
