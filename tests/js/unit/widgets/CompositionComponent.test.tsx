import React from "react";
import { describe, it, expect } from "vitest";
import { render } from "../../test-utils";
import { CompositionComponent } from "@common/widgets/CompositionComponent";

describe("CompositionComponent", () => {
  it("renders children without adding a DOM wrapper element", () => {
    const { container } = render(
      <div data-testid="parent">
        <CompositionComponent name="TestComp">
          <p>child one</p>
          <p>child two</p>
        </CompositionComponent>
      </div>
    );

    const parent = container.querySelector("[data-testid='parent']")!;
    // Children should be direct DOM children of parent — no intermediate span
    expect(parent.children).toHaveLength(2);
    expect(parent.children[0].tagName).toBe("P");
    expect(parent.children[1].tagName).toBe("P");
  });

  it("does not inject data-trellis-component into the DOM", () => {
    const { container } = render(
      <CompositionComponent name="MyComp">
        <span>hello</span>
      </CompositionComponent>
    );

    expect(container.querySelector("[data-trellis-component]")).toBeNull();
  });

  it("renders without a name", () => {
    const { container } = render(
      <CompositionComponent>
        <span>content</span>
      </CompositionComponent>
    );

    expect(container.querySelector("span")).toHaveTextContent("content");
    // Still no wrapper element
    expect(container.querySelector("[data-trellis-component]")).toBeNull();
  });
});
