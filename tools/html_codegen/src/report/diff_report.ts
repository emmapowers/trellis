export interface DiffSummary {
  changed: number;
  added: number;
  removed: number;
}

export function render_diff_summary(summary: DiffSummary): string {
  return [
    "diff summary",
    `  changed: ${summary.changed}`,
    `  added: ${summary.added}`,
    `  removed: ${summary.removed}`,
  ].join("\n");
}
