/**
 * Theme CSS variable references for use in TypeScript components.
 *
 * These map to the CSS custom properties defined in theme.css.
 * Use these instead of hardcoded colors to support dark/light mode.
 */

export const theme = {
  // Backgrounds
  bg: "var(--trellis-bg)",
  bgSubtle: "var(--trellis-bg-subtle)",
  bgMuted: "var(--trellis-bg-muted)",

  // Foregrounds
  fg: "var(--trellis-fg)",
  fgMuted: "var(--trellis-fg-muted)",
  fgSubtle: "var(--trellis-fg-subtle)",

  // Borders
  border: "var(--trellis-border)",
  borderStrong: "var(--trellis-border-strong)",

  // Accent
  accent: "var(--trellis-accent)",
  accentHover: "var(--trellis-accent-hover)",
  accentFg: "var(--trellis-accent-fg)",

  // Semantic
  danger: "var(--trellis-danger)",
  dangerHover: "var(--trellis-danger-hover)",

  // Surfaces
  surface: "var(--trellis-surface)",
  surfaceBorder: "var(--trellis-surface-border)",

  // Shadows
  shadow: "var(--trellis-shadow)",

  // Inputs
  inputBg: "var(--trellis-input-bg)",
  inputBorder: "var(--trellis-input-border)",
  inputFg: "var(--trellis-input-fg)",

  // Focus
  focusRing: "var(--trellis-focus-ring)",
} as const;
