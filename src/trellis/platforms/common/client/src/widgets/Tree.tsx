import React, { useState, useCallback } from "react";
import { colors, spacing, typography, radius } from "../theme";
import { Icon } from "./Icon";

interface TreeNode {
  id: string;
  label: string;
  icon?: string;
  children?: TreeNode[];
}

interface TreeProps {
  data?: TreeNode[];
  selected?: string;
  expanded?: string[];
  on_select?: (id: string) => void;
  on_expand?: (id: string, isExpanded: boolean) => void;
  show_icons?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

interface TreeNodeItemProps {
  node: TreeNode;
  level: number;
  selected?: string;
  expanded: Set<string>;
  onSelect?: (id: string) => void;
  onExpand?: (id: string, isExpanded: boolean) => void;
  showIcons: boolean;
}

function TreeNodeItem({
  node,
  level,
  selected,
  expanded,
  onSelect,
  onExpand,
  showIcons,
}: TreeNodeItemProps): React.ReactElement {
  const hasChildren = node.children && node.children.length > 0;
  const isExpanded = expanded.has(node.id);
  const isSelected = selected === node.id;

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (hasChildren) {
      onExpand?.(node.id, !isExpanded);
    }
  };

  const handleSelect = () => {
    onSelect?.(node.id);
  };

  const getIcon = (): string => {
    if (node.icon) return node.icon;
    if (hasChildren) return isExpanded ? "folder-open" : "folder";
    return "file";
  };

  return (
    <div>
      <div
        onClick={handleSelect}
        style={{
          display: "flex",
          alignItems: "center",
          gap: spacing.xs,
          padding: `${spacing.xs}px ${spacing.sm}px`,
          paddingLeft: spacing.sm + level * spacing.lg,
          cursor: "pointer",
          backgroundColor: isSelected ? colors.accent.subtle : "transparent",
          color: isSelected ? colors.accent.primary : colors.text.primary,
          fontSize: typography.fontSize.sm,
          borderRadius: radius.sm,
          transition: "background-color 0.1s ease",
        }}
        onMouseEnter={(e) => {
          if (!isSelected) {
            e.currentTarget.style.backgroundColor = colors.bg.surfaceHover;
          }
        }}
        onMouseLeave={(e) => {
          if (!isSelected) {
            e.currentTarget.style.backgroundColor = "transparent";
          }
        }}
      >
        {/* Expand/collapse chevron */}
        <span
          onClick={handleToggle}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: 16,
            height: 16,
            visibility: hasChildren ? "visible" : "hidden",
          }}
        >
          <Icon
            name={isExpanded ? "chevron-down" : "chevron-right"}
            size={12}
            color={colors.text.secondary}
          />
        </span>

        {/* Node icon */}
        {showIcons && (
          <Icon
            name={getIcon()}
            size={14}
            color={isSelected ? colors.accent.primary : colors.text.secondary}
          />
        )}

        {/* Label */}
        <span
          style={{
            fontWeight: isSelected
              ? typography.fontWeight.medium
              : typography.fontWeight.normal,
          }}
        >
          {node.label}
        </span>
      </div>

      {/* Children */}
      {hasChildren && isExpanded && (
        <div>
          {node.children!.map((child) => (
            <TreeNodeItem
              key={child.id}
              node={child}
              level={level + 1}
              selected={selected}
              expanded={expanded}
              onSelect={onSelect}
              onExpand={onExpand}
              showIcons={showIcons}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function Tree({
  data = [],
  selected,
  expanded: expandedProp,
  on_select,
  on_expand,
  show_icons = true,
  className,
  style,
}: TreeProps): React.ReactElement {
  // Use internal state if not controlled
  const [internalExpanded, setInternalExpanded] = useState<Set<string>>(
    new Set(expandedProp || [])
  );

  const expanded = expandedProp ? new Set(expandedProp) : internalExpanded;

  const handleExpand = useCallback(
    (id: string, isExpanded: boolean) => {
      if (on_expand) {
        on_expand(id, isExpanded);
      } else {
        setInternalExpanded((prev) => {
          const next = new Set(prev);
          if (isExpanded) {
            next.add(id);
          } else {
            next.delete(id);
          }
          return next;
        });
      }
    },
    [on_expand]
  );

  return (
    <div
      className={className}
      style={{
        fontFamily: typography.fontFamily,
        ...style,
      }}
    >
      {data.map((node) => (
        <TreeNodeItem
          key={node.id}
          node={node}
          level={0}
          selected={selected}
          expanded={expanded}
          onSelect={on_select}
          onExpand={handleExpand}
          showIcons={show_icons}
        />
      ))}
    </div>
  );
}
