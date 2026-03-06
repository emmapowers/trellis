import React from "react";
import { Button as ShadcnButton } from "@trellis/trellis-widgets/shadcn/ui/button";

interface ButtonProps {
  text: string;
  disabled?: boolean;
  variant?: "default" | "outline" | "secondary" | "ghost" | "destructive" | "link";
  size?: "default" | "xs" | "sm" | "lg";
}

export function Button({
  text,
  disabled = false,
  variant = "default",
  size = "default",
}: ButtonProps): React.ReactElement {
  return (
    <ShadcnButton disabled={disabled} size={size} variant={variant}>
      {text}
    </ShadcnButton>
  );
}
