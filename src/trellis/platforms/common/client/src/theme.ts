/**
 * Design tokens for Trellis widgets.
 *
 * Colors use CSS custom properties for light/dark mode support.
 * Spacing, typography, and other values remain static.
 */

// Color palette - uses CSS variables for theme support
export const colors = {
  // Backgrounds
  bg: {
    page: "var(--trellis-bg-page)",
    surface: "var(--trellis-bg-surface)",
    surfaceRaised: "var(--trellis-bg-surface-raised)",
    surfaceHover: "var(--trellis-bg-surface-hover)",
    input: "var(--trellis-bg-input)",
  },

  // Borders
  border: {
    default: "var(--trellis-border-default)",
    subtle: "var(--trellis-border-subtle)",
    strong: "var(--trellis-border-strong)",
    focus: "var(--trellis-border-focus)",
  },

  // Text
  text: {
    primary: "var(--trellis-text-primary)",
    secondary: "var(--trellis-text-secondary)",
    muted: "var(--trellis-text-muted)",
    inverse: "var(--trellis-text-inverse)",
  },

  // Semantic colors
  semantic: {
    success: "var(--trellis-success)",
    successBg: "var(--trellis-success-bg)",
    successBorder: "var(--trellis-success-border)",
    error: "var(--trellis-error)",
    errorBg: "var(--trellis-error-bg)",
    errorBorder: "var(--trellis-error-border)",
    errorHover: "var(--trellis-error-hover)",
    warning: "var(--trellis-warning)",
    warningBg: "var(--trellis-warning-bg)",
    warningBorder: "var(--trellis-warning-border)",
    info: "var(--trellis-info)",
    infoBg: "var(--trellis-info-bg)",
    infoBorder: "var(--trellis-info-border)",
  },

  // Accent (indigo)
  accent: {
    primary: "var(--trellis-accent-primary)",
    primaryHover: "var(--trellis-accent-primary-hover)",
    primaryActive: "var(--trellis-accent-primary-active)",
    subtle: "var(--trellis-accent-subtle)",
  },

  // Neutral scale (slate)
  neutral: {
    50: "var(--trellis-neutral-50)",
    100: "var(--trellis-neutral-100)",
    200: "var(--trellis-neutral-200)",
    300: "var(--trellis-neutral-300)",
    400: "var(--trellis-neutral-400)",
    500: "var(--trellis-neutral-500)",
    600: "var(--trellis-neutral-600)",
    700: "var(--trellis-neutral-700)",
    800: "var(--trellis-neutral-800)",
    900: "var(--trellis-neutral-900)",
  },
};

// Spacing scale (compact) - static values
export const spacing = {
  xs: 4,
  sm: 6,
  md: 8,
  lg: 12,
  xl: 16,
  xxl: 24,
};

// Border radius (smaller for compact look) - static values
export const radius = {
  none: 0,
  sm: 4,
  md: 6,
  lg: 8,
  full: 9999,
};

// Typography - static values
export const typography = {
  fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
  fontSize: {
    xs: 11,
    sm: 12,
    md: 13,
    lg: 14,
    xl: 16,
    xxl: 20,
    xxxl: 24,
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },
};

// Input height (explicit to avoid cross-browser inconsistencies)
export const inputHeight = 32;

// Shadows - uses CSS variables for theme support
export const shadows = {
  none: "none",
  sm: "var(--trellis-shadow-sm)",
  md: "var(--trellis-shadow-md)",
  lg: "var(--trellis-shadow-lg)",
};

// Focus ring style (reusable) - uses CSS variable for color
export const focusRing = {
  outline: "2px solid var(--trellis-focus-ring-color)",
  outlineOffset: "-2px",
};

// Focus ring for dark/colored backgrounds - subtle double ring for contrast
export const focusRingOnColor = {
  outline: "1px solid rgba(255, 255, 255, 0.8)",
  outlineOffset: "-1px",
  boxShadow: "0 0 0 2px var(--trellis-focus-ring-color)",
};
