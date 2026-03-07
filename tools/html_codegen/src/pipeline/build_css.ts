import type { CssDocument, CssMediaFeatureDef, CssPropertyDef, CssValueAliasDef, SourceProvenance, TypeExpr } from "../ir/types.js";
import { extract_css_surface } from "../sources/webref_css.js";

function alias_source(reason: string): SourceProvenance {
  return {
    winner: "webref",
    contributors: ["webref", "csstype"],
    reason,
    source_version: "@webref/css@8.4.0",
  };
}

export async function build_css_document(): Promise<CssDocument> {
  const surface = await extract_css_surface();
  const properties: CssPropertyDef[] = [...surface.properties.values()].sort((left, right) =>
    left.css_name.localeCompare(right.css_name),
  );
  const media_features: CssMediaFeatureDef[] = [...surface.media_features.values()].sort((left, right) =>
    left.css_name.localeCompare(right.css_name),
  );
  const value_aliases: CssValueAliasDef[] = [...surface.value_aliases.entries()]
    .filter(([name]) => !["CssValue", "CssLength", "CssPercent", "CssColor", "CssTime", "CssAngle"].includes(name))
    .map(([name, type_expr]): CssValueAliasDef => ({
      name,
      type_expr,
      source: alias_source("css_value_alias"),
    }))
    .sort((left, right) => left.name.localeCompare(right.name));

  return {
    properties,
    media_features,
    value_aliases,
  };
}
