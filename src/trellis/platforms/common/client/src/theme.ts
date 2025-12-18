/**
 * Design tokens for Trellis widgets.
 *
 * Light theme optimized for data-dense desktop dashboards.
 */

// Color palette
export const colors = {
  // Backgrounds
  bg: {
    page: "#f8fafc",
    surface: "#ffffff",
    surfaceRaised: "#f8fafc",
    surfaceHover: "#f1f5f9",
    input: "#ffffff",
  },

  // Borders
  border: {
    default: "#e2e8f0",
    subtle: "#f1f5f9",
    strong: "#cbd5e1",
    focus: "#6366f1",
  },

  // Text
  text: {
    primary: "#0f172a",
    secondary: "#64748b",
    muted: "#94a3b8",
    inverse: "#ffffff",
  },

  // Semantic colors
  semantic: {
    success: "#16a34a",
    successBg: "#f0fdf4",
    successBorder: "#bbf7d0",
    error: "#dc2626",
    errorBg: "#fef2f2",
    errorBorder: "#fecaca",
    warning: "#d97706",
    warningBg: "#fffbeb",
    warningBorder: "#fde68a",
    info: "#2563eb",
    infoBg: "#eff6ff",
    infoBorder: "#bfdbfe",
  },

  // Accent (indigo)
  accent: {
    primary: "#6366f1",
    primaryHover: "#4f46e5",
    primaryActive: "#4338ca",
    subtle: "#eef2ff",
  },

  // Neutral scale (slate)
  neutral: {
    50: "#f8fafc",
    100: "#f1f5f9",
    200: "#e2e8f0",
    300: "#cbd5e1",
    400: "#94a3b8",
    500: "#64748b",
    600: "#475569",
    700: "#334155",
    800: "#1e293b",
    900: "#0f172a",
  },
};

// Spacing scale (compact)
export const spacing = {
  xs: 4,
  sm: 6,
  md: 8,
  lg: 12,
  xl: 16,
  xxl: 24,
};

// Border radius (smaller for compact look)
export const radius = {
  none: 0,
  sm: 4,
  md: 6,
  lg: 8,
  full: 9999,
};

// Typography
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

// Shadows (subtle for light theme)
export const shadows = {
  none: "none",
  sm: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
  md: "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)",
  lg: "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)",
};

// Focus ring style (reusable) - uses outline to avoid overlap with adjacent elements
export const focusRing = {
  outline: `2px solid ${colors.accent.primary}`,
  outlineOffset: "-2px",
};

// Focus ring for dark/colored backgrounds - subtle double ring for contrast
export const focusRingOnColor = {
  outline: `1px solid rgba(255, 255, 255, 0.8)`,
  outlineOffset: "-1px",
  boxShadow: `0 0 0 2px ${colors.accent.primary}`,
};
