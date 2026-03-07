export function render_generated_module_docstring(
  summary: string,
  generated_at: string,
): string {
  return `"""${summary}

Generated at: ${generated_at}
"""`;
}
