#!/bin/bash
# ============================================================================
# cc-launcher v2.0 — Deployment & Cleanup Script
# ============================================================================
# Run this ONCE after the session to deploy the fix and clean up.
# Usage: bash deploy.sh
# ============================================================================
set -euo pipefail

echo "╔══════════════════════════════════════════════════════╗"
echo "║  cc-launcher v2.0 — Deployment & Cleanup             ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ─── 1. Verify modified files are in place ────────────────────────────────

echo "1. Verifying modified files..."

verify_file() {
    local path="$1"
    local desc="$2"
    if [[ -f "$path" ]]; then
        echo "   ✓ $desc: $path"
    else
        echo "   ✗ MISSING: $path — $desc"
    fi
}

verify_file "$HOME/.local/bin/cc"                        "cc launcher (main fix)"
verify_file "$HOME/.claude/CLAUDE.md"                     "Global CLAUDE.md (user-wide rules)"
verify_file "$HOME/.claude-native/CLAUDE.md"              "Claude native CLAUDE.md"
verify_file "$HOME/.claude-deepseek/CLAUDE.md"            "DeepSeek CLAUDE.md"
verify_file "$HOME/.local/share/ai-project-manager/ai_project_manager/launcher.py" "AI PM launcher (CC_ACTIVE_PROJECT)"
verify_file "$HOME/.local/share/ai-project-manager/ai_project_manager/hooks.py"    "AI PM hooks (CC_ACTIVE_PROJECT)"

echo ""

# ─── 2. Clean recent projects file ────────────────────────────────────────

RECENT_FILE="$HOME/.local/state/cc-launcher/recent-projects"

echo "2. Cleaning recent projects..."

if [[ -f "$RECENT_FILE" ]]; then
    # Timestamp pattern: YYYYMMDD-HHMMSS-tool-shortid
    TIMESTAMP_PATTERN='^[0-9]{8}-[0-9]{6}-[a-z]+-[a-f0-9]{6}$'

    CLEANED=()
    while IFS= read -r line; do
        [[ -n "$line" ]] || continue
        [[ -d "$line" ]] || continue

        name="$(basename "$line")"

        # Filter timestamp session dirs
        if [[ "$name" =~ $TIMESTAMP_PATTERN ]]; then
            echo "   Removing timestamp dir: $line"
            continue
        fi

        # Filter session subdirs
        if [[ "$line" == *"/.ai/sessions/"* ]] || [[ "$line" == *"/.ai-session/sessions/"* ]]; then
            echo "   Removing session subdir: $line"
            continue
        fi

        CLEANED+=("$line")
    done < "$RECENT_FILE"

    # Write back (max 20)
    if [[ ${#CLEANED[@]} -gt 0 ]]; then
        printf '%s\n' "${CLEANED[@]}" | head -20 > "$RECENT_FILE"
    fi

    echo "   Recent projects cleaned. Entries: ${#CLEANED[@]}"
    echo ""
    echo "   Current entries:"
    cat "$RECENT_FILE" | while IFS= read -r l; do echo "     $l"; done
else
    echo "   No recent projects file found."
fi

echo ""

# ─── 3. Handle timestamp projects in ~/Projects ───────────────────────────

PROJECTS_DIR="$HOME/Projects"
TIMESTAMP_PATTERN='^[0-9]{8}-[0-9]{6}-[a-z]+-[a-f0-9]{6}$'
RECOVERY_DIR="$PROJECTS_DIR/_recovery-review"

echo "3. Scanning for timestamp session directories..."
FOUND_TS=()

for d in "$PROJECTS_DIR"/*/; do
    [[ -d "$d" ]] || continue
    name="$(basename "$d")"
    if [[ "$name" =~ $TIMESTAMP_PATTERN ]]; then
        FOUND_TS+=("${d%/}")
        echo "   Found: $d"
    fi
done

if [[ ${#FOUND_TS[@]} -eq 0 ]]; then
    echo "   No timestamp directories found. Clean!"
else
    echo ""
    echo "   Found ${#FOUND_TS[@]} timestamp directories."
    echo ""

    for ts_dir in "${FOUND_TS[@]}"; do
        echo "   --- $ts_dir ---"

        # Check contents
        has_git=false
        git -C "$ts_dir" rev-parse --show-toplevel &>/dev/null 2>&1 && has_git=true

        file_count=$(find "$ts_dir" -type f -not -path '*/.git/*' 2>/dev/null | wc -l)
        has_ai_session=false
        [[ -d "$ts_dir/.ai-session" ]] && has_ai_session=true

        echo "   Git: $has_git  Files: $file_count  AI session: $has_ai_session"

        # If it's just a skeleton (only .ai-session and template files), safe to delete
        if [[ "$has_git" == "false" ]] && [[ $file_count -le 10 ]] && [[ "$has_ai_session" == "true" ]]; then
            echo "   → Skeleton only. Moving to recovery..."
            mkdir -p "$RECOVERY_DIR"
            mv "$ts_dir" "$RECOVERY_DIR/$(basename "$ts_dir")" 2>/dev/null || \
                echo "   WARNING: Could not move $ts_dir (may be current working dir)"
        elif [[ "$has_git" == "true" ]] && [[ $file_count -gt 10 ]]; then
            echo "   → Has real content. KEEP and review manually."
        else
            echo "   → Uncertain. Moving to recovery for review."
            mkdir -p "$RECOVERY_DIR"
            mv "$ts_dir" "$RECOVERY_DIR/$(basename "$ts_dir")" 2>/dev/null || \
                echo "   WARNING: Could not move $ts_dir (may be current working dir)"
        fi
    done

    echo ""
    echo "   Recovery dir: $RECOVERY_DIR"
    echo "   Review contents, merge valuable work back to real projects, then delete."
fi

echo ""

# ─── 4. Verify CC_ACTIVE_PROJECT in cc ────────────────────────────────────

echo "4. Verifying CC_ACTIVE_PROJECT integration..."
if grep -q "CC_ACTIVE_PROJECT" "$HOME/.local/bin/cc"; then
    echo "   ✓ cc exports CC_ACTIVE_PROJECT"
else
    echo "   ✗ CC_ACTIVE_PROJECT NOT found in cc"
fi

if grep -q "launch-here" "$HOME/.local/bin/cc" && ! grep -q "aiproj launch-new" "$HOME/.local/bin/cc"; then
    echo "   ✓ cc uses launch-here (not launch-new)"
else
    echo "   ✗ cc may still use launch-new"
fi

echo ""

# ─── 5. Verify global CLAUDE.md ───────────────────────────────────────────

echo "5. Verifying CLAUDE.md files..."
for f in "$HOME/.claude/CLAUDE.md" "$HOME/.claude-native/CLAUDE.md" "$HOME/.claude-deepseek/CLAUDE.md"; do
    if [[ -f "$f" ]]; then
        if grep -q "项目整理" "$f" 2>/dev/null; then
            echo "   ✓ $f — has hygiene rules"
        else
            echo "   ~ $f — exists but no hygiene rules"
        fi
    else
        echo "   ✗ $f — MISSING"
    fi
done

echo ""

# ─── 6. Test cc syntax ────────────────────────────────────────────────────

echo "6. Running final syntax checks..."
bash -n "$HOME/.local/bin/cc" && echo "   ✓ cc: bash syntax OK" || echo "   ✗ cc: bash syntax ERROR"

python3 -c "import ast; ast.parse(open('$HOME/.local/share/ai-project-manager/ai_project_manager/launcher.py').read()); print('   ✓ launcher.py: OK')" 2>/dev/null || echo "   ✗ launcher.py: ERROR"
python3 -c "import ast; ast.parse(open('$HOME/.local/share/ai-project-manager/ai_project_manager/hooks.py').read()); print('   ✓ hooks.py: OK')" 2>/dev/null || echo "   ✗ hooks.py: ERROR"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  DEPLOYMENT COMPLETE                                 ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "Backup: $PWD/.ai-session/backups/20260712-231748/"
echo "Rollback: bash $PWD/.ai-session/backups/20260712-231748/rollback.sh"
echo ""
echo "Next steps:"
echo "  1. Review $RECOVERY_DIR if it exists"
echo "  2. Run 'cc' and select an existing project to test"
echo "  3. Verify Claude opens in the selected project dir"
echo ""
echo "If any issues: bash $PWD/.ai-session/backups/20260712-231748/rollback.sh"
