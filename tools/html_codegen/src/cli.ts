import { spawn } from "node:child_process";
import { mkdtemp, mkdir, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { basename, dirname, join } from "node:path";

import { build_trellis_events_module } from "./emit/targets/trellis_events.js";
import { build_trellis_html_modules } from "./emit/targets/trellis_html.js";
import { build_ir_document } from "./pipeline/build.js";
import { render_diff_summary } from "./report/diff_report.js";

export interface CliResult {
  exit_code: number;
  stdout: string;
  stderr: string;
}

export interface RunCliOptions {
  format_python?: boolean;
  generated_at?: string;
  repo_root?: string;
}

const GENERATED_AT_PREFIX = "Generated at: ";

function normalize_generated_metadata(content: string): string {
  return content.replace(
    /^Generated at: .+$/m,
    `${GENERATED_AT_PREFIX}<normalized>`,
  );
}

async function format_python_source(
  formatter_root: string,
  path: string,
  content: string,
): Promise<string> {
  if (!path.endsWith(".py")) {
    return content;
  }

  const black_formatted = await new Promise<string>((resolve, reject) => {
    const child = spawn(
      "pixi",
      ["run", "black", "--quiet", "--stdin-filename", path, "-"],
      {
        cwd: formatter_root,
        stdio: ["pipe", "pipe", "pipe"],
      },
    );

    let stdout = "";
    let stderr = "";

    child.stdout.setEncoding("utf8");
    child.stdout.on("data", (chunk: string) => {
      stdout += chunk;
    });

    child.stderr.setEncoding("utf8");
    child.stderr.on("data", (chunk: string) => {
      stderr += chunk;
    });

    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) {
        resolve(stdout);
        return;
      }
      reject(new Error(`black failed for ${path}: ${stderr || `exit code ${code}`}`));
    });

    child.stdin.end(content);
  });

  const temp_dir = await mkdtemp(join(tmpdir(), "html-codegen-format-"));
  const temp_path = join(temp_dir, basename(path));
  try {
    await writeFile(temp_path, black_formatted, "utf-8");
    await new Promise<void>((resolve, reject) => {
      const child = spawn(
        "pixi",
        ["run", "ruff", "check", "--select", "RUF022,I001", "--fix", temp_path],
        {
          cwd: formatter_root,
          stdio: ["ignore", "pipe", "pipe"],
        },
      );

      let stderr = "";
      child.stderr.setEncoding("utf8");
      child.stderr.on("data", (chunk: string) => {
        stderr += chunk;
      });

      child.on("error", reject);
      child.on("close", (code) => {
        if (code === 0) {
          resolve();
          return;
        }
        reject(new Error(`ruff failed for ${path}: ${stderr || `exit code ${code}`}`));
      });
    });

    return await readFile(temp_path, "utf-8");
  } finally {
    await rm(temp_dir, { force: true, recursive: true });
  }
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
  format_python: boolean,
  generated_at: string,
): Promise<{
  targets: Array<{ path: string; content: string }>;
  stale_paths: string[];
  summary: { changed: number; added: number; removed: number };
}> {
  const formatter_root = default_repo_root();
  const document = await build_ir_document();
  const payloads = [
    ...build_trellis_html_modules(document, generated_at),
    build_trellis_events_module(document, generated_at),
  ];
  const targets = await Promise.all(
    payloads.map(async (payload) => ({
      path: join(repo_root, payload.path),
      content: format_python
        ? await format_python_source(formatter_root, payload.path, payload.content)
        : payload.content,
    })),
  );

  const summary = { changed: 0, added: 0, removed: 0 };
  const expected_paths = new Set(targets.map((target) => target.path));
  const generated_dir = join(repo_root, "src", "trellis", "html");
  const stale_paths: string[] = [];

  try {
    const existing_names = await readdir(generated_dir);
    for (const name of existing_names) {
      const is_generated_file =
        (name.startsWith("_generated_") && name.endsWith(".py")) || name === "events.py";
      if (!is_generated_file) {
        continue;
      }

      const path = join(generated_dir, name);
      if (!expected_paths.has(path)) {
        stale_paths.push(path);
      }
    }
  } catch {
    // Directory may not exist yet in compare mode.
  }

  for (const target of targets) {
    let existing_content: string | undefined;
    try {
      existing_content = await readFile(target.path, "utf-8");
    } catch {
      existing_content = undefined;
    }

    if (existing_content === undefined) {
      summary.added += 1;
    } else if (
      normalize_generated_metadata(existing_content) !==
      normalize_generated_metadata(target.content)
    ) {
      summary.changed += 1;
    }
  }
  summary.removed = stale_paths.length;

  return {
    stale_paths,
    targets,
    summary,
  };
}

export async function runCli(argv: string[], options: RunCliOptions = {}): Promise<CliResult> {
  const format_python = options.format_python ?? true;
  const generated_at = options.generated_at ?? new Date().toISOString();
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
    const { summary } = await compute_target_summary(repo_root, format_python, generated_at);
    const has_diff = summary.changed + summary.added + summary.removed > 0;
    return {
      exit_code: has_diff ? 1 : 0,
      stdout: render_diff_summary(summary),
      stderr: "",
    };
  }

  if (command === "write") {
    const { targets, stale_paths, summary } = await compute_target_summary(
      repo_root,
      format_python,
      generated_at,
    );
    for (const target of targets) {
      await mkdir(dirname(target.path), { recursive: true });
      await writeFile(target.path, target.content, "utf-8");
    }
    for (const stale_path of stale_paths) {
      await rm(stale_path, { force: true });
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
