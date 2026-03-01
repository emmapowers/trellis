import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "../../test-utils";
import { Mutable, resetMutableStates } from "@trellis/trellis-core/core/types";
import { useTextValue } from "@trellis/trellis-core/core/useTextValue";

function TestInput({ value }: { value: string | Mutable<string> }) {
  const tv = useTextValue(value);
  return <input ref={tv.ref} value={tv.value} onChange={tv.onChange} />;
}

describe("useTextValue", () => {
  beforeEach(() => {
    resetMutableStates();
  });

  it("renders plain string value", () => {
    render(<TestInput value="hello" />);
    expect(screen.getByRole("textbox")).toHaveValue("hello");
  });

  it("renders mutable value", () => {
    const onEvent = vi.fn();
    const mutable = new Mutable<string>(
      { __mutable__: "tv-id", value: "mutable-val", version: 0 },
      onEvent
    );
    render(<TestInput value={mutable} />);
    expect(screen.getByRole("textbox")).toHaveValue("mutable-val");
  });

  it("updates displayed value immediately on typing", () => {
    render(<TestInput value="hello" />);
    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "hello world" } });
    expect(input).toHaveValue("hello world");
  });

  it("sends value to server via mutable binding", () => {
    const onEvent = vi.fn();
    const mutable = new Mutable<string>(
      { __mutable__: "tv-id", value: "initial", version: 0 },
      onEvent
    );
    render(<TestInput value={mutable} />);
    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "updated" } });
    expect(onEvent).toHaveBeenCalledWith("tv-id", ["updated", 1]);
  });

  it("accepts new server value on rerender", () => {
    const { rerender } = render(<TestInput value="v1" />);
    rerender(<TestInput value="v2" />);
    expect(screen.getByRole("textbox")).toHaveValue("v2");
  });

  it("preserves cursor position when server value changes while focused", () => {
    const { rerender } = render(<TestInput value="hello" />);
    const input = screen.getByRole("textbox") as HTMLInputElement;
    input.focus();

    input.setSelectionRange(3, 3);
    fireEvent.change(input, { target: { value: "helXlo", selectionStart: 4 } });

    rerender(<TestInput value="HELXLO" />);

    expect(input.selectionStart).toBe(4);
    expect(input.selectionEnd).toBe(4);
  });
});
