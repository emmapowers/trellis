import React from "react";
import { isCallbackRef, CallbackRef } from "../types";

interface ButtonProps {
  text?: string;
  on_click?: CallbackRef | null;
  disabled?: boolean;
}

export function Button({
  text = "",
  on_click,
  disabled = false,
}: ButtonProps): React.ReactElement {
  const handleClick = () => {
    if (on_click && isCallbackRef(on_click)) {
      // For now, just log. Events will be sent to server in future.
      console.log("Button clicked, callback:", on_click.__callback__);
    }
  };

  return (
    <button onClick={handleClick} disabled={disabled}>
      {text}
    </button>
  );
}
