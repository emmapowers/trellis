import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "../../test-utils";
import { Mutable } from "@trellis/trellis-core/core/types";
import { MultilineInput } from "../../../../src/trellis/widgets/client/MultilineInput";

describe("MultilineInput", () => {
  it("renders textarea value", () => {
    render(<MultilineInput value={"hello\nworld"} />);

    const textarea = screen.getByRole("textbox");
    expect(textarea).toHaveValue("hello\nworld");
  });

  it("supports mutable two-way binding", () => {
    const onEvent = vi.fn();
    const mutable = new Mutable<string>({ __mutable__: "cb-id", value: "initial" }, onEvent);

    render(<MultilineInput value={mutable} />);

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "updated text" } });

    expect(onEvent).toHaveBeenCalledWith("cb-id", ["updated text"]);
  });

  it("supports disabled and read_only", () => {
    render(<MultilineInput value="read only" disabled read_only />);

    const textarea = screen.getByRole("textbox");
    expect(textarea).toBeDisabled();
    expect(textarea).toHaveAttribute("readonly");
  });

  it("handles large text content", () => {
    const largeText = "a".repeat(20000);
    render(<MultilineInput value={largeText} />);

    const textarea = screen.getByRole("textbox");
    expect((textarea as HTMLTextAreaElement).value.length).toBe(20000);
  });
});
