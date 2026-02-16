import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent } from "../../test-utils";
import { SplitPane } from "../../../../src/trellis/widgets/client/SplitPane";

describe("SplitPane", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
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
});
