#!/usr/bin/env bash
# Typecheck the updater library and every package update.py.
set -euo pipefail

echo "Typechecking updater library..."
mypy scripts/updater

echo "Typechecking update scripts..."
find packages -type f -name 'update.py' -print0 | xargs -0 -n1 -P 0 mypy
