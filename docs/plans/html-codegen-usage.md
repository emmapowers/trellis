# HTML Codegen Usage

The HTML code generator lives in `tools/html_codegen/` and is a manual developer tool.

## Setup

```bash
cd tools/html_codegen
npm install
```

## Commands

```bash
npm run codegen:compare
npm run codegen:write
```

- `compare`: show a diff summary without writing files.
- `write`: write generated outputs and print a diff summary.

## Typical Workflow

1. Run `npm run codegen:compare`.
2. If changes are expected, run `npm run codegen:write`.
3. Review diffs in git.
4. Run project checks (`pixi run lint`, `pixi run test`).
5. Commit generated changes with related source updates.
