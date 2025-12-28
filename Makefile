# Makefile for trellis build artifacts
# Use with pixi: pixi run make <target>

.PHONY: all clean wheel bundles server-bundle desktop-bundle browser-bundle \
        api-docs example-pages playground docs

# Directories
SRC := src/trellis
PLATFORMS := $(SRC)/platforms
COMMON_CLIENT := $(PLATFORMS)/common/client/src
SERVER_DIST := $(PLATFORMS)/server/client/dist
DESKTOP_DIST := $(PLATFORMS)/desktop/client/dist
BROWSER_DIST := $(PLATFORMS)/browser/client/dist
DOCS := docs
DOCS_STATIC := $(DOCS)/static

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
# Platform bundles
#------------------------------------------------------------------------------
bundles: server-bundle desktop-bundle browser-bundle

server-bundle: $(SERVER_DIST)/bundle.js
desktop-bundle: $(DESKTOP_DIST)/bundle.js
browser-bundle: $(BROWSER_DIST)/bundle.js

$(SERVER_DIST)/bundle.js: $(TS_SOURCES)
	trellis bundle build --platform server

$(DESKTOP_DIST)/bundle.js: $(TS_SOURCES)
	trellis bundle build --platform desktop

$(BROWSER_DIST)/bundle.js: $(TS_SOURCES)
	trellis bundle build --platform browser

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

$(SENTINEL)/.example-pages-built: $(BROWSER_DIST)/bundle.js $(EXAMPLE_SOURCES) scripts/generate-example-pages.py
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

$(DOCS_STATIC)/playground/dist/playground.js: $(BROWSER_DIST)/bundle.js dist/.wheel-built $(PLAYGROUND_SOURCES) $(DOCS_STATIC)/playground/node_modules
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
	rm -rf $(DOCS_STATIC)/playground/dist
	rm -rf $(DOCS)/build
