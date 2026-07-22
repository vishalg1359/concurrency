#!/usr/bin/env bash
# Reset your attempts back to the original stubs so you can redo the lab.
# Only the stub files in taskpool/ are reverted; solutions/ and tests/ are never
# touched (you don't edit those). Run from anywhere: ./reset.sh
set -e
cd "$(dirname "$0")"
git restore taskpool
find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
echo "Reset done — fresh stubs restored. Happy drilling."
