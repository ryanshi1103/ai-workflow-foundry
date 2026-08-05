#!/bin/bash
set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MONOREPO_ROOT="$(cd "$PROJECT_ROOT/../.." && pwd)"
SCRIPT="${CC_TEST_SCRIPT:-$PROJECT_ROOT/bin/cc}"
PYTHON_SOURCE="$MONOREPO_ROOT/src/flowfoundry/workspace/cc_launcher.py"
TEST_TMP_BASE="$MONOREPO_ROOT/.test-tmp"
mkdir -p "$TEST_TMP_BASE"
TEST_ROOT="$(mktemp -d -p "$TEST_TMP_BASE")"
FAKE_HOME="$TEST_ROOT/home"
FAKE_BIN="$TEST_ROOT/bin"
STATE_HOME="$TEST_ROOT/state"
OUTPUT="$TEST_ROOT/output"
EXEC_LOG="$TEST_ROOT/exec.log"
TEST_PROJECT="$FAKE_HOME/Projects/launcher-fixture"
PASSED=0
FAILED=0

cleanup() {
    rm -rf "$TEST_ROOT"
    rmdir "$TEST_TMP_BASE" 2>/dev/null || true
}
trap cleanup EXIT

pass() {
    echo "PASS: $1"
    PASSED=$((PASSED + 1))
}

fail() {
    echo "FAIL: $1"
    FAILED=$((FAILED + 1))
}

show_output() {
    sed 's/^/  launcher: /' "$OUTPUT" 2>/dev/null || true
}

assert_contains() {
    local file="$1" pattern="$2" description="$3"
    if grep -qF -- "$pattern" "$file"; then
        pass "$description"
    else
        fail "$description"
    fi
}

mkdir -p "$FAKE_HOME/.codex" "$FAKE_BIN" "$STATE_HOME/cc-launcher" "$TEST_PROJECT"
git -C "$TEST_PROJECT" init -q

for profile in manual readonly auto full; do
    printf 'model = "gpt-5.6-sol"\n' > "$FAKE_HOME/.codex/gpt56-sol-${profile}.config.toml"
done

cat > "$FAKE_BIN/codex" <<'FAKE_CODEX'
#!/bin/bash
if [[ "${1:-}" == "--version" ]]; then
    echo "codex-cli 0.144.0"
    exit 0
fi
printf 'command=codex\nargs=%s\nproject=%s\nmode=%s\n' \
    "$*" "${CC_ACTIVE_PROJECT:-}" "${CC_PROJECT_MODE:-}" > "$CC_TEST_EXEC_LOG"
FAKE_CODEX

cat > "$FAKE_BIN/aiproj" <<'FAKE_AIPROJ'
#!/bin/bash
printf 'command=aiproj\nargs=%s\nproject=%s\nmode=%s\n' \
    "$*" "${CC_ACTIVE_PROJECT:-}" "${CC_PROJECT_MODE:-}" > "$CC_TEST_EXEC_LOG"
FAKE_AIPROJ

cat > "$FAKE_BIN/timeout" <<'FAKE_TIMEOUT'
#!/bin/bash
exit 0
FAKE_TIMEOUT

cat > "$FAKE_BIN/curl" <<'FAKE_CURL'
#!/bin/bash
exit 0
FAKE_CURL

cat > "$FAKE_BIN/claude" <<'FAKE_CLAUDE'
#!/bin/bash
if [[ "${1:-}" == "--version" ]]; then
    echo "claude-cli test"
    exit 0
fi
printf 'command=claude\nargs=%s\nproject=%s\nmode=%s\nconfig=%s\n' \
    "$*" "${CC_ACTIVE_PROJECT:-}" "${CC_PROJECT_MODE:-}" "${CLAUDE_CONFIG_DIR:-}" \
    > "$CC_TEST_EXEC_LOG"
FAKE_CLAUDE

chmod +x "$FAKE_BIN/codex" "$FAKE_BIN/aiproj" "$FAKE_BIN/timeout" "$FAKE_BIN/curl" "$FAKE_BIN/claude"

run_launcher() {
    local input="$1"
    local remote="${2:-false}"
    local remote_env=()
    if [[ "$remote" == "true" ]]; then
        remote_env+=(
            # Synthetic Tailscale-range addresses; not real device endpoints.
            SSH_CONNECTION="100.64.0.2 54321 100.64.0.1 22"
            SSH_TTY="/dev/pts/9"
        )
    fi
    rm -f "$EXEC_LOG" "$OUTPUT"
    # The suite must behave identically when invoked locally or from a real
    # SSH/mobile session.  Remove inherited SSH markers, then add controlled
    # fake markers only for test cases that explicitly request remote mode.
    printf '%s' "$input" | env -u SSH_CONNECTION -u SSH_TTY \
        HOME="$FAKE_HOME" \
        XDG_STATE_HOME="$STATE_HOME" \
        PYTHONPATH="$MONOREPO_ROOT/src" \
        PATH="$FAKE_BIN:/usr/bin:/bin" \
        _CC_PRESET_PROJECT="$TEST_PROJECT" \
        CC_TEST_EXEC_LOG="$EXEC_LOG" \
        "${remote_env[@]}" \
        "$SCRIPT" > "$OUTPUT" 2>&1
}

seed_valid_cache() {
    printf '%s\n%s\n%s\n%s\n' \
        "$(date +%s)" "$FAKE_BIN/codex" "codex-cli 0.144.0" "test" \
        > "$STATE_HOME/cc-launcher/codex-preflight"
}

test_codex_mode() {
    local mode="$1" profile="$2"
    seed_valid_cache
    if run_launcher "o
$mode
yes
"; then
        assert_contains "$EXEC_LOG" "args=--profile $profile" "Codex $mode uses $profile"
        assert_contains "$EXEC_LOG" "project=$TEST_PROJECT" "Codex $mode exports CC_ACTIVE_PROJECT"
    else
        fail "Codex $mode reaches intercepted exec"
    fi
}

bash -n "$SCRIPT" && pass "source bash -n" || fail "source bash -n"

test_codex_mode m gpt56-sol-manual
test_codex_mode p gpt56-sol-readonly
test_codex_mode a gpt56-sol-auto
test_codex_mode b gpt56-sol-full

seed_valid_cache
if run_launcher "o
a
yes
" true; then
    assert_contains "$OUTPUT" "SSH 远程会话" "remote session banner is visible"
    assert_contains "$EXEC_LOG" "args=--profile gpt56-sol-auto" "remote safe Codex mode launches normally"
else
    fail "remote safe Codex mode reaches intercepted exec"
fi

seed_valid_cache
if run_launcher "o
b
yes
" true; then
    fail "remote Codex full access rejects missing remote-yes"
else
    [[ ! -e "$EXEC_LOG" ]] && pass "remote Codex full access stops before exec" || fail "remote Codex full access executed without remote-yes"
    assert_contains "$OUTPUT" "远程高权限确认失败" "remote Codex full access explains rejection"
fi

seed_valid_cache
if run_launcher "o
b
remote-yes
yes
" true; then
    assert_contains "$EXEC_LOG" "args=--profile gpt56-sol-full" "remote Codex full access accepts two confirmations"
else
    fail "remote Codex full access reaches intercepted exec after two confirmations"
fi

seed_valid_cache
if run_launcher "o
b
not-yes
"; then
    fail "Codex b rejects incorrect confirmation"
else
    [[ ! -e "$EXEC_LOG" ]] && pass "Codex b incorrect input cancels before exec" || fail "Codex b incorrect input executed Codex"
    assert_contains "$OUTPUT" "已取消。" "Codex b incorrect input reports cancellation"
fi

seed_valid_cache
if run_launcher "o
b
yes
"; then
    assert_contains "$EXEC_LOG" "args=--profile gpt56-sol-full" "Codex b yes continues to intercepted exec"
else
    fail "Codex b yes reaches intercepted exec"
fi

seed_valid_cache
if run_launcher "o
b
"; then
    fail "closed stdin cancels with non-zero status"
else
    [[ ! -e "$EXEC_LOG" ]] && pass "closed stdin cancels before exec" || fail "closed stdin executed Codex"
    assert_contains "$OUTPUT" "输入已关闭，已取消。" "closed stdin reports safe cancellation"
    if grep -q '未绑定的变量\|unbound variable' "$OUTPUT"; then
        fail "closed stdin avoids unbound-variable error"
    else
        pass "closed stdin avoids unbound-variable error"
    fi
fi

printf 'EOF\nlegacy corrupt cache\n' > "$STATE_HOME/cc-launcher/codex-preflight"
if run_launcher "o
b
yes
"; then
    first_cache_line="$(head -n 1 "$STATE_HOME/cc-launcher/codex-preflight")"
    if [[ "$first_cache_line" =~ ^[0-9]+$ ]]; then
        pass "legacy EOF cache is repaired to a numeric timestamp"
    else
        fail "legacy EOF cache remains invalid"
    fi
    if grep -q '未绑定的变量\|unbound variable' "$OUTPUT"; then
        fail "legacy EOF cache avoids unbound-variable error"
    else
        pass "legacy EOF cache avoids unbound-variable error"
    fi
else
    fail "legacy EOF cache safely reaches intercepted exec"
fi

if run_launcher "q
"; then
    assert_contains "$OUTPUT" "已取消。" "provider q returns safely"
else
    fail "provider q exits successfully"
fi

if run_launcher "o
q
q
"; then
    assert_contains "$OUTPUT" "已取消。" "Codex q returns to provider menu"
else
    fail "Codex q return flow exits successfully"
fi

run_launcher "c
m
yes
"
claude_status=$?
if [[ -e "$EXEC_LOG" ]]; then
    assert_contains "$EXEC_LOG" "command=claude" "Claude branch reaches intercepted native CLI"
    assert_contains "$EXEC_LOG" "project=$TEST_PROJECT" "Claude branch preserves selected project"
    assert_contains "$EXEC_LOG" "config=$FAKE_HOME/.claude-native" "Claude native config isolation preserved"
    if [[ $claude_status -ne 0 ]]; then
        assert_contains "$OUTPUT" "Transcript parsing produced no real user prompt" "synthetic Claude run reports expected finalization limitation"
    fi
else
    fail "Claude branch still launches"
    show_output
fi

run_launcher "d
m
yes
"
deepseek_status=$?
if [[ -e "$EXEC_LOG" ]]; then
    assert_contains "$EXEC_LOG" "command=claude" "DeepSeek branch reaches intercepted compatible CLI"
    assert_contains "$EXEC_LOG" "project=$TEST_PROJECT" "DeepSeek branch preserves selected project"
    assert_contains "$EXEC_LOG" "config=$FAKE_HOME/.claude-deepseek" "DeepSeek config isolation preserved"
    if [[ $deepseek_status -ne 0 ]]; then
        assert_contains "$OUTPUT" "Transcript parsing produced no real user prompt" "synthetic DeepSeek run reports expected finalization limitation"
    fi
else
    fail "DeepSeek branch still launches"
    show_output
fi

run_launcher "c
b
remote-yes
yes
" true
remote_claude_status=$?
if [[ -e "$EXEC_LOG" ]]; then
    assert_contains "$EXEC_LOG" "--permission-mode bypassPermissions" "remote Claude bypass accepts two confirmations"
    if [[ $remote_claude_status -ne 0 ]]; then
        assert_contains "$OUTPUT" "Transcript parsing produced no real user prompt" "synthetic remote Claude run reports expected finalization limitation"
    fi
else
    fail "remote Claude bypass reaches intercepted exec after two confirmations"
    show_output
fi

assert_contains "$PYTHON_SOURCE" '"claude"' "Claude branch remains in source"
assert_contains "$PYTHON_SOURCE" '"deepseek"' "DeepSeek branch remains in source"
assert_contains "$PYTHON_SOURCE" 'os.execv(codex_bin' "Codex native TUI exec remains in source"
assert_contains "$PYTHON_SOURCE" 'launch_here(' "launch-here prevents timestamp top-level projects"
assert_contains "$PYTHON_SOURCE" 'https://api.openai.com/' "Codex preflight checks the OpenAI HTTPS endpoint"
if grep -qF '/dev/tcp/8.8.8.8/53' "$PYTHON_SOURCE"; then
    fail "Codex preflight no longer relies on public DNS TCP port 53"
else
    pass "Codex preflight no longer relies on public DNS TCP port 53"
fi

printf 'RESULT: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
