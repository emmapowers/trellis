# HTML IR + Codegen Design

## Summary

Build a TypeScript-only, in-repo developer tool that ingests React/TS + webref
sources, resolves them into a normalized Intermediate Representation (IR), and
generates Trellis HTML Python APIs from that IR.

The system is runtime-first: React/TS compatibility wins when sources disagree,
because Trellis renders through React and must compile and run correctly.

## Goals

- Generate a complete, consistent HTML API surface from authoritative sources.
- Enforce strict typing for generated Python APIs (including `Literal[...]` unions).
- Keep Python API snake_case-only.
- Preserve deterministic output and explainable diffs with provenance.
- Keep the generator in the Trellis repo, but out of the distributed Python package.

## Non-Goals (v1)

- CSS typed system.
- DOM API wrappers.
- SVG/MathML generation output.
- Experimental/browser-specific attribute output.
- Published package/artifact pipeline.

## Source Strategy

Primary runtime compatibility source:

- `@types/react` (element inclusion, prop names/types, event handler names/signatures).

Specification/enrichment sources:

- `@webref/elements`
- `@webref/events`
- `@webref/idl`

The resolver is runtime-first. Webref fills missing data and contributes metadata.

## Architecture

Pipeline stages:

1. `sources/react_ts`: parse `@types/react` intrinsic elements, props, and events.
2. `sources/webref`: parse webref element/event/IDL data.
3. `normalize`: map into canonical IR records.
4. `resolve`: apply deterministic precedence and conflict rules.
5. `validate`: enforce IR and emission invariants.
6. `emit`: generate Python HTML modules + tests.
7. `artifacts`: write IR snapshot and diff report.

Outputs are deterministic and fully reviewable in git.

## IR Schema (v1)

Core entities:

- `ElementDef`
- `AttributeDef`
- `EventDef`
- `TypeExpr`
- `SourceProvenance`
- `AttributePatternDef` (for explicit dynamic namespaces like data attributes)

### `ElementDef`

- `namespace`: `"html"` for generated output (IR remains namespace-aware for future).
- `tag_name`: source tag name.
- `python_name`: generated symbol name.
- `is_container`: bool.
- `attributes`: references to `AttributeDef`.
- `events`: references to `EventDef`.
- `source`: provenance summary.

### `AttributeDef`

- `id`: stable identifier (`namespace:element:attribute`).
- `name_source`: original source/runtime attribute name.
- `name_python`: snake_case API name.
- `applies_to`: global or element-scoped.
- `type_expr`: strict type expression.
- `required`: bool.
- `default`: optional default.
- `category`: `standard | aria | data`.
- `source`: winner/contributors/reason metadata.

### `EventDef`

- `name_source`: source event handler name.
- `name_python`: snake_case event handler name.
- `handler_signature`: normalized callable signature.
- `event_payload`: typed payload reference.
- `source`: winner/contributors/reason metadata.

### `TypeExpr`

Recursive type node:

- `literal`
- `union`
- `primitive`
- `array`
- `object`
- `callable`
- `reference`
- `nullable`

Literal unions stay strict in emitted Python APIs.

### `SourceProvenance`

- `winner`: `react_ts | webref`.
- `contributors`: list of source records.
- `reason`: resolution reason code.
- `source_version`: version/hash metadata for reproducibility.

### `AttributePatternDef` (dynamic-name lane)

For v1 this is used for data attributes:

- Python API exposes a dedicated `data` parameter.
- `data` type: `Mapping[str, DataValue] | None`.
- `DataValue`: `str | int | float | bool | None`.
- Keys are DOM-style suffixes as-is (example: `"test-id"` -> `data-test-id`).
- No snake_case key transform for `data` mapping keys.

## Conflict Resolution Rules

Priority order:

1. React/TS (`@types/react`) wins for runtime-facing behavior.
2. webref fills missing fields and contributes metadata.
3. Trellis policy transforms apply last (snake_case mapping, strictness rules).

Type rules:

- Strict literals only (no `Literal[...] | str` widening for known bounded sets).
- Open-ended source types remain open-ended (`str`, etc.).
- No broad catch-all kwargs in emitted component signatures.

Name rules:

- Generated Python API names are snake_case only.
- Original source names are retained in IR provenance.

Scope rules:

- Generate HTML output only in v1.
- Exclude experimental/browser-specific output in v1.
- Keep IR namespace-aware for future SVG/MathML support.

## Generated API Rules

- Closed signatures for each element.
- Unknown non-data attributes are rejected (type-check and runtime validation).
- No `**kwargs` in generated component APIs.
- Hybrid text/container behavior remains explicitly modeled.

## Tech Stack

- Node 22
- TypeScript 5.x
- pnpm
- `ts-morph` (or TS compiler API) for React type extraction
- `webidl2` for IDL parsing
- `zod` for IR schema validation
- `vitest` for generator tests

Generator location:

- In repo, e.g. `tools/html_codegen/`
- Not part of distributed Trellis Python package.

Execution model:

- Manual developer command (no pixi task required).
- Developer runs generator, reviews diffs, commits generated results.

## Validation and Testing

Validation gates:

1. IR schema validation.
2. Resolver invariant checks (no unresolved conflicts, unique Python names, no camelCase leaks in emitted API).
3. Emitted code validation (`mypy`, lint, and tests in Trellis).

Tests:

- Golden IR snapshot tests.
- Resolver precedence tests.
- Codegen snapshot/tests for generated Python signatures.
- Event round-trip tests (frontend serialization to Python typed event payloads).
- `data` mapping tests (`{"test-id": "x"}` -> `data-test-id="x"`).

## Rollout Plan

1. Implement generator with compare mode first (report-only).
2. Compare against current handwritten HTML layer.
3. Resolve intentional differences via policy/adapter updates.
4. Switch HTML modules to generated output.
5. Commit generated code + IR snapshot for review.
6. Later phases: SVG/MathML output, CSS typing, DOM wrapper generation.

## Future Extensions

- CSS typed system can plug into the same IR + resolver framework.
- DOM API wrappers (for future JsProxy system) can reuse provenance, type model, and codegen patterns.

