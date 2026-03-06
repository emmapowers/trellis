import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

describe("documentation", () => {
  it("documents compare and write workflow", () => {
    const root = resolve(import.meta.dirname, "..", "..", "..");
    const usage_path = resolve(root, "docs/plans/html-codegen-usage.md");
    const content = readFileSync(usage_path, "utf-8");

    expect(content).toContain("compare");
    expect(content).toContain("write");
  });
});
