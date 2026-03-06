export interface CliResult {
  exit_code: number;
  stdout: string;
  stderr: string;
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

export async function runCli(argv: string[]): Promise<CliResult> {
  if (argv.includes("--help") || argv.includes("-h") || argv.length === 0) {
    return {
      exit_code: 0,
      stdout: help_text(),
      stderr: "",
    };
  }

  const command = argv[0];
  if (command === "compare" || command === "write") {
    return {
      exit_code: 0,
      stdout: `TODO: ${command}`,
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
