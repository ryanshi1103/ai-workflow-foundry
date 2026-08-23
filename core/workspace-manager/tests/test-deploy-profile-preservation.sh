#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MONOREPO_ROOT="$(cd "$PROJECT_ROOT/../.." && pwd)"
TEST_TMP_BASE="$MONOREPO_ROOT/.test-tmp"
mkdir -p "$TEST_TMP_BASE"
TEST_ROOT="$(mktemp -d -p "$TEST_TMP_BASE")"
TEST_HOME="$TEST_ROOT/home"
TEST_STATE="$TEST_ROOT/state"
OUTPUT="$TEST_ROOT/deploy-output"

cleanup() {
    rm -rf "$TEST_ROOT"
    rmdir "$TEST_TMP_BASE" 2>/dev/null || true
}
trap cleanup EXIT

mkdir -p "$TEST_HOME/.codex" "$TEST_HOME/.local/bin"

cat > "$TEST_HOME/.codex/gpt56-sol-full.config.toml" <<'PROFILE'
model = "old-model"
approval_policy = "on-request"
sandbox_mode = "read-only"

[projects."/tmp/project-one"]
trust_level = "trusted"

[projects."/tmp/project two"]
trust_level = "untrusted"
PROFILE

printf '%s\n' 'auth-sentinel-do-not-touch' > "$TEST_HOME/.codex/auth.json"

HOME="$TEST_HOME" XDG_STATE_HOME="$TEST_STATE" \
    bash "$PROJECT_ROOT/scripts/deploy.sh" > "$OUTPUT" 2>&1

deployed="$TEST_HOME/.codex/gpt56-sol-full.config.toml"

grep -qF 'model = "gpt-5.6-sol"' "$deployed"
grep -qF 'sandbox_mode = "danger-full-access"' "$deployed"
grep -qF '[projects."/tmp/project-one"]' "$deployed"
grep -qF '[projects."/tmp/project two"]' "$deployed"
grep -qF 'trust_level = "trusted"' "$deployed"
grep -qF 'trust_level = "untrusted"' "$deployed"
[[ "$(stat -c '%a' "$deployed")" == "600" ]]
[[ "$(cat "$TEST_HOME/.codex/auth.json")" == "auth-sentinel-do-not-touch" ]]
grep -qF 'Verification:' "$OUTPUT"
grep -qF '0 failed' "$OUTPUT"

echo "PASS: deploy updates managed profile settings"
echo "PASS: deploy preserves local [projects] trust entries"
echo "PASS: deploy writes profile permissions as 600"
echo "PASS: deploy leaves auth.json untouched"
