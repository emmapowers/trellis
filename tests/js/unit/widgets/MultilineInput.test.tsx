import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "../../test-utils";
import { Mutable, resetMutableStates } from "@trellis/trellis-core/core/types";
import { MultilineInput } from "../../../../src/trellis/widgets/client/MultilineInput";

describe("MultilineInput", () => {
  beforeEach(() => {
    resetMutableStates();
  });

  it("renders textarea value", () => {
    render(<MultilineInput value={"hello\nworld"} />);

    const textarea = screen.getByRole("textbox");
    expect(textarea).toHaveValue("hello\nworld");
  });

  it("supports mutable two-way binding", () => {
    const onEvent = vi.fn();
    const mutable = new Mutable<string>({ __mutable__: "cb-id", value: "initial", version: 0 }, onEvent);

    render(<MultilineInput value={mutable} />);

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "updated text" } });

    expect(onEvent).toHaveBeenCalledWith("cb-id", ["updated text", 1]);
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

  it("preserves cursor position after typing when server value arrives", () => {
    const { rerender } = render(<MultilineInput value={"hello"} />);

    const textarea = screen.getByRole("textbox") as HTMLTextAreaElement;
    textarea.focus();

    // Simulate user typing in the middle: positions cursor at 3, types 'X'
    textarea.setSelectionRange(3, 3);
    fireEvent.change(textarea, { target: { value: "helXlo", selectionStart: 4 } });

    // Server responds with transformed value (e.g., uppercase)
    rerender(<MultilineInput value={"HELXLO"} />);

    expect(textarea.selectionStart).toBe(4);
    expect(textarea.selectionEnd).toBe(4);
  });
});
