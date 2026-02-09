# Makefile for trellis build artifacts
# Use with pixi: pixi run make <target>

.PHONY: all clean wheel bundles server-bundle desktop-bundle browser-bundle browser-lib \
        api-docs example-pages playground docs

# Directories
SRC := src/trellis
PLATFORMS := $(SRC)/platforms
DOCS := docs
DOCS_STATIC := $(DOCS)/static
TRELLIS_LIB := $(DOCS_STATIC)/trellis

# Source file patterns
PY_SOURCES := $(shell find $(SRC) -name '*.py')
TS_SOURCES := $(shell find $(PLATFORMS) -name '*.ts' -o -name '*.tsx')
EXAMPLE_SOURCES := $(shell find examples -name '*.py' 2>/dev/null)
PLAYGROUND_SOURCES := $(shell find $(DOCS_STATIC)/playground/src -name '*.ts' -o -name '*.tsx' 2>/dev/null)

# Sentinel files for targets without single output
SENTINEL := .build
$(shell mkdir -p $(SENTINEL))

#------------------------------------------------------------------------------
# Default target
#------------------------------------------------------------------------------
all: wheel bundles api-docs

#------------------------------------------------------------------------------
# Python wheel
#------------------------------------------------------------------------------
wheel: dist/.wheel-built

dist/.wheel-built: pyproject.toml $(PY_SOURCES)
	pip wheel . -w dist --no-deps
	@touch $@

#------------------------------------------------------------------------------
# Browser library bundle (for playground and TrellisDemo)
#------------------------------------------------------------------------------
browser-lib: $(TRELLIS_LIB)/index.js

$(TRELLIS_LIB)/index.js: $(TS_SOURCES) $(PY_SOURCES) docs/trellis-lib/pyproject.toml
	trellis --app-root docs/trellis-lib bundle --dest $(TRELLIS_LIB)

#------------------------------------------------------------------------------
# API documentation
#------------------------------------------------------------------------------
api-docs: $(SENTINEL)/.api-docs-built

$(SENTINEL)/.api-docs-built: $(PY_SOURCES) pydoc-markdown.yaml
	pydoc-markdown
	@touch $@

#------------------------------------------------------------------------------
# Example pages (for docs)
#------------------------------------------------------------------------------
example-pages: $(SENTINEL)/.example-pages-built

$(SENTINEL)/.example-pages-built: $(EXAMPLE_SOURCES) scripts/generate-example-pages.py
	python scripts/generate-example-pages.py
	@touch $@

#------------------------------------------------------------------------------
# Copy wheel to docs
#------------------------------------------------------------------------------
docs-wheel: $(SENTINEL)/.docs-wheel-copied

$(SENTINEL)/.docs-wheel-copied: dist/.wheel-built
	find $(DOCS_STATIC) -maxdepth 1 -name '*.whl' -delete
	cp dist/trellis-*.whl $(DOCS_STATIC)/
	@touch $@

#------------------------------------------------------------------------------
# Playground
#------------------------------------------------------------------------------
playground: $(DOCS_STATIC)/playground/dist/playground.js

$(DOCS_STATIC)/playground/node_modules: $(DOCS_STATIC)/playground/package.json
	cd $(DOCS_STATIC)/playground && npm install
	@touch $@

$(DOCS_STATIC)/playground/dist/playground.js: $(TRELLIS_LIB)/index.js dist/.wheel-built $(PLAYGROUND_SOURCES) $(DOCS_STATIC)/playground/node_modules
	cd $(DOCS_STATIC)/playground && npm run build

#------------------------------------------------------------------------------
# Full docs build
#------------------------------------------------------------------------------
docs: $(SENTINEL)/.api-docs-built playground $(SENTINEL)/.example-pages-built $(SENTINEL)/.docs-wheel-copied
	cd $(DOCS) && npm ci && npm run build

#------------------------------------------------------------------------------
# Clean
#------------------------------------------------------------------------------
clean:
	rm -rf dist build .mypy_cache .ruff_cache .pytest_cache .coverage
	rm -rf $(SENTINEL)
	rm -f $(SERVER_DIST)/bundle.js $(SERVER_DIST)/bundle.css
	rm -f $(DESKTOP_DIST)/bundle.js $(DESKTOP_DIST)/bundle.css
	rm -f $(BROWSER_DIST)/bundle.js $(BROWSER_DIST)/bundle.css
	rm -rf $(TRELLIS_LIB)
	rm -rf $(DOCS_STATIC)/playground/dist
	rm -rf $(DOCS)/build
