#!/bin/bash
# Regression entry point for the unified Python cc launcher.
# The original shell implementation was migrated to flowfoundry.workspace;
# this command preserves the public test entry point while exercising the
# wrapper and the same menu, project, recent-list, provider, and safety rules.
set -euo pipefail

COMPONENT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MONOREPO_ROOT="$(cd "$COMPONENT_ROOT/../.." && pwd)"
TEST_TMP_BASE="$MONOREPO_ROOT/.test-tmp"

cleanup() {
    rmdir "$TEST_TMP_BASE" 2>/dev/null || true
}
trap cleanup EXIT

mkdir -p "$TEST_TMP_BASE"

bash -n "$COMPONENT_ROOT/bin/cc"
bash -n "$COMPONENT_ROOT/bin/aiproj"
bash -n "$COMPONENT_ROOT/bin/cc-projects-maintain"

FLOWFOUNDRY_TEST_TMP="$TEST_TMP_BASE" \
PYTHONPATH="$MONOREPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}" \
    python3 -m unittest discover \
        -s "$COMPONENT_ROOT/tests" \
        -p 'test_cc_launcher.py' \
        -v
