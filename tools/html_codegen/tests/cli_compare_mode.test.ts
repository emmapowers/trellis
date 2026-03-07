import { mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import { runCli } from "../src/cli.js";

describe("compare mode", () => {
  it("returns a diff summary", async () => {
    const result = await runCli(["compare"], { format_python: false });
    expect([0, 1]).toContain(result.exit_code);
    expect(result.stdout).toContain("diff summary");
  });

  it("ignores timestamp-only diffs", async () => {
    const repo_root = await mkdtemp(join(tmpdir(), "html-codegen-"));

    const writeResult = await runCli(["write"], {
      format_python: false,
      generated_at: "2026-03-07T12:00:00.000Z",
      repo_root,
    });
    expect(writeResult.exit_code).toBe(0);

    const compareResult = await runCli(["compare"], {
      format_python: false,
      generated_at: "2026-03-07T12:05:00.000Z",
      repo_root,
    });
    expect(compareResult.exit_code).toBe(0);
  });
});
