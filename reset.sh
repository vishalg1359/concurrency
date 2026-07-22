#!/usr/bin/env bash
# Reset your attempts back to the ORIGINAL blank stubs so you can redo the lab.
# Copies the pristine stubs from .stubs/ over taskpool/ — this always wipes your
# work back to "not completed at all", even if you committed an attempt.
# solutions/ and tests/ are never touched. Run from anywhere: ./reset.sh
set -e
cd "$(dirname "$0")"
cp .stubs/taskpool/*.py taskpool/
find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
echo "Reset done — fresh blank stubs restored. Happy drilling."
