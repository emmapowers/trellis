import React, { useState, useCallback, useRef, useMemo } from "react";
import { colors, spacing, typography, radius, focusRing } from "@trellis/trellis-core/theme";
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

interface FlattenedNode {
  node: TreeNode;
  level: number;
  parent?: string;
}

interface TreeNodeItemProps {
  node: TreeNode;
  level: number;
  selected?: string;
  expanded: Set<string>;
  onSelect?: (id: string) => void;
  onExpand?: (id: string, isExpanded: boolean) => void;
  showIcons: boolean;
  isFocused: boolean;
  setSize: number;
  posInSet: number;
}

function TreeNodeItem({
  node,
  level,
  selected,
  expanded,
  onSelect,
  onExpand,
  showIcons,
  isFocused,
  setSize,
  posInSet,
}: TreeNodeItemProps): React.ReactElement {
  const ref = useRef<HTMLDivElement>(null);
  const hasChildren = node.children && node.children.length > 0;
  const isExpanded = expanded.has(node.id);
  const isSelected = selected === node.id;
  const [isFocusVisible, setIsFocusVisible] = React.useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const handleToggle = (e: React.MouseEvent | React.KeyboardEvent) => {
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

  // Focus this element when it becomes the focused node
  React.useEffect(() => {
    if (isFocused && ref.current) {
      ref.current.focus();
    }
  }, [isFocused]);

  return (
    <div
      role="treeitem"
      ref={ref}
      tabIndex={isFocused ? 0 : -1}
      aria-selected={isSelected}
      aria-expanded={hasChildren ? isExpanded : undefined}
      aria-level={level + 1}
      aria-setsize={setSize}
      aria-posinset={posInSet}
      data-node-id={node.id}
      onClick={handleSelect}
      onKeyDown={(e) => {
        // Let parent handle navigation keys
        if (["ArrowUp", "ArrowDown", "Home", "End"].includes(e.key)) {
          return;
        }
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          handleSelect();
        } else if (e.key === "ArrowRight") {
          e.preventDefault();
          if (hasChildren && !isExpanded) {
            onExpand?.(node.id, true);
          }
        } else if (e.key === "ArrowLeft") {
          e.preventDefault();
          if (hasChildren && isExpanded) {
            onExpand?.(node.id, false);
          }
        }
      }}
      onFocus={(e) => {
        if (e.target.matches(":focus-visible")) {
          setIsFocusVisible(true);
        }
      }}
      onBlur={() => setIsFocusVisible(false)}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        display: "flex",
        alignItems: "center",
        gap: spacing.xs,
        padding: `${spacing.xs}px ${spacing.sm}px`,
        paddingLeft: spacing.sm + level * spacing.lg,
        cursor: "pointer",
        backgroundColor: isSelected
          ? colors.accent.subtle
          : isHovered
            ? colors.bg.surfaceHover
            : "transparent",
        color: isSelected ? colors.accent.primary : colors.text.primary,
        fontSize: typography.fontSize.sm,
        borderRadius: radius.sm,
        transition: "background-color 0.1s ease",
        outline: "none",
        ...(isFocusVisible ? focusRing : {}),
      }}
    >
      {/* Expand/collapse chevron */}
      <span
        role="button"
        aria-label={hasChildren ? (isExpanded ? "Collapse" : "Expand") : undefined}
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
  );
}

// Flatten tree to get visible nodes for keyboard navigation
function flattenVisibleNodes(
  nodes: TreeNode[],
  expanded: Set<string>,
  level: number = 0,
  parent?: string
): FlattenedNode[] {
  const result: FlattenedNode[] = [];
  for (const node of nodes) {
    result.push({ node, level, parent });
    if (node.children && node.children.length > 0 && expanded.has(node.id)) {
      result.push(...flattenVisibleNodes(node.children, expanded, level + 1, node.id));
    }
  }
  return result;
}

// Recursive component to render tree with proper nesting for accessibility
function TreeGroup({
  nodes,
  level,
  selected,
  expanded,
  onSelect,
  onExpand,
  showIcons,
  focusedId,
}: {
  nodes: TreeNode[];
  level: number;
  selected?: string;
  expanded: Set<string>;
  onSelect?: (id: string) => void;
  onExpand?: (id: string, isExpanded: boolean) => void;
  showIcons: boolean;
  focusedId: string | null;
}): React.ReactElement {
  return (
    <>
      {nodes.map((node, index) => {
        const hasChildren = node.children && node.children.length > 0;
        const isExpanded = expanded.has(node.id);

        return (
          <React.Fragment key={node.id}>
            <TreeNodeItem
              node={node}
              level={level}
              selected={selected}
              expanded={expanded}
              onSelect={onSelect}
              onExpand={onExpand}
              showIcons={showIcons}
              isFocused={focusedId === node.id}
              setSize={nodes.length}
              posInSet={index + 1}
            />
            {hasChildren && isExpanded && (
              <div role="group">
                <TreeGroup
                  nodes={node.children!}
                  level={level + 1}
                  selected={selected}
                  expanded={expanded}
                  onSelect={onSelect}
                  onExpand={onExpand}
                  showIcons={showIcons}
                  focusedId={focusedId}
                />
              </div>
            )}
          </React.Fragment>
        );
      })}
    </>
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
  const treeRef = useRef<HTMLDivElement>(null);

  // Use internal state if not controlled
  const [internalExpanded, setInternalExpanded] = useState<Set<string>>(
    new Set(expandedProp || [])
  );

  const expanded = expandedProp ? new Set(expandedProp) : internalExpanded;

  // Track focused node for keyboard navigation
  const [focusedId, setFocusedId] = useState<string | null>(null);

  // Get flattened visible nodes for keyboard navigation
  const visibleNodes = useMemo(
    () => flattenVisibleNodes(data, expanded),
    [data, expanded]
  );

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

  // Handle keyboard navigation at tree level
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (visibleNodes.length === 0) return;

    const currentIndex = focusedId
      ? visibleNodes.findIndex((n) => n.node.id === focusedId)
      : -1;

    switch (e.key) {
      case "ArrowDown": {
        e.preventDefault();
        const nextIndex = currentIndex < visibleNodes.length - 1 ? currentIndex + 1 : 0;
        setFocusedId(visibleNodes[nextIndex].node.id);
        break;
      }
      case "ArrowUp": {
        e.preventDefault();
        const prevIndex = currentIndex > 0 ? currentIndex - 1 : visibleNodes.length - 1;
        setFocusedId(visibleNodes[prevIndex].node.id);
        break;
      }
      case "ArrowLeft": {
        e.preventDefault();
        if (currentIndex >= 0) {
          const current = visibleNodes[currentIndex];
          const hasChildren = current.node.children && current.node.children.length > 0;
          const isExpanded = expanded.has(current.node.id);

          if (hasChildren && isExpanded) {
            // Collapse current node
            handleExpand(current.node.id, false);
          } else if (current.parent) {
            // Move to parent
            setFocusedId(current.parent);
          }
        }
        break;
      }
      case "ArrowRight": {
        e.preventDefault();
        if (currentIndex >= 0) {
          const current = visibleNodes[currentIndex];
          const hasChildren = current.node.children && current.node.children.length > 0;
          const isExpanded = expanded.has(current.node.id);

          if (hasChildren) {
            if (!isExpanded) {
              // Expand current node
              handleExpand(current.node.id, true);
            } else if (current.node.children && current.node.children.length > 0) {
              // Move to first child
              setFocusedId(current.node.children[0].id);
            }
          }
        }
        break;
      }
      case "Home": {
        e.preventDefault();
        if (visibleNodes.length > 0) {
          setFocusedId(visibleNodes[0].node.id);
        }
        break;
      }
      case "End": {
        e.preventDefault();
        if (visibleNodes.length > 0) {
          setFocusedId(visibleNodes[visibleNodes.length - 1].node.id);
        }
        break;
      }
    }
  };

  // Initialize focus to first node on first focus
  const handleFocus = (e: React.FocusEvent) => {
    if (e.target === treeRef.current && !focusedId && visibleNodes.length > 0) {
      setFocusedId(visibleNodes[0].node.id);
    }
  };

  return (
    <div
      ref={treeRef}
      role="tree"
      aria-label="Tree"
      className={className}
      tabIndex={focusedId ? -1 : 0}
      onKeyDown={handleKeyDown}
      onFocus={handleFocus}
      style={{
        fontFamily: typography.fontFamily,
        outline: "none",
        ...style,
      }}
    >
      <TreeGroup
        nodes={data}
        level={0}
        selected={selected}
        expanded={expanded}
        onSelect={on_select}
        onExpand={handleExpand}
        showIcons={show_icons}
        focusedId={focusedId}
      />
    </div>
  );
}
