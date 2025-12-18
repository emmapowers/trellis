import React from "react";
import * as LucideIcons from "lucide-react";
import { colors } from "../theme";

interface IconProps {
  name: string;
  size?: number;
  color?: string;
  stroke_width?: number;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * Convert kebab-case icon name to PascalCase for Lucide component lookup.
 * e.g., "arrow-up" -> "ArrowUp"
 */
function toPascalCase(str: string): string {
  return str
    .split("-")
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
    .join("");
}

/**
 * Icon component using Lucide React icons.
 *
 * Renders icons by name from the Lucide icon library.
 * See https://lucide.dev/icons for available icons.
 */
export function Icon({
  name,
  size = 16,
  color,
  stroke_width = 2,
  className,
  style,
}: IconProps): React.ReactElement | null {
  const pascalName = toPascalCase(name);
  const IconComponent = (LucideIcons as Record<string, React.ComponentType<LucideIcons.LucideProps>>)[pascalName];

  if (!IconComponent) {
    console.warn(`Unknown icon: ${name} (looked up as ${pascalName})`);
    return null;
  }

  return (
    <IconComponent
      size={size}
      color={color ?? colors.text.primary}
      strokeWidth={stroke_width}
      className={className}
      style={style}
    />
  );
}
