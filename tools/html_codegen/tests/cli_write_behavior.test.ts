import { access, mkdtemp, readFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import { runCli } from "../src/cli.js";

describe("write mode", () => {
  it("writes generated module output", async () => {
    const repo_root = await mkdtemp(join(tmpdir(), "html-codegen-"));

    const result = await runCli(["write"], { format_python: false, repo_root });
    expect(result.exit_code).toBe(0);

    const generated_path = join(repo_root, "src", "trellis", "html", "_generated_runtime.py");
    const forms_path = join(repo_root, "src", "trellis", "html", "_generated_forms.py");
    const media_path = join(
      repo_root,
      "src",
      "trellis",
      "html",
      "_generated_image_and_multimedia.py",
    );
    const events_path = join(repo_root, "src", "trellis", "html", "events.py");
    await expect(access(generated_path)).resolves.toBeUndefined();
    await expect(access(forms_path)).resolves.toBeUndefined();
    await expect(access(media_path)).resolves.toBeUndefined();
    await expect(access(events_path)).resolves.toBeUndefined();

    const content = await readFile(generated_path, "utf-8");
    expect(content).toContain("from trellis.html._generated_sectioning_and_layout import (");
    expect(content).toContain("    Div,");

    const forms_content = await readFile(forms_path, "utf-8");
    expect(forms_content).toContain("def Input(");

    const media_content = await readFile(media_path, "utf-8");
    expect(media_content).toContain("def Audio(");

    const events_content = await readFile(events_path, "utf-8");
    expect(events_content).toContain("class MouseEvent");
  });
});
