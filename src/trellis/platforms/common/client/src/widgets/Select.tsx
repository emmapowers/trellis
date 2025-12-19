import React, { useRef, useEffect } from "react";
import { useSelect, useListBox, useOption, useButton, HiddenSelect, DismissButton, useOverlay } from "react-aria";
import { useSelectState, Item } from "react-stately";
import { colors, radius, typography, spacing, focusRing, shadows } from "../theme";
import { Mutable, unwrapMutable } from "../core/types";

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  value?: string | Mutable<string>;
  options?: SelectOption[];
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

const buttonStyles: React.CSSProperties = {
  backgroundColor: colors.bg.input,
  border: `1px solid ${colors.border.default}`,
  borderRadius: `${radius.sm}px`,
  padding: `${spacing.sm}px ${spacing.md + 2}px`,
  color: colors.text.primary,
  fontSize: `${typography.fontSize.md}px`,
  outline: "none",
  width: "100%",
  boxSizing: "border-box",
  cursor: "pointer",
  transition: "border-color 150ms ease, box-shadow 150ms ease",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  textAlign: "left",
};

const listBoxStyles: React.CSSProperties = {
  marginTop: "4px",
  backgroundColor: colors.bg.surface,
  border: `1px solid ${colors.border.default}`,
  borderRadius: `${radius.sm}px`,
  boxShadow: shadows.md,
  maxHeight: "200px",
  overflowY: "auto",
  zIndex: 1000,
  padding: `${spacing.xs}px 0`,
};

// Overlay container positions the dropdown below the button
const overlayContainerStyles: React.CSSProperties = {
  position: "absolute",
  top: "100%",
  left: 0,
  right: 0,
  zIndex: 1000,
};

const optionStyles: React.CSSProperties = {
  padding: `${spacing.sm}px ${spacing.md + 2}px`,
  cursor: "pointer",
  fontSize: `${typography.fontSize.md}px`,
  color: colors.text.primary,
  outline: "none", // Suppress default focus ring; we use background color for focus indication
};

const disabledStyles: React.CSSProperties = {
  opacity: 0.5,
  cursor: "not-allowed",
  backgroundColor: colors.neutral[50],
};

function ListBox({
  state,
  listBoxRef,
  onClose,
}: {
  state: ReturnType<typeof useSelectState>;
  listBoxRef: React.RefObject<HTMLUListElement | null>;
  onClose: () => void;
}) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const { listBoxProps } = useListBox(
    { autoFocus: state.focusStrategy || true },
    state,
    listBoxRef
  );

  const { overlayProps } = useOverlay(
    {
      isOpen: true,
      onClose,
      shouldCloseOnBlur: true,
      isDismissable: true,
    },
    overlayRef
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation();
      onClose();
    } else {
      // Let react-aria handle other keys
      listBoxProps.onKeyDown?.(e as never);
    }
  };

  return (
    <div {...overlayProps} ref={overlayRef} style={overlayContainerStyles}>
      <DismissButton onDismiss={onClose} />
      <ul {...listBoxProps} ref={listBoxRef} style={listBoxStyles} onKeyDown={handleKeyDown}>
        {[...state.collection].map((item) => (
          <Option key={item.key} item={item} state={state} />
        ))}
      </ul>
      <DismissButton onDismiss={onClose} />
    </div>
  );
}

function Option({ item, state }: { item: { key: React.Key; rendered: React.ReactNode }; state: ReturnType<typeof useSelectState> }) {
  const ref = useRef<HTMLLIElement>(null);
  const { optionProps, isSelected, isFocused } = useOption({ key: item.key }, state, ref);
  const [isHovered, setIsHovered] = React.useState(false);

  const handleMouseEnter = (e: React.MouseEvent<HTMLLIElement>) => {
    setIsHovered(true);
    optionProps.onMouseEnter?.(e as never);
  };

  const handleMouseLeave = (e: React.MouseEvent<HTMLLIElement>) => {
    setIsHovered(false);
    optionProps.onMouseLeave?.(e as never);
  };

  // Selected items get accent background, hover gets gray background
  const getBackgroundColor = () => {
    if (isSelected) return colors.accent.subtle;
    if (isFocused || isHovered) return colors.bg.surfaceHover;
    return "transparent";
  };

  return (
    <li
      {...optionProps}
      ref={ref}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      style={{
        ...optionStyles,
        backgroundColor: getBackgroundColor(),
        fontWeight: isSelected ? typography.fontWeight.medium : typography.fontWeight.normal,
        color: isSelected ? colors.accent.primary : colors.text.primary,
      }}
    >
      {item.rendered}
    </li>
  );
}

export function Select({
  value: valueProp,
  options = [],
  placeholder,
  disabled = false,
  className,
  style,
}: SelectProps): React.ReactElement {
  // Unwrap mutable binding if present
  const { value, setValue } = unwrapMutable(valueProp);

  const triggerRef = useRef<HTMLButtonElement>(null);
  const listBoxRef = useRef<HTMLUListElement>(null);

  // Convert options to Item elements for react-stately
  const items = options.map((opt) => ({ key: opt.value, label: opt.label }));

  const state = useSelectState({
    selectedKey: value,
    onSelectionChange: (key) => setValue?.(key as string),
    isDisabled: disabled,
    children: items.map((item) => <Item key={item.key}>{item.label}</Item>),
  });

  const { triggerProps, valueProps, menuProps } = useSelect(
    {
      selectedKey: value,
      onSelectionChange: (key) => setValue?.(key as string),
      isDisabled: disabled,
      children: items.map((item) => <Item key={item.key}>{item.label}</Item>),
    },
    state,
    triggerRef
  );

  const { buttonProps } = useButton(triggerProps, triggerRef);
  const [isFocusVisible, setIsFocusVisible] = React.useState(false);

  const selectedItem = state.selectedItem;
  const displayValue = selectedItem ? selectedItem.rendered : placeholder || "Select...";

  const computedButtonStyle: React.CSSProperties = {
    ...buttonStyles,
    ...(isFocusVisible && !disabled ? focusRing : {}),
    ...(disabled ? disabledStyles : {}),
  };

  // Apply width/sizing styles to the container, not the button
  const containerStyle: React.CSSProperties = {
    position: "relative",
    ...style,
  };

  return (
    <div className={className} style={containerStyle}>
      <HiddenSelect state={state} triggerRef={triggerRef} name={undefined} />
      <button
        {...buttonProps}
        ref={triggerRef}
        style={computedButtonStyle}
        onFocus={(e) => {
          buttonProps.onFocus?.(e);
          if (e.target.matches(":focus-visible")) {
            setIsFocusVisible(true);
          }
        }}
        onBlur={(e) => {
          buttonProps.onBlur?.(e);
          setIsFocusVisible(false);
        }}
      >
        <span {...valueProps} style={{ color: selectedItem ? colors.text.primary : colors.text.muted }}>
          {displayValue}
        </span>
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          style={{ marginLeft: "8px", transform: state.isOpen ? "rotate(180deg)" : undefined, transition: "transform 150ms" }}
        >
          <path fill={colors.text.secondary} d="M6 8L1 3h10z" />
        </svg>
      </button>
      {state.isOpen && <ListBox {...menuProps} state={state} listBoxRef={listBoxRef} onClose={() => state.close()} />}
    </div>
  );
}
