import { describe, expect, it } from "vitest";

import { runCli } from "../src/cli.js";

describe("cli smoke", () => {
  it("supports --help", async () => {
    const result = await runCli(["--help"]);
    expect(result.exit_code).toBe(0);
    expect(result.stdout).toContain("html-codegen");
  });
});
