# Contributing to Trellis

## Development Setup

1. Install [pixi](https://pixi.sh)
2. Clone and install:
   ```bash
   git clone https://github.com/emmapowers/trellis.git
   cd trellis
   pixi install
   ```

## Development Commands

```bash
pixi run test       # Run tests
pixi run test-cov   # Run tests with coverage
pixi run cleanup    # Format and lint (auto-fix)
pixi run lint       # Check linting (no fix)
pixi run ci         # Full CI checks
```

## Code Style

- Formatting: Black (100 char line length)
- Linting: Ruff
- Type checking: MyPy (strict mode)

Run `pixi run cleanup` before committing.
