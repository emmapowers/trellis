import React from "react";
import MarkdownIt from "markdown-it";
import { colors, spacing, typography } from "@trellis/trellis-core/theme";
import { sanitizeMarkdownHtml } from "./markdown_policy";

interface MarkdownProps {
  content?: string;
  base_path?: string | null;
  className?: string;
  style?: React.CSSProperties;
}

const markdownParser = new MarkdownIt({
  html: true,
  linkify: true,
  breaks: true,
});

const shadowStyles = `
  :host {
    display: block;
    color: ${colors.text.primary};
    font-size: ${typography.fontSize.md}px;
    line-height: 1.5;
  }
  .trellis-markdown-root {
    display: block;
    width: 100%;
  }
  .trellis-markdown-root p {
    margin: 0 0 ${spacing.md}px 0;
  }
  .trellis-markdown-root h1,
  .trellis-markdown-root h2,
  .trellis-markdown-root h3,
  .trellis-markdown-root h4,
  .trellis-markdown-root h5,
  .trellis-markdown-root h6 {
    margin: 0 0 ${spacing.sm}px 0;
    line-height: 1.25;
  }
  .trellis-markdown-root code {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    background: ${colors.neutral[100]};
    padding: 0 4px;
    border-radius: 4px;
  }
  .trellis-markdown-root pre {
    overflow: auto;
    margin: 0 0 ${spacing.md}px 0;
    padding: ${spacing.sm}px;
    border: 1px solid ${colors.border.default};
    border-radius: 6px;
    background: ${colors.neutral[50]};
  }
  .trellis-markdown-root pre code {
    background: transparent;
    padding: 0;
  }
  .trellis-markdown-root a {
    color: ${colors.accent.primary};
  }
  .trellis-markdown-root img {
    max-width: 100%;
    height: auto;
  }
`;

export function Markdown({
  content = "",
  base_path = null,
  className,
  style,
}: MarkdownProps): React.ReactElement {
  const hostRef = React.useRef<HTMLDivElement>(null);

  const sanitizedHtml = React.useMemo(() => {
    const rendered = markdownParser.render(content);
    return sanitizeMarkdownHtml(rendered, { base_path });
  }, [content, base_path]);

  React.useEffect(() => {
    const host = hostRef.current;
    if (!host) {
      return;
    }

    const shadowRoot = host.shadowRoot ?? host.attachShadow({ mode: "open" });
    shadowRoot.innerHTML = `<style>${shadowStyles}</style><article class="trellis-markdown-root">${sanitizedHtml}</article>`;
  }, [sanitizedHtml]);

  return (
    <div
      ref={hostRef}
      data-testid="markdown-host"
      className={className}
      style={{
        width: "100%",
        ...style,
      }}
    />
  );
}
