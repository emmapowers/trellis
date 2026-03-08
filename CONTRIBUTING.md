# Contributing to Trellis

## Development Setup

1. Install [uv](https://docs.astral.sh/uv/)
2. Clone and install:
   ```bash
   git clone https://github.com/emmapowers/trellis.git
   cd trellis
   uv sync --dev
   ```

## Development Commands

```bash
just test       # Run tests
just test-cov   # Run tests with coverage
just cleanup    # Format and lint (auto-fix)
just lint       # Check linting (no fix)
just ci         # Full CI checks
```

## HTML Codegen Tool

The HTML codegen tool is a manual developer workflow:

```bash
cd tools/html_codegen
npm install
npm run codegen:compare
npm run codegen:write
```

`codegen:write` updates generated artifacts under `src/trellis/html/_generated_*.py`,
including `src/trellis/html/_generated_runtime.py` and
`src/trellis/html/_generated_events.py`.

After writing outputs, run `pixi run ci` and commit the resulting diffs.

## Code Style

- Formatting: Ruff (100 char line length)
- Linting: Ruff
- Type checking: Basedpyright (standard mode)

Run `just ci` before committing.
