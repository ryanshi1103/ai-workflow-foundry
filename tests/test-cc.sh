#!/bin/bash
# Automated test suite for cc launcher
# Tests from requirement section 八
# Non-interactive — tests structure, functions, and logic only

set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$PROJECT_ROOT/bin/cc"
TEST_ROOT="$(mktemp -d)"
TEST_HOME="$TEST_ROOT/home"
TEST_PROJECTS_ROOT="$TEST_HOME/Projects"
trap 'rm -rf "$TEST_ROOT"' EXIT

FAILED=0
PASSED=0

pass() { echo "  ✅ PASS: $1"; PASSED=$((PASSED+1)); }
fail() { echo "  ❌ FAIL: $1"; FAILED=$((FAILED+1)); }

echo "╔══════════════════════════════════════════╗"
echo "║  CC Launcher Test Suite                  ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ─────────────────────────────────────────────────────────────────────────
echo "=== 1. Syntax Check ==="
bash -n "$SCRIPT" 2>&1 && pass "bash -n passes" || fail "bash -n FAILED"
echo ""

# ─────────────────────────────────────────────────────────────────────────
echo "=== 2. meeting-media-auto removed ==="
grep -q 'meeting-media-auto' "$SCRIPT" && fail "still references meeting-media-auto" || pass "no reference to meeting-media-auto"
echo ""

# ─────────────────────────────────────────────────────────────────────────
echo "=== 3. New Menu Structure ==="
check_menu() {
    local pattern="$1" desc="$2"
    grep -q "$pattern" "$SCRIPT" && pass "$desc" || fail "$desc — NOT FOUND"
}
check_menu '║  1.*当前目录'     "Menu option 1: 当前目录"
check_menu '║  2.*最近项目'     "Menu option 2: 最近项目"
check_menu '║  3.*~/Projects.*选择项目' "Menu option 3: 从 ~/Projects 选择"
check_menu '║  4.*~/Projects.*新建项目' "Menu option 4: 在 ~/Projects 新建"
check_menu '║  5.*手动输入项目路径' "Menu option 5: 手动输入项目路径"
check_menu '║  q.*退出'         "Menu option q: 退出"
grep -q '请选择 (1/2/3/4/5/q)' "$SCRIPT" && pass "Prompt shows 1/2/3/4/5/q" || fail "Prompt NOT updated"
echo ""

# ─────────────────────────────────────────────────────────────────────────
echo "=== 4. Recent Projects Menu ==="
grep -q 'recent_projects_menu()' "$SCRIPT" && pass "recent_projects_menu function exists" || fail "recent_projects_menu function MISSING"
grep -q '暂无最近项目' "$SCRIPT" && pass "shows '暂无最近项目' when empty" || fail "missing '暂无最近项目'"
recent_menu_body="$(sed -n '/^recent_projects_menu()/,/^}/p' "$SCRIPT")"
grep -q 'basename' <<< "$recent_menu_body" && pass "shows project name via basename" || fail "missing basename display"
grep -q 'entries\[$i\]' <<< "$recent_menu_body" && pass "shows full path (entries array)" || fail "missing full path display"
grep -q '返回主菜单' <<< "$recent_menu_body" && pass "'b' back option present" || fail "'b' back option MISSING"
grep -q 'q.*退出\|Q.*退出\|已取消' <<< "$recent_menu_body" && pass "'q' exit option present" || fail "'q' exit option MISSING"

# Test the function logic directly
TEST_DIR="$TEST_PROJECTS_ROOT"
mkdir -p "$TEST_DIR"
export HOME="$TEST_HOME"
export RECENT_STATE_DIR="$TEST_ROOT/state/cc-launcher"
export RECENT_FILE="${RECENT_STATE_DIR}/recent-projects"
mkdir -p "$RECENT_STATE_DIR"
# Create test projects
mkdir -p "$TEST_DIR/proj-a"
mkdir -p "$TEST_DIR/proj-b"
mkdir -p "$TEST_DIR/proj with spaces"

# Source add_to_recent
eval "$(grep '^TIMESTAMP_PATTERN=' "$SCRIPT")"
eval "$(sed -n '/^is_timestamp_session_dir()/,/^}/p' "$SCRIPT")"
eval "$(sed -n '/^add_to_recent()/,/^}/p' "$SCRIPT")"

# Test recording
add_to_recent "$TEST_DIR/proj-a" && pass "add_to_recent: records entry" || fail "add_to_recent: FAILED"
add_to_recent "$TEST_DIR/proj-b"
add_to_recent "$TEST_DIR/proj with spaces"

# Test dedup
add_to_recent "$TEST_DIR/proj-a"
count=$(grep -c "$TEST_DIR/proj-a" "$RECENT_FILE" 2>/dev/null || echo 0)
[[ "$count" -eq 1 ]] && pass "add_to_recent: dedup works" || fail "add_to_recent: dedup FAILED (count=$count)"

# Test ordering
first=$(head -1 "$RECENT_FILE")
[[ "$first" == "$TEST_DIR/proj-a" ]] && pass "add_to_recent: newest first" || fail "add_to_recent: order FAILED (first=$first)"

# Test spaces
grep -q "proj with spaces" "$RECENT_FILE" && pass "add_to_recent: spaces in path OK" || fail "add_to_recent: spaces in path FAILED"

# Test non-existent cleanup
mkdir -p "$TEST_DIR/temp-dir"
add_to_recent "$TEST_DIR/temp-dir"
rm -rf "$TEST_DIR/temp-dir"
add_to_recent "$TEST_DIR/proj-a"  # triggers cleanup on read
grep -q "temp-dir" "$RECENT_FILE" && fail "add_to_recent: stale dir NOT cleaned" || pass "add_to_recent: stale dir cleaned"

# Test max 20
for i in $(seq 1 25); do
    mkdir -p "$TEST_DIR/many-$i"
    add_to_recent "$TEST_DIR/many-$i"
done
line_count=$(wc -l < "$RECENT_FILE" 2>/dev/null || echo 0)
[[ "$line_count" -le 20 ]] && pass "add_to_recent: caps at 20 (has $line_count)" || fail "add_to_recent: exceeds 20 (has $line_count)"

echo ""

# ─────────────────────────────────────────────────────────────────────────
echo "=== 5. Create New Project ==="
grep -q 'create_new_project()' "$SCRIPT" && pass "create_new_project function exists" || fail "create_new_project function MISSING"
grep -q '请输入项目名称' "$SCRIPT" && pass "prompts for project name" || fail "missing name prompt"
grep -q '路径分隔符\|特殊字符' "$SCRIPT" && pass "path traversal check" || fail "missing path traversal check"
grep -q '项目已存在' "$SCRIPT" && pass "existing project dialog" || fail "missing existing dialog"
grep -q '项目创建成功' "$SCRIPT" && pass "success message" || fail "missing success message"
grep -q '直接打开已有项目' "$SCRIPT" && pass "reopen existing option" || fail "missing reopen option"
grep -q '重新输入名称' "$SCRIPT" && pass "rename option" || fail "missing rename option"
echo ""

# ─────────────────────────────────────────────────────────────────────────
echo "=== 6. Browse Projects Display ==="
grep -A20 '~/Projects 中的项目' "$SCRIPT" | grep -q 'd_clean' && pass "strips trailing slash" || fail "missing slash strip"
grep -A20 '~/Projects 中的项目' "$SCRIPT" | grep -q 'project_indicators' && pass "Git/AI indicators" || fail "missing project indicators"
grep -A20 '~/Projects 中的项目' "$SCRIPT" | grep -q 'printf.*d_clean' && pass "shows full path" || fail "missing full path"
echo ""

# ─────────────────────────────────────────────────────────────────────────
echo "=== 7. Manual Path Input ==="
grep -q 'manual_project_input()' "$SCRIPT" && pass "manual_project_input exists" || fail "manual_project_input MISSING"
grep -q '~' "$SCRIPT" && grep -q 'RAW_PATH' "$SCRIPT" && pass "tilde expansion" || fail "missing tilde expansion"
grep -q '解析后的路径' "$SCRIPT" && pass "shows resolved path" || fail "missing resolved path display"
echo ""

# ─────────────────────────────────────────────────────────────────────────
echo "=== 8. Recent Recording Hook ==="
grep -q 'add_to_recent.*PROJECT_DIR' "$SCRIPT" && pass "recording in main flow" || fail "recording MISSING"
grep -q '_CC_HERE_MODE.*!=.*1' "$SCRIPT" && pass "skips for here-mode" || fail "here-mode skip MISSING"
echo ""

# ─────────────────────────────────────────────────────────────────────────
echo "=== 9. Preserved Features ==="
check_keep() {
    grep -q "$1" "$SCRIPT" && pass "kept: $2" || fail "LOST: $2"
}
check_keep 'PROVIDER="claude"'      "Claude native mode"
check_keep 'PROVIDER="deepseek"'    "DeepSeek mode"
check_keep 'PERM_MODE="default"'    "Manual permission mode"
check_keep 'acceptEdits'            "acceptEdits mode"
check_keep 'PERM_MODE="plan"'       "plan mode"
check_keep 'bypassPermissions'      "bypassPermissions mode"
check_keep 'CLAUDE_CONFIG_DIR'      "config dir isolation"
check_keep 'ANTHROPIC_BASE_URL'      "DeepSeek env vars"
check_keep 'ANTHROPIC_AUTH_TOKEN'   "auth token clearing"
check_keep 'CLAUDE_CODE_SUBAGENT_MODEL' "subagent model env"
check_keep 'CLAUDE_CODE_EFFORT_LEVEL'   "effort level env"
check_keep 'launch-here'            "aiproj launch-here"
check_keep 'launch-new'             "aiproj launch-new"
check_keep 'exec aiproj'            "exec for proper launch"
check_keep 'PROJECT_DIR=.*PWD'      "current directory support"
check_keep 'git rev-parse'          "git auto-detect"
check_keep '_CC_HERE_MODE'          "here-mode"
check_keep '_CC_PRESET_PROJECT'     "preset project"
grep -A2 'q|Q)' "$SCRIPT" | grep -q 'exit 0' && pass "kept: q exit logic" || fail "LOST: q exit logic"
check_keep 'Shift+Tab'              "Shift+Tab hint"
echo ""

# ─────────────────────────────────────────────────────────────────────────
echo "=== 10. Safety Checks ==="
grep -q 'eval' "$SCRIPT" && fail "uses 'eval'" || pass "no eval usage"
grep -qE 'rm[[:space:]]+-rf[[:space:]]+/' "$SCRIPT" && fail "potentially dangerous rm -rf" || pass "no dangerous rm -rf"
echo ""

# ─────────────────────────────────────────────────────────────────────────
echo "╔══════════════════════════════════════════╗"
printf "║  Results: %2d passed, %2d failed          ║\n" $PASSED $FAILED
echo "╚══════════════════════════════════════════╝"

[[ $FAILED -eq 0 ]] && exit 0 || exit 1
