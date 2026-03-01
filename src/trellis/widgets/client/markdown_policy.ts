import DOMPurify from "dompurify";

export interface MarkdownPolicyOptions {
  base_path?: string | null;
}

const WEB_PROTOCOLS = new Set(["http:", "https:"]);
const LINK_PROTOCOLS = new Set(["http:", "https:", "mailto:", "tel:"]);

function hasExplicitScheme(value: string): boolean {
  return /^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(value);
}

function normalizePath(path: string): string {
  const decoded = decodeURIComponent(path).replace(/\\/g, "/");
  const isAbsolute = decoded.startsWith("/");
  const segments: string[] = [];
  for (const segment of decoded.split("/")) {
    if (!segment || segment === ".") {
      continue;
    }
    if (segment === "..") {
      if (segments.length > 0) {
        segments.pop();
      }
      continue;
    }
    segments.push(segment);
  }
  return `${isAbsolute ? "/" : ""}${segments.join("/")}`;
}

function normalizeBasePath(basePath: string): string | null {
  try {
    const normalizedBase = normalizePath(basePath);
    if (!normalizedBase.startsWith("/")) {
      return null;
    }
    return normalizedBase;
  } catch {
    return null;
  }
}

function toBaseFileUrl(basePath: string): URL | null {
  const normalizedBase = normalizeBasePath(basePath);
  if (normalizedBase === null) {
    return null;
  }
  const withSlash = normalizedBase.endsWith("/") ? normalizedBase : `${normalizedBase}/`;
  return new URL(`file://${withSlash}`);
}

function resolveLocalReference(reference: string, basePath: string): string | null {
  try {
    if (reference.startsWith("file://")) {
      return normalizePath(new URL(reference).pathname);
    }
    if (hasExplicitScheme(reference)) {
      return null;
    }
    const baseUrl = toBaseFileUrl(basePath);
    if (baseUrl === null) {
      return null;
    }
    const resolved = new URL(reference, baseUrl);
    if (resolved.protocol !== "file:") {
      return null;
    }
    return normalizePath(resolved.pathname);
  } catch {
    return null;
  }
}

function isWithinBasePath(reference: string, basePath: string): boolean {
  const candidate = resolveLocalReference(reference, basePath);
  if (candidate === null) {
    return false;
  }
  const normalizedBase = normalizeBasePath(basePath);
  if (normalizedBase === null) {
    return false;
  }
  return candidate === normalizedBase || candidate.startsWith(`${normalizedBase}/`);
}

function isWebUrl(reference: string): boolean {
  try {
    const parsed = new URL(reference);
    return WEB_PROTOCOLS.has(parsed.protocol);
  } catch {
    return false;
  }
}

function shouldKeepResourceReference(reference: string, basePath?: string | null): boolean {
  if (!reference) {
    return false;
  }
  if (isWebUrl(reference)) {
    return true;
  }
  if (!basePath) {
    return false;
  }
  return isWithinBasePath(reference, basePath);
}

function applyResourcePolicy(container: HTMLElement, basePath?: string | null): void {
  const selectors = [
    "img[src]",
    "audio[src]",
    "video[src]",
    "source[src]",
    "iframe[src]",
    "embed[src]",
    "object[data]",
    "link[href]",
  ];
  const elements = container.querySelectorAll<HTMLElement>(selectors.join(","));

  for (const element of elements) {
    const attribute = element.hasAttribute("src")
      ? "src"
      : element.hasAttribute("data")
        ? "data"
        : "href";
    const reference = element.getAttribute(attribute) ?? "";
    if (!shouldKeepResourceReference(reference, basePath)) {
      element.remove();
    }
  }
}

function applyLinkPolicy(container: HTMLElement, basePath?: string | null): void {
  for (const anchor of container.querySelectorAll<HTMLAnchorElement>("a[href]")) {
    const reference = anchor.getAttribute("href") ?? "";
    if (!reference) {
      anchor.removeAttribute("href");
      continue;
    }

    if (reference.startsWith("#")) {
      continue;
    }

    if (hasExplicitScheme(reference)) {
      try {
        const protocol = new URL(reference).protocol;
        if (!LINK_PROTOCOLS.has(protocol)) {
          anchor.removeAttribute("href");
          continue;
        }
      } catch {
        anchor.removeAttribute("href");
        continue;
      }
    } else if (!basePath || !isWithinBasePath(reference, basePath)) {
      anchor.removeAttribute("href");
      continue;
    }

    if (isWebUrl(reference)) {
      anchor.setAttribute("target", "_blank");
      anchor.setAttribute("rel", "noopener noreferrer");
    }
  }
}

export function sanitizeMarkdownHtml(rawHtml: string, options: MarkdownPolicyOptions): string {
  const clean = DOMPurify.sanitize(rawHtml, {
    USE_PROFILES: { html: true },
    FORBID_TAGS: ["script", "style"],
    FORBID_ATTR: ["style"],
  });

  const container = document.createElement("div");
  container.innerHTML = clean;
  applyResourcePolicy(container, options.base_path);
  applyLinkPolicy(container, options.base_path);
  return container.innerHTML;
}
