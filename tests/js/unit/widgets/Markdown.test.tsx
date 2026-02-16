import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "../../test-utils";
import { Markdown } from "../../../../src/trellis/widgets/client/Markdown";
import { sanitizeMarkdownHtml } from "../../../../src/trellis/widgets/client/markdown_policy";

describe("Markdown", () => {
  it("renders inside shadow dom", () => {
    render(<Markdown content={"# Title"} />);

    const host = screen.getByTestId("markdown-host");
    expect(host.shadowRoot).not.toBeNull();
    expect(host.shadowRoot?.textContent).toContain("Title");
  });

  it("scrubs script tags from html output", () => {
    const html = sanitizeMarkdownHtml("<script>alert(1)</script><p>safe</p>", {});
    expect(html).toContain("safe");
    expect(html).not.toContain("script");
  });

  it("scrubs local resource references when base_path is unset", () => {
    const html = sanitizeMarkdownHtml("<img src=\"./local.png\" />", {});
    expect(html).not.toContain("<img");
  });

  it("allows local resources under base_path", () => {
    const html = sanitizeMarkdownHtml("<img src=\"images/pic.png\" />", {
      base_path: "/project",
    });
    expect(html).toContain("<img");
  });

  it("scrubs local resources outside base_path", () => {
    const html = sanitizeMarkdownHtml("<img src=\"../secret.png\" />", {
      base_path: "/project/subdir",
    });
    expect(html).not.toContain("<img");
  });

  it("forces outbound links to open in new tab", () => {
    const html = sanitizeMarkdownHtml("<a href=\"https://example.com\">external</a>", {});
    expect(html).toContain('target="_blank"');
    expect(html).toContain('rel="noopener noreferrer"');
  });

  it("keeps fragment-only links when base_path is unset", () => {
    const html = sanitizeMarkdownHtml("<a href=\"#section\">jump</a>", {});
    expect(html).toContain('href="#section"');
  });

  it("treats relative base_path as unset for local resource policy", () => {
    const html = sanitizeMarkdownHtml("<img src=\"images/pic.png\" />", {
      base_path: "project",
    });
    expect(html).not.toContain("<img");
  });

  it("treats malformed base_path as unset for local resource policy", () => {
    const html = sanitizeMarkdownHtml("<img src=\"images/pic.png\" />", {
      base_path: "/bad%ZZ",
    });
    expect(html).not.toContain("<img");
  });
});
