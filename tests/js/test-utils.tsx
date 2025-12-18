import React from "react";
import { render, RenderOptions } from "@testing-library/react";

// Custom render function that can wrap components with providers if needed
function customRender(
  ui: React.ReactElement,
  options?: Omit<RenderOptions, "wrapper">
) {
  return render(ui, { ...options });
}

// Re-export everything from testing-library
export * from "@testing-library/react";

// Override render with custom render
export { customRender as render };
