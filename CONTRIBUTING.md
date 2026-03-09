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

## Code Style

- Formatting: Ruff (100 char line length)
- Linting: Ruff
- Type checking: MyPy (strict mode)

Run `just cleanup` before committing.
