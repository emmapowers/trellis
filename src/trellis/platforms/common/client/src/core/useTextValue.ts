/**
 * Hook for text input widgets that need optimistic local state,
 * server value syncing, and cursor position preservation.
 *
 * Handles the full lifecycle:
 * - Immediate local rendering on each keystroke (no server round-trip lag)
 * - Accepting server values when they arrive (e.g. transforms like .upper())
 * - Preserving cursor position across value changes while focused
 */

import { useRef, useState, useLayoutEffect } from "react";

import { Mutable, unwrapMutable } from "./types";

interface TextValueResult<E extends HTMLInputElement | HTMLTextAreaElement> {
  /** The current display value (local optimistic or server-accepted). */
  value: string;
  /** Ref to attach to the input/textarea element. */
  ref: React.RefObject<E>;
  /** onChange handler that saves cursor, updates local state, and sends to server. */
  onChange: (e: React.ChangeEvent<E>) => void;
  /**
   * Save cursor position from a change event without updating the value.
   * Use when another handler (e.g. react-aria's inputProps.onChange) will
   * call setValue separately, to avoid double-sending to the server.
   */
  saveCursor: (e: React.ChangeEvent<E>) => void;
  /** Set the display value and send to server (for integration with libraries like react-aria). */
  setValue: (v: string) => void;
}

export function useTextValue<
  E extends HTMLInputElement | HTMLTextAreaElement = HTMLInputElement,
>(valueProp: string | Mutable<string>): TextValueResult<E> {
  const { value: serverValue, setValue: sendToServer } =
    unwrapMutable(valueProp);
  const [localValue, setLocalValue] = useState(serverValue);

  const ref = useRef<E>(null);
  const cursorRef = useRef<number | null>(null);
  const prevServerRef = useRef(serverValue);

  // Accept new server values (e.g. transforms like .upper())
  if (serverValue !== prevServerRef.current) {
    prevServerRef.current = serverValue;
    setLocalValue(serverValue);
  }

  // Restore cursor position after React commits a value change while focused.
  useLayoutEffect(() => {
    if (
      ref.current &&
      ref.current === document.activeElement &&
      cursorRef.current !== null
    ) {
      const pos = Math.min(cursorRef.current, localValue.length);
      ref.current.setSelectionRange(pos, pos);
    }
  }, [localValue]);

  const saveCursor = (e: React.ChangeEvent<E>) => {
    cursorRef.current = e.target.selectionStart;
  };

  const onChange = (e: React.ChangeEvent<E>) => {
    saveCursor(e);
    setLocalValue(e.target.value);
    sendToServer?.(e.target.value);
  };

  return {
    value: localValue,
    ref,
    onChange,
    saveCursor,
    setValue: (v: string) => {
      setLocalValue(v);
      sendToServer?.(v);
    },
  };
}
