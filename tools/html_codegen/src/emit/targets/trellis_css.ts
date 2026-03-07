import type { CssDocument, CssMediaFeatureDef, CssPropertyDef, CssValueAliasDef } from "../../ir/types.js";
import { render_type_expr } from "../python/render_types.js";
import { render_generated_module_docstring } from "./generated_metadata.js";

import type { TrellisModulePayload } from "./trellis_html.js";

function sort_by_name<T extends { name?: string; python_name?: string }>(items: T[]): T[] {
  return [...items].sort((left, right) =>
    (left.name ?? left.python_name ?? "").localeCompare(right.name ?? right.python_name ?? ""),
  );
}

function emit_aliases(aliases: CssValueAliasDef[]): string[] {
  const lines: string[] = [];
  for (const alias of sort_by_name(aliases)) {
    lines.push(`${alias.name} = ${render_type_expr(alias.type_expr)}`);
  }
  return lines;
}

function emit_style_fields(properties: CssPropertyDef[]): string[] {
  const lines = ["@dataclass(kw_only=True)", "class _GeneratedStyleFields:"];
  for (const property of [...properties].sort((left, right) => left.python_name.localeCompare(right.python_name))) {
    lines.push(`    ${property.python_name}: ${property.value_type_name} | None = None`);
  }
  if (properties.length === 0) {
    lines.push("    pass");
  }
  return lines;
}

function emit_media_rule(media_features: CssMediaFeatureDef[]): string[] {
  const lines = ["@dataclass(frozen=True, kw_only=True)", "class MediaRule:"];
  for (const feature of [...media_features].sort((left, right) => left.python_name.localeCompare(right.python_name))) {
    lines.push(`    ${feature.python_name}: ${feature.value_type_name} | None = None`);
  }
  lines.push('    query: str | None = None');
  lines.push('    style: "Style"');
  return lines;
}

function emit_types_module(document: CssDocument, generated_at: string): string {
  const aliases = emit_aliases(document.value_aliases);
  const style_fields = emit_style_fields(document.properties);
  const media_rule = emit_media_rule(document.media_features);
  return [
    render_generated_module_docstring("Generated CSS style type declarations.", generated_at),
    "from __future__ import annotations",
    "",
    "from dataclasses import dataclass",
    "from typing import Literal",
    "",
    "from trellis.html._css_primitives import CssAngle, CssColor, CssLength, CssPercent, CssTime, CssValue",
    "",
    ...aliases,
    "",
    ...style_fields,
    "",
    ...media_rule,
    "",
  ].join("\n");
}

function emit_metadata_module(document: CssDocument, generated_at: string): string {
  const css_name_by_field = [...document.properties]
    .sort((left, right) => left.python_name.localeCompare(right.python_name))
    .map((property) => `    "${property.python_name}": "${property.css_name}",`)
    .join("\n");

  const auto_px_fields = [...document.properties]
    .filter((property) => property.accepts_auto_px)
    .sort((left, right) => left.python_name.localeCompare(right.python_name))
    .map((property) => `    "${property.python_name}",`)
    .join("\n");

  const shorthand_fields = [...document.properties]
    .filter((property) => property.is_shorthand)
    .sort((left, right) => left.python_name.localeCompare(right.python_name))
    .map((property) => `    "${property.python_name}",`)
    .join("\n");

  return [
    render_generated_module_docstring("Generated CSS style metadata.", generated_at),
    "from __future__ import annotations",
    "",
    "CSS_NAME_BY_FIELD = {",
    css_name_by_field,
    "}",
    "",
    "AUTO_PX_FIELDS = frozenset({",
    auto_px_fields,
    "})",
    "",
    "SHORTHAND_FIELDS = frozenset({",
    shorthand_fields,
    "})",
    "",
  ].join("\n");
}

export function build_trellis_css_modules(
  document: CssDocument,
  generated_at: string,
): TrellisModulePayload[] {
  return [
    {
      path: "src/trellis/html/_generated_style_types.py",
      content: emit_types_module(document, generated_at),
    },
    {
      path: "src/trellis/html/_generated_style_metadata.py",
      content: emit_metadata_module(document, generated_at),
    },
  ];
}
