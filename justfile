# Trellis development task runner
# Run `just --list` to see all available recipes

# Formatting
fmt:
    uv run ruff format src tests examples
    uv run ruff check --fix src tests examples

fmt-check:
    uv run ruff format --check src tests examples
    uv run ruff check src tests examples

# Type checking
mypy:
    uv run dmypy run -- src/trellis examples

mypy-ci:
    uv run mypy src/trellis examples

# Testing
test:
    uv run pytest tests/py

test-cov:
    uv run pytest tests/py --cov=src/trellis --cov-report=term-missing

install-js-test-deps:
    cd tests/js && uv run pybun install

test-js: install-js-test-deps
    cd tests/js && uv run pybun run test

# Composite lint/test tasks
cleanup: fmt

lint: fmt-check mypy-ci

ci: lint test test-js

# Build tasks
clean:
    rm -rf dist build .build .mypy_cache .ruff_cache .pytest_cache .coverage

# Examples
demo:
    uv run python examples/demo.py

showcase:
    uv run trellis -r examples/widget_showcase run --desktop

sliders:
    uv run python examples/all_sliders_all_the_time.py

breakfast:
    uv run python -m examples.breakfast_todo

# Playground
install-playground-deps:
    cd docs/static/playground && uv run pybun install

build-playground: install-playground-deps
    cd docs/static/playground && uv run pybun run build

playground: build-playground
    cd docs/static && uv run python -c "import http.server, socketserver, socket; s=socket.socket(); s.bind(('',0)); port=s.getsockname()[1]; s.close(); print(f'\n  Playground: http://localhost:{port}/playground/\n'); http.server.test(HandlerClass=http.server.SimpleHTTPRequestHandler, port=port, bind='127.0.0.1')"

# Documentation
generate-api-docs:
    uv run pydoc-markdown

generate-example-pages:
    uv run python scripts/generate-example-pages.py

install-docs-deps:
    cd docs && uv run pybun install

build-docs: install-docs-deps generate-api-docs build-playground generate-example-pages
    cd docs && uv run pybun run build

serve-docs: install-docs-deps generate-api-docs build-playground generate-example-pages
    cd docs && uv run pybun run start

watch-api-docs:
    uv run watchfiles 'just generate-api-docs' src/trellis
