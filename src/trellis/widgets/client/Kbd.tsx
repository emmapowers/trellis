import React from "react";
import { colors, typography } from "@trellis/trellis-core/theme";

const IS_MAC =
  typeof navigator !== "undefined" &&
  /Mac|iPhone|iPad/.test(navigator.platform);

type KeyMap = Record<string, { mac: string; other: string } | string>;

const KEY_SYMBOLS: KeyMap = {
  // Modifiers
  Mod: { mac: "⌘", other: "Ctrl" },
  Meta: { mac: "⌘", other: "Super" },
  Control: { mac: "⌃", other: "Ctrl" },
  Alt: { mac: "⌥", other: "Alt" },
  Shift: { mac: "⇧", other: "Shift" },
  // Arrow keys
  ArrowLeft: "←",
  ArrowRight: "→",
  ArrowUp: "↑",
  ArrowDown: "↓",
  // Special keys
  Enter: "↩",
  Escape: "Esc",
  Backspace: "⌫",
  Delete: "⌦",
  Tab: "⇥",
  Space: "Space",
};

/**
 * Parse a key filter string like "Mod+S" into resolved display tokens.
 * Exported for testing.
 */
export function resolveKeyTokens(keys: string, isMac: boolean): string[] {
  return keys.split("+").map((token) => {
    const mapping = KEY_SYMBOLS[token];
    if (mapping === undefined) return token;
    if (typeof mapping === "string") return mapping;
    return isMac ? mapping.mac : mapping.other;
  });
}

interface KbdProps {
  keys?: string;
  style?: React.CSSProperties;
}

export function Kbd({ keys = "", style }: KbdProps): React.ReactElement {
  const tokens = resolveKeyTokens(keys, IS_MAC);

  return (
    <kbd
      style={{
        fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
        fontSize: `${typography.fontSize.sm}px`,
        color: colors.text.secondary,
        fontStyle: "normal",
        fontWeight: typography.fontWeight.normal,
        ...style,
      }}
    >
      {tokens.map((token, i) => (
        <React.Fragment key={i}>
          {i > 0 && (
            <span
              style={{
                color: colors.text.muted,
                padding: "0 1px",
              }}
            >
              +
            </span>
          )}
          <span>{token}</span>
        </React.Fragment>
      ))}
    </kbd>
  );
}
