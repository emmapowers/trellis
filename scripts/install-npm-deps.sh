#!/bin/bash
# Installs Bun dependencies for repo-owned JavaScript packages if needed.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Function to check if bun install is needed
needs_bun_install() {
    local dir="$1"
    # If node_modules doesn't exist, need install
    [[ ! -d "$dir/node_modules" ]] && return 0
    # If bun.lock is newer than node_modules, need install
    [[ "$dir/bun.lock" -nt "$dir/node_modules" ]] && return 0
    return 1
}

# Install docs deps if needed
if needs_bun_install "$REPO_ROOT/docs"; then
    echo "Installing docs Bun dependencies..."
    (cd "$REPO_ROOT/docs" && bun install)
fi

# Install playground deps if needed
if needs_bun_install "$REPO_ROOT/docs/static/playground"; then
    echo "Installing playground Bun dependencies..."
    (cd "$REPO_ROOT/docs/static/playground" && bun install)
fi

# Install JS test deps if needed
if needs_bun_install "$REPO_ROOT/tests/js"; then
    echo "Installing JS test Bun dependencies..."
    (cd "$REPO_ROOT/tests/js" && bun install)
fi
