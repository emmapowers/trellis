import React from "react";
import { isCallbackRef, CallbackRef } from "../types";
import { useTrellisClient } from "../TrellisContext";

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
  const client = useTrellisClient();

  const handleClick = () => {
    if (on_click && isCallbackRef(on_click)) {
      client.sendEvent(on_click.__callback__);
    }
  };

  return (
    <button onClick={handleClick} disabled={disabled}>
      {text}
    </button>
  );
}
