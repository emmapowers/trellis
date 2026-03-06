# HTML IR + Codegen Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an in-repo TypeScript generator that builds a runtime-first HTML IR from React + webref sources and emits strict, snake_case Trellis HTML Python APIs.

**Architecture:** A staged pipeline under `tools/html_codegen/` ingests source adapters (`@types/react`, `@webref/*`), normalizes and resolves into a validated IR with provenance, then emits deterministic Python modules and tests. Resolver precedence is runtime-first (React/TS wins), with webref as metadata/fill-in.

**Tech Stack:** Node 22, TypeScript 5, pnpm, ts-morph, @webref/elements, @webref/events, @webref/idl, webidl2, zod, vitest.

---

### Task 1: Scaffold generator project

**Files:**
- Create: `tools/html_codegen/package.json`
- Create: `tools/html_codegen/tsconfig.json`
- Create: `tools/html_codegen/vitest.config.ts`
- Create: `tools/html_codegen/src/cli.ts`
- Create: `tools/html_codegen/src/index.ts`
- Create: `tools/html_codegen/README.md`
- Test: `tools/html_codegen/tests/cli_smoke.test.ts`

**Step 1: Write the failing test**

```ts
import { describe, expect, it } from "vitest";
import { runCli } from "../src/cli";

describe("cli smoke", () => {
  it("supports --help", async () => {
    const result = await runCli(["--help"]);
    expect(result.exit_code).toBe(0);
    expect(result.stdout).toContain("html-codegen");
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd tools/html_codegen && pnpm test cli_smoke.test.ts`
Expected: FAIL because CLI scaffolding does not exist.

**Step 3: Write minimal implementation**

Add minimal package config, Vitest config, and `runCli` handler for `--help`.

**Step 4: Run test to verify it passes**

Run: `cd tools/html_codegen && pnpm test cli_smoke.test.ts`
Expected: PASS.

**Step 5: Commit**

```bash
git add tools/html_codegen
git commit -m "chore: scaffold html codegen tool"
```

### Task 2: Define IR schema and invariants

**Files:**
- Create: `tools/html_codegen/src/ir/schema.ts`
- Create: `tools/html_codegen/src/ir/types.ts`
- Test: `tools/html_codegen/tests/ir_schema.test.ts`

**Step 1: Write the failing test**

```ts
import { describe, expect, it } from "vitest";
import { ir_schema } from "../src/ir/schema";

describe("ir schema", () => {
  it("rejects attribute without provenance winner", () => {
    const result = ir_schema.safeParse({ elements: [], attributes: [{ id: "x" }], events: [] });
    expect(result.success).toBe(false);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd tools/html_codegen && pnpm test ir_schema.test.ts`
Expected: FAIL because schema is missing.

**Step 3: Write minimal implementation**

Define `zod` schemas for:
- `ElementDef`
- `AttributeDef`
- `EventDef`
- `TypeExpr`
- `SourceProvenance`
- `AttributePatternDef` (`data` support model)

Add invariants:
- snake_case `name_python`
- allowed namespaces include `html`
- strict source winner enum

**Step 4: Run test to verify it passes**

Run: `cd tools/html_codegen && pnpm test ir_schema.test.ts`
Expected: PASS.

**Step 5: Commit**

```bash
git add tools/html_codegen/src/ir tools/html_codegen/tests/ir_schema.test.ts
git commit -m "feat: add validated IR schema for html codegen"
```

### Task 3: Implement React/TS source adapter

**Files:**
- Create: `tools/html_codegen/src/sources/react_ts.ts`
- Create: `tools/html_codegen/src/sources/ts_helpers.ts`
- Test: `tools/html_codegen/tests/react_source.test.ts`

**Step 1: Write the failing test**

```ts
import { describe, expect, it } from "vitest";
import { extract_react_surface } from "../src/sources/react_ts";

describe("react source extraction", () => {
  it("extracts input type literal union and onClick event", async () => {
    const surface = await extract_react_surface();
    const input = surface.elements.get("input");
    expect(input?.attributes.get("type")?.kind).toBe("union");
    expect(input?.events.has("onClick")).toBe(true);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd tools/html_codegen && pnpm test react_source.test.ts`
Expected: FAIL because adapter is missing.

**Step 3: Write minimal implementation**

Use `ts-morph` to parse `@types/react` and extract:
- intrinsic elements
- attribute types per element
- global/DOM event handler names and payload types

**Step 4: Run test to verify it passes**

Run: `cd tools/html_codegen && pnpm test react_source.test.ts`
Expected: PASS.

**Step 5: Commit**

```bash
git add tools/html_codegen/src/sources tools/html_codegen/tests/react_source.test.ts
git commit -m "feat: extract html surface from react type definitions"
```

### Task 4: Implement webref source adapters

**Files:**
- Create: `tools/html_codegen/src/sources/webref_elements.ts`
- Create: `tools/html_codegen/src/sources/webref_events.ts`
- Create: `tools/html_codegen/src/sources/webref_idl.ts`
- Test: `tools/html_codegen/tests/webref_sources.test.ts`

**Step 1: Write the failing test**

```ts
import { describe, expect, it } from "vitest";
import { extract_webref_surface } from "../src/sources/webref_elements";

describe("webref extraction", () => {
  it("loads html element metadata", async () => {
    const surface = await extract_webref_surface();
    expect(surface.elements.has("button")).toBe(true);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd tools/html_codegen && pnpm test webref_sources.test.ts`
Expected: FAIL because adapters are missing.

**Step 3: Write minimal implementation**

Parse `@webref/elements`, `@webref/events`, and `@webref/idl` (via `webidl2`) into
normalized source records.

**Step 4: Run test to verify it passes**

Run: `cd tools/html_codegen && pnpm test webref_sources.test.ts`
Expected: PASS.

**Step 5: Commit**

```bash
git add tools/html_codegen/src/sources tools/html_codegen/tests/webref_sources.test.ts
git commit -m "feat: add webref adapters for elements events and idl"
```

### Task 5: Build normalizer and resolver (runtime-first precedence)

**Files:**
- Create: `tools/html_codegen/src/normalize/normalize.ts`
- Create: `tools/html_codegen/src/resolve/resolve.ts`
- Create: `tools/html_codegen/src/resolve/name_map.ts`
- Test: `tools/html_codegen/tests/resolve_precedence.test.ts`

**Step 1: Write the failing test**

```ts
import { describe, expect, it } from "vitest";
import { resolve_ir } from "../src/resolve/resolve";

describe("resolver precedence", () => {
  it("prefers react types and records provenance reason", () => {
    const ir = resolve_ir(/* fixture with conflict */);
    const attr = ir.attributes.find((a) => a.id === "html:video:auto_play");
    expect(attr?.source.winner).toBe("react_ts");
    expect(attr?.source.reason).toBe("runtime_precedence");
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd tools/html_codegen && pnpm test resolve_precedence.test.ts`
Expected: FAIL because resolver is missing.

**Step 3: Write minimal implementation**

Implement deterministic precedence:
- React/TS wins conflicts.
- webref fills missing.
- map names to snake_case.
- build provenance records.

**Step 4: Run test to verify it passes**

Run: `cd tools/html_codegen && pnpm test resolve_precedence.test.ts`
Expected: PASS.

**Step 5: Commit**

```bash
git add tools/html_codegen/src/normalize tools/html_codegen/src/resolve tools/html_codegen/tests/resolve_precedence.test.ts
git commit -m "feat: add runtime-first ir resolver with provenance"
```

### Task 6: Add strict validation and policy checks

**Files:**
- Create: `tools/html_codegen/src/validate/policies.ts`
- Create: `tools/html_codegen/src/validate/validate_ir.ts`
- Test: `tools/html_codegen/tests/validate_policies.test.ts`

**Step 1: Write the failing test**

```ts
import { describe, expect, it } from "vitest";
import { validate_ir } from "../src/validate/validate_ir";

describe("policy validation", () => {
  it("rejects non-snake-case python names", () => {
    const result = validate_ir(/* fixture with className */);
    expect(result.ok).toBe(false);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd tools/html_codegen && pnpm test validate_policies.test.ts`
Expected: FAIL because validator is missing.

**Step 3: Write minimal implementation**

Enforce:
- snake_case generated names
- no unresolved conflicts
- strict literal encoding
- no wildcard kwargs policy in emitted signatures
- only approved namespaces emitted for v1 (`html`)

**Step 4: Run test to verify it passes**

Run: `cd tools/html_codegen && pnpm test validate_policies.test.ts`
Expected: PASS.

**Step 5: Commit**

```bash
git add tools/html_codegen/src/validate tools/html_codegen/tests/validate_policies.test.ts
git commit -m "feat: add ir policy validation gates"
```

### Task 7: Implement Python emitter core (elements, attrs, events)

**Files:**
- Create: `tools/html_codegen/src/emit/python/render_types.ts`
- Create: `tools/html_codegen/src/emit/python/render_element.ts`
- Create: `tools/html_codegen/src/emit/python/render_module.ts`
- Test: `tools/html_codegen/tests/python_emitter.test.ts`

**Step 1: Write the failing test**

```ts
import { describe, expect, it } from "vitest";
import { emit_python_module } from "../src/emit/python/render_module";

describe("python emitter", () => {
  it("emits snake_case params and strict Literal unions", () => {
    const source = emit_python_module(/* small IR fixture */);
    expect(source).toContain("def Input(");
    expect(source).toContain("type: Literal[");
    expect(source).toContain("class_name:");
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd tools/html_codegen && pnpm test python_emitter.test.ts`
Expected: FAIL because emitter is missing.

**Step 3: Write minimal implementation**

Emit deterministic Python source for:
- function signatures
- overloads for hybrid text/container elements
- typed events
- no `**kwargs` in public signatures

**Step 4: Run test to verify it passes**

Run: `cd tools/html_codegen && pnpm test python_emitter.test.ts`
Expected: PASS.

**Step 5: Commit**

```bash
git add tools/html_codegen/src/emit tools/html_codegen/tests/python_emitter.test.ts
git commit -m "feat: add python emitter for html api modules"
```

### Task 8: Implement explicit `data` mapping support

**Files:**
- Modify: `tools/html_codegen/src/ir/schema.ts`
- Modify: `tools/html_codegen/src/emit/python/render_element.ts`
- Create: `tools/html_codegen/src/runtime/data_attr_encoder.ts`
- Test: `tools/html_codegen/tests/data_mapping.test.ts`

**Step 1: Write the failing test**

```ts
import { describe, expect, it } from "vitest";
import { encode_data_attributes } from "../src/runtime/data_attr_encoder";

describe("data mapping", () => {
  it("maps data key suffixes to data-* dom attributes", () => {
    const dom = encode_data_attributes({ "test-id": "abc", enabled: true });
    expect(dom["data-test-id"]).toBe("abc");
    expect(dom["data-enabled"]).toBe(true);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd tools/html_codegen && pnpm test data_mapping.test.ts`
Expected: FAIL because mapper is missing.

**Step 3: Write minimal implementation**

Implement:
- `data: Mapping[str, DataValue] | None` emission contract
- key validation for DOM-style suffixes
- output mapping to `data-*`

**Step 4: Run test to verify it passes**

Run: `cd tools/html_codegen && pnpm test data_mapping.test.ts`
Expected: PASS.

**Step 5: Commit**

```bash
git add tools/html_codegen/src/ir/schema.ts tools/html_codegen/src/emit/python/render_element.ts tools/html_codegen/src/runtime tools/html_codegen/tests/data_mapping.test.ts
git commit -m "feat: add strict data attribute mapping support"
```

### Task 9: Add CLI modes (`compare` and `write`) and diff reporting

**Files:**
- Modify: `tools/html_codegen/src/cli.ts`
- Create: `tools/html_codegen/src/report/diff_report.ts`
- Test: `tools/html_codegen/tests/cli_compare_mode.test.ts`

**Step 1: Write the failing test**

```ts
import { describe, expect, it } from "vitest";
import { runCli } from "../src/cli";

describe("compare mode", () => {
  it("returns non-zero when generated output differs", async () => {
    const result = await runCli(["compare"]);
    expect([0, 1]).toContain(result.exit_code);
    expect(result.stdout).toContain("diff summary");
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd tools/html_codegen && pnpm test cli_compare_mode.test.ts`
Expected: FAIL because compare mode is missing.

**Step 3: Write minimal implementation**

Add:
- `compare`: compute IR/output diffs only.
- `write`: overwrite generated files and update snapshots.
- deterministic textual and JSON diff reports.

**Step 4: Run test to verify it passes**

Run: `cd tools/html_codegen && pnpm test cli_compare_mode.test.ts`
Expected: PASS.

**Step 5: Commit**

```bash
git add tools/html_codegen/src/cli.ts tools/html_codegen/src/report tools/html_codegen/tests/cli_compare_mode.test.ts
git commit -m "feat: add compare and write modes with diff reports"
```

### Task 10: Wire generator outputs into Trellis HTML modules

**Files:**
- Create: `tools/html_codegen/src/emit/targets/trellis_html.ts`
- Modify: `src/trellis/html/*.py` (generated outputs)
- Modify: `tests/py/integration/test_html.py` (only where behavior intentionally changes)
- Modify: `tests/py/integration/test_anchor_routing.py` (only if routing/event surface changes)

**Step 1: Write the failing test**

Add assertion(s) for known current drift fixed by generation (example: `auto_play` naming for media params).

**Step 2: Run test to verify it fails**

Run: `pixi run test tests/py/integration/test_html.py -k media -v`
Expected: FAIL on old handwritten surface.

**Step 3: Write minimal implementation**

Run generator in `write` mode and apply generated HTML module updates.

**Step 4: Run test to verify it passes**

Run:
- `pixi run test tests/py/integration/test_html.py -v`
- `pixi run test tests/py/integration/test_anchor_routing.py -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/trellis/html tests/py/integration/test_html.py tests/py/integration/test_anchor_routing.py tools/html_codegen/src/emit/targets/trellis_html.ts
git commit -m "feat: switch trellis html surface to generated api"
```

### Task 11: Add generator documentation and developer workflow

**Files:**
- Create: `docs/plans/html-codegen-usage.md` (or move into existing contributor docs path)
- Modify: `README.md` (developer section)
- Modify: `CONTRIBUTING.md`

**Step 1: Write the failing test**

Add doc-check test if available; otherwise add a checklist-based CI doc lint rule in generator tests.

**Step 2: Run test to verify it fails**

Run: `cd tools/html_codegen && pnpm test` (with doc assertion)
Expected: FAIL until docs are updated.

**Step 3: Write minimal implementation**

Document:
- install dependencies
- `compare` and `write` commands
- expected review flow for generated diffs

**Step 4: Run test to verify it passes**

Run:
- `cd tools/html_codegen && pnpm test`
- `pixi run lint`

Expected: PASS.

**Step 5: Commit**

```bash
git add README.md CONTRIBUTING.md docs/plans/html-codegen-usage.md
git commit -m "docs: add html codegen workflow for contributors"
```

### Task 12: Full verification before merge

**Files:**
- Verify only; no new files.

**Step 1: Run generator compare**

Run: `cd tools/html_codegen && pnpm run codegen:compare`
Expected: zero unexpected diffs.

**Step 2: Run generator write and re-compare**

Run:
- `cd tools/html_codegen && pnpm run codegen:write`
- `cd tools/html_codegen && pnpm run codegen:compare`

Expected: second compare shows no diffs.

**Step 3: Run project verification**

Run:
- `pixi run lint`
- `pixi run mypy`
- `pixi run test`

Expected: PASS.

**Step 4: Commit final generated updates**

```bash
git add tools/html_codegen src/trellis/html tests
git commit -m "chore: regenerate html api from runtime-first ir pipeline"
```

## Notes for Executor

- Keep scope to HTML output in v1 even if IR is namespace-aware.
- Do not add `**kwargs` to generated public APIs.
- Preserve strict literal typing where source unions are bounded.
- Keep source provenance on every resolved field for auditability.

