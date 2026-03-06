import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "../test-utils";
import { Button } from "../../../src/trellis/widgets/client/components/Button";

describe("Button", () => {
  it("renders the provided text", () => {
    render(<Button text="Smoke test" />);

    expect(screen.getByRole("button", { name: "Smoke test" })).toBeInTheDocument();
  });

  it("respects the disabled prop", () => {
    render(<Button text="Disabled" disabled />);

    expect(screen.getByRole("button", { name: "Disabled" })).toBeDisabled();
  });
});
