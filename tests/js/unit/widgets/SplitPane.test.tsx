import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent } from "../../test-utils";
import { SplitPane } from "../../../../src/trellis/widgets/client/SplitPane";
import { Mutable, resetMutableStates } from "@trellis/trellis-core/core/types";

describe("SplitPane", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    resetMutableStates();
  });

  it("renders exactly two panes", () => {
    render(
      <SplitPane>
        <div>left</div>
        <div>right</div>
      </SplitPane>
    );

    expect(screen.getByTestId("split-pane-first")).toBeInTheDocument();
    expect(screen.getByTestId("split-pane-second")).toBeInTheDocument();
    expect(screen.getByRole("separator")).toBeInTheDocument();
  });

  it("updates split ratio while dragging", () => {
    render(
      <SplitPane split={0.5} min_size={50}>
        <div>left</div>
        <div>right</div>
      </SplitPane>
    );

    const root = screen.getByTestId("split-pane-root");
    const separator = screen.getByRole("separator");
    const firstPane = screen.getByTestId("split-pane-first");

    vi.spyOn(root, "getBoundingClientRect").mockReturnValue({
      x: 0,
      y: 0,
      top: 0,
      left: 0,
      right: 400,
      bottom: 300,
      width: 400,
      height: 300,
      toJSON: () => ({}),
    } as DOMRect);

    fireEvent.mouseDown(separator, { clientX: 200, clientY: 50 });
    fireEvent.mouseMove(window, { clientX: 300, clientY: 50 });

    expect(firstPane).toHaveStyle({ flexBasis: "75%" });
  });

  it("enforces min_size while dragging", () => {
    render(
      <SplitPane split={0.5} min_size={100}>
        <div>left</div>
        <div>right</div>
      </SplitPane>
    );

    const root = screen.getByTestId("split-pane-root");
    const separator = screen.getByRole("separator");
    const firstPane = screen.getByTestId("split-pane-first");

    vi.spyOn(root, "getBoundingClientRect").mockReturnValue({
      x: 0,
      y: 0,
      top: 0,
      left: 0,
      right: 400,
      bottom: 300,
      width: 400,
      height: 300,
      toJSON: () => ({}),
    } as DOMRect);

    fireEvent.mouseDown(separator, { clientX: 200, clientY: 50 });
    fireEvent.mouseMove(window, { clientX: 10, clientY: 50 });
    expect(firstPane).toHaveStyle({ flexBasis: "25%" });

    fireEvent.mouseMove(window, { clientX: 390, clientY: 50 });
    expect(firstPane).toHaveStyle({ flexBasis: "75%" });
  });

  it("applies explicit height prop to the split pane root", () => {
    render(
      <SplitPane height={220}>
        <div>left</div>
        <div>right</div>
      </SplitPane>
    );

    const root = screen.getByTestId("split-pane-root");
    expect(root).toHaveStyle({ height: "220px" });
  });

  it("calls Mutable setValue on drag completion (mouseUp)", () => {
    const onEvent = vi.fn();
    const mutable = new Mutable<number>({ __mutable__: "split-cb", value: 0.5, version: 0 }, onEvent);

    render(
      <SplitPane split={mutable} min_size={50}>
        <div>left</div>
        <div>right</div>
      </SplitPane>
    );

    const root = screen.getByTestId("split-pane-root");
    const separator = screen.getByRole("separator");

    vi.spyOn(root, "getBoundingClientRect").mockReturnValue({
      x: 0,
      y: 0,
      top: 0,
      left: 0,
      right: 400,
      bottom: 300,
      width: 400,
      height: 300,
      toJSON: () => ({}),
    } as DOMRect);

    // Start drag
    fireEvent.mouseDown(separator, { clientX: 200, clientY: 50 });
    // Move to 75%
    fireEvent.mouseMove(window, { clientX: 300, clientY: 50 });
    // setValue should NOT be called during drag
    expect(onEvent).not.toHaveBeenCalled();

    // Release — setValue should fire
    fireEvent.mouseUp(window);
    expect(onEvent).toHaveBeenCalledWith("split-cb", [0.75, 1]);
  });

  it("works with a plain number split prop (no Mutable)", () => {
    render(
      <SplitPane split={0.3} min_size={50}>
        <div>left</div>
        <div>right</div>
      </SplitPane>
    );

    const firstPane = screen.getByTestId("split-pane-first");
    expect(firstPane).toHaveStyle({ flexBasis: "30%" });
  });
});
