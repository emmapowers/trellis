#!/bin/bash
# Installs npm dependencies for docs if needed

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Function to check if npm install is needed
needs_npm_install() {
    local dir="$1"
    # If node_modules doesn't exist, need install
    [[ ! -d "$dir/node_modules" ]] && return 0
    # If package-lock.json is newer than node_modules, need install
    [[ "$dir/package-lock.json" -nt "$dir/node_modules" ]] && return 0
    return 1
}

# Install docs deps if needed
if needs_npm_install "$REPO_ROOT/docs"; then
    echo "Installing docs npm dependencies..."
    (cd "$REPO_ROOT/docs" && npm install)
fi

# Install playground deps if needed
if needs_npm_install "$REPO_ROOT/docs/static/playground"; then
    echo "Installing playground npm dependencies..."
    (cd "$REPO_ROOT/docs/static/playground" && npm install)
fi
