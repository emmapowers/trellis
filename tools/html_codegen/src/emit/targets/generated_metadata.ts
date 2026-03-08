export function render_generated_module_docstring(
  summary: string,
  generated_at: string,
  details: string[] = [],
): string {
  const lines = [`"""${summary}`, ""];
  if (details.length > 0) {
    lines.push(...details, "");
  }
  lines.push(`Generated at: ${generated_at}`, '"""');
  return lines.join("\n");
}
