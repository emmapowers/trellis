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

  it("preserves cursor position when value changes while focused", () => {
    const { rerender } = render(<TextInput value={"hello"} />);

    const input = screen.getByRole("textbox") as HTMLInputElement;
    input.focus();
    input.setSelectionRange(3, 3); // Cursor after "hel"

    // Simulate server pushing an updated value (e.g., uppercase transform)
    rerender(<TextInput value={"HELLO"} />);

    expect(input.selectionStart).toBe(3);
    expect(input.selectionEnd).toBe(3);
  });
});
