import { access, mkdtemp, readFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import { runCli } from "../src/cli.js";

describe("write mode", () => {
  it("writes generated module output", async () => {
    const repo_root = await mkdtemp(join(tmpdir(), "html-codegen-"));

    const result = await runCli(["write"], { repo_root });
    expect(result.exit_code).toBe(0);

    const generated_path = join(repo_root, "src", "trellis", "html", "_generated_runtime.py");
    await expect(access(generated_path)).resolves.toBeUndefined();

    const content = await readFile(generated_path, "utf-8");
    expect(content).toContain("def Div(");
  });
});
