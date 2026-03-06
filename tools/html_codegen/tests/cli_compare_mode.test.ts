import { describe, expect, it } from "vitest";

import { runCli } from "../src/cli.js";

describe("compare mode", () => {
  it("returns a diff summary", async () => {
    const result = await runCli(["compare"]);
    expect([0, 1]).toContain(result.exit_code);
    expect(result.stdout).toContain("diff summary");
  });
});
