import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "../../test-utils";
import { Mutable, resetMutableStates } from "@trellis/trellis-core/core/types";
import { TextInput } from "../../../../src/trellis/widgets/client/TextInput";

describe("TextInput", () => {
  beforeEach(() => {
    resetMutableStates();
  });

  it("renders input value", () => {
    render(<TextInput value={"hello"} />);

    const input = screen.getByRole("textbox");
    expect(input).toHaveValue("hello");
  });

  it("supports mutable two-way binding", () => {
    const onEvent = vi.fn();
    const mutable = new Mutable<string>({ __mutable__: "cb-id", value: "initial", version: 0 }, onEvent);

    render(<TextInput value={mutable} />);

    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "updated text" } });

    expect(onEvent).toHaveBeenCalledWith("cb-id", ["updated text", 1]);
  });

  it("supports disabled", () => {
    render(<TextInput value="read only" disabled />);

    const input = screen.getByRole("textbox");
    expect(input).toBeDisabled();
  });

  it("preserves cursor position after typing when server value arrives", () => {
    const { rerender } = render(<TextInput value={"hello"} />);

    const input = screen.getByRole("textbox") as HTMLInputElement;
    input.focus();

    // Simulate user typing in the middle: positions cursor at 3, types 'X'
    input.setSelectionRange(3, 3);
    fireEvent.change(input, { target: { value: "helXlo", selectionStart: 4 } });

    // Server responds with transformed value (e.g., uppercase)
    rerender(<TextInput value={"HELXLO"} />);

    expect(input.selectionStart).toBe(4);
    expect(input.selectionEnd).toBe(4);
  });
});
