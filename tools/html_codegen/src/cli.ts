import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";

import { build_trellis_events_module } from "./emit/targets/trellis_events.js";
import { build_trellis_html_module } from "./emit/targets/trellis_html.js";
import { build_ir_document } from "./pipeline/build.js";
import { render_diff_summary } from "./report/diff_report.js";

export interface CliResult {
  exit_code: number;
  stdout: string;
  stderr: string;
}

export interface RunCliOptions {
  repo_root?: string;
}

function default_repo_root(): string {
  return join(import.meta.dirname, "..", "..", "..");
}

function help_text(): string {
  return [
    "html-codegen",
    "",
    "Usage:",
    "  html-codegen compare",
    "  html-codegen write",
    "  html-codegen --help",
  ].join("\n");
}

async function compute_target_summary(
  repo_root: string,
): Promise<{
  targets: Array<{ path: string; content: string }>;
  summary: { changed: number; added: number; removed: number };
}> {
  const document = await build_ir_document();
  const payloads = [build_trellis_html_module(document), build_trellis_events_module(document)];
  const targets = payloads.map((payload) => ({
    path: join(repo_root, payload.path),
    content: payload.content,
  }));

  const summary = { changed: 0, added: 0, removed: 0 };
  for (const target of targets) {
    let existing_content: string | undefined;
    try {
      existing_content = await readFile(target.path, "utf-8");
    } catch {
      existing_content = undefined;
    }

    if (existing_content === undefined) {
      summary.added += 1;
    } else if (existing_content !== target.content) {
      summary.changed += 1;
    }
  }

  return {
    targets,
    summary,
  };
}

export async function runCli(argv: string[], options: RunCliOptions = {}): Promise<CliResult> {
  const repo_root = options.repo_root ?? default_repo_root();

  if (argv.includes("--help") || argv.includes("-h") || argv.length === 0) {
    return {
      exit_code: 0,
      stdout: help_text(),
      stderr: "",
    };
  }

  const command = argv[0];
  if (command === "compare") {
    const { summary } = await compute_target_summary(repo_root);
    const has_diff = summary.changed + summary.added + summary.removed > 0;
    return {
      exit_code: has_diff ? 1 : 0,
      stdout: render_diff_summary(summary),
      stderr: "",
    };
  }

  if (command === "write") {
    const { targets, summary } = await compute_target_summary(repo_root);
    for (const target of targets) {
      await mkdir(dirname(target.path), { recursive: true });
      await writeFile(target.path, target.content, "utf-8");
    }

    return {
      exit_code: 0,
      stdout: [
        "wrote generated outputs",
        render_diff_summary(summary),
      ].join("\n"),
      stderr: "",
    };
  }

  return {
    exit_code: 2,
    stdout: "",
    stderr: `Unknown command: ${command}`,
  };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const result = await runCli(process.argv.slice(2));
  if (result.stdout) {
    process.stdout.write(`${result.stdout}\n`);
  }
  if (result.stderr) {
    process.stderr.write(`${result.stderr}\n`);
  }
  process.exit(result.exit_code);
}
