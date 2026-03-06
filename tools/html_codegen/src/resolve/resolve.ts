import type { IrDocument, SourceWinner } from "../ir/types.js";
import type { NormalizeInput, RawAttributeRecord } from "../normalize/normalize.js";
import { camel_or_kebab_to_snake } from "./name_map.js";

function choose_winner(
  candidates: RawAttributeRecord[],
): { winner: RawAttributeRecord; winner_name: SourceWinner; contributors: string[] } {
  const react = candidates.find((candidate) => candidate.source === "react_ts");
  if (react) {
    return {
      winner: react,
      winner_name: "react_ts",
      contributors: [...new Set(candidates.map((candidate) => candidate.source))],
    };
  }

  return {
    winner: candidates[0],
    winner_name: "webref",
    contributors: [...new Set(candidates.map((candidate) => candidate.source))],
  };
}

export function resolve_ir(input: NormalizeInput): IrDocument {
  const attributes_by_id = new Map<string, RawAttributeRecord[]>();
  for (const attribute of input.attributes) {
    const existing = attributes_by_id.get(attribute.id) ?? [];
    existing.push(attribute);
    attributes_by_id.set(attribute.id, existing);
  }

  const attributes = [...attributes_by_id.entries()].map(([id, candidates]) => {
    const picked = choose_winner(candidates);
    return {
      id,
      name_source: picked.winner.name_source,
      name_python: camel_or_kebab_to_snake(picked.winner.name_source),
      applies_to: "element" as const,
      type_expr: picked.winner.type_expr,
      required: false,
      category: "standard" as const,
      source: {
        winner: picked.winner_name,
        contributors: picked.contributors,
        reason: picked.contributors.length > 1 ? "runtime_precedence" : "single_source",
        source_version: "unversioned",
      },
    };
  });

  return {
    elements: [],
    attributes,
    events: [],
    attribute_patterns: [],
  };
}
