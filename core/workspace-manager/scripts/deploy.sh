#!/bin/bash
# ============================================================================
# cc-launcher v3.1 — Deployment Script (Claude + DeepSeek + Codex + SSH remote safety)
# ============================================================================
# Deploys cc launcher, Codex profiles, AGENTS.md, and systemd units.
# Usage: bash deploy.sh
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MONOREPO_CANDIDATE="$(cd "$PROJECT_ROOT/../.." 2>/dev/null && pwd || true)"
if [[ -f "$MONOREPO_CANDIDATE/pyproject.toml" ]] \
        && [[ -d "$MONOREPO_CANDIDATE/src/flowfoundry" ]]; then
    PACKAGE_ROOT="$MONOREPO_CANDIDATE"
else
    PACKAGE_ROOT="$PROJECT_ROOT"
fi
PYTHON_LAUNCHER_SOURCE="$PACKAGE_ROOT/src/flowfoundry/workspace/cli/launcher.py"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/cc-projects/backups/${TIMESTAMP}-cc-v31"

echo "╔══════════════════════════════════════════════════════╗"
echo "║  cc-launcher v3.1 — Deployment (Claude/DeepSeek/Codex) ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ─── 0. Create backup ────────────────────────────────────────────────────────
echo "0. Creating backup..."
mkdir -p "$BACKUP_DIR"

backup_if_exists() {
    local src="$1"
    if [[ -f "$src" ]]; then
        cp -v "$src" "$BACKUP_DIR/" 2>&1 | sed 's/^/   /'
    fi
}

backup_if_exists "$HOME/.local/bin/cc"
backup_if_exists "$HOME/.local/bin/cc-projects-maintain"
backup_if_exists "$HOME/.codex/config.toml"
backup_if_exists "$HOME/.codex/AGENTS.md"
backup_if_exists "${XDG_STATE_HOME:-$HOME/.local/state}/cc-launcher/recent-projects"
backup_if_exists "$HOME/.config/cc-projects/managed-projects"

# Backup existing Codex profiles if they exist
for profile in gpt56-sol-manual gpt56-sol-readonly gpt56-sol-auto gpt56-sol-full; do
    backup_if_exists "$HOME/.codex/${profile}.config.toml"
done

# Generate SHA256SUMS for all backed-up files
( cd "$BACKUP_DIR" && sha256sum ./* 2>/dev/null > SHA256SUMS )

# Generate MANIFEST
cat > "$BACKUP_DIR/MANIFEST.txt" << MANIFEST
cc Launcher v3.1 Deployment — Backup
========================================
Date: $(date -Iseconds)
Source project: $PROJECT_ROOT

Files backed up:
$(cd "$BACKUP_DIR" && ls -1 * 2>/dev/null | grep -v SHA256SUMS | grep -v MANIFEST | sed 's/^/  - /')

To rollback: bash $BACKUP_DIR/rollback.sh
MANIFEST

# Generate rollback.sh
cat > "$BACKUP_DIR/rollback.sh" << ROLLBACK
#!/bin/bash
# Rollback cc launcher v3.1 deployment
# Generated: $(date -Iseconds)
set -euo pipefail
echo "Rolling back cc launcher v3.1 deployment..."

RESTORE_DIR="$BACKUP_DIR"

if [[ -f "\$RESTORE_DIR/cc" ]]; then
    cp -v "\$RESTORE_DIR/cc" "\$HOME/.local/bin/cc"
    chmod +x "\$HOME/.local/bin/cc"
    echo "   ✓ cc restored"
fi

if [[ -f "\$RESTORE_DIR/cc-projects-maintain" ]]; then
    cp -v "\$RESTORE_DIR/cc-projects-maintain" "\$HOME/.local/bin/cc-projects-maintain"
    chmod +x "\$HOME/.local/bin/cc-projects-maintain"
    echo "   ✓ cc-projects-maintain restored"
fi

if [[ -f "\$RESTORE_DIR/managed-projects" ]]; then
    mkdir -p "\$HOME/.config/cc-projects"
    cp -v "\$RESTORE_DIR/managed-projects" "\$HOME/.config/cc-projects/managed-projects"
    echo "   ✓ managed project policy restored"
fi

if [[ -f "\$RESTORE_DIR/config.toml" ]]; then
    cp -v "\$RESTORE_DIR/config.toml" "\$HOME/.codex/config.toml"
    echo "   ✓ config.toml restored"
fi

if [[ -f "\$RESTORE_DIR/AGENTS.md" ]]; then
    cp -v "\$RESTORE_DIR/AGENTS.md" "\$HOME/.codex/AGENTS.md"
    echo "   ✓ AGENTS.md restored"
fi

# Restore profiles that existed before
for profile in gpt56-sol-manual gpt56-sol-readonly gpt56-sol-auto gpt56-sol-full; do
    if [[ -f "\$RESTORE_DIR/\${profile}.config.toml" ]]; then
        cp -v "\$RESTORE_DIR/\${profile}.config.toml" "\$HOME/.codex/\${profile}.config.toml"
        echo "   ✓ \${profile} restored"
    else
        # Remove if newly created (not in backup)
        rm -f "\$HOME/.codex/\${profile}.config.toml"
        echo "   ~ \${profile} removed (was new)"
    fi
done

echo ""
echo "Rollback complete."
echo "Note: auth.json was never touched by deploy or rollback."
ROLLBACK
chmod +x "$BACKUP_DIR/rollback.sh"

echo "   Backup: $BACKUP_DIR"
echo "   Rollback: $BACKUP_DIR/rollback.sh"
echo ""

# ─── 1. Deploy cc launcher ───────────────────────────────────────────────────
echo "1. Deploying cc launcher..."

# Preserve the pre-unification legacy launcher as the wrapper's fallback.
# Only copy when the installed cc is still the legacy script, so a re-run
# of deploy never clobbers cc-legacy with the wrapper itself.
if [[ -f "$HOME/.local/bin/cc" ]] && ! grep -q 'flowfoundry.cc' "$HOME/.local/bin/cc"; then
    cp -v "$HOME/.local/bin/cc" "$HOME/.local/bin/cc-legacy"
    chmod +x "$HOME/.local/bin/cc-legacy"
    echo "   ✓ legacy cc preserved as cc-legacy fallback"
fi

cp -v "$PROJECT_ROOT/bin/cc" "$HOME/.local/bin/cc"
chmod +x "$HOME/.local/bin/cc"
echo "   ✓ cc deployed"
cp -v "$PROJECT_ROOT/bin/cc-projects-maintain" "$HOME/.local/bin/cc-projects-maintain"
chmod +x "$HOME/.local/bin/cc-projects-maintain"
echo "   ✓ cc-projects-maintain deployed"

mkdir -p "$HOME/.config/cc-projects"
if [[ ! -f "$HOME/.config/cc-projects/managed-projects" ]]; then
    cp -v "$PROJECT_ROOT/config/managed-projects.example" "$HOME/.config/cc-projects/managed-projects"
    echo "   ✓ managed project policy installed"
else
    echo "   ~ managed project policy preserved"
fi
echo ""

# ─── 2. Deploy Codex profiles ────────────────────────────────────────────────
echo "2. Deploying Codex profiles..."

mkdir -p "$HOME/.codex"

extract_codex_project_sections() {
    local profile_file="$1"
    awk '
        /^\[/ {
            in_projects = ($0 ~ /^\[projects([.\]]|$)/)
        }
        in_projects { print }
    ' "$profile_file"
}

for profile in gpt56-sol-manual gpt56-sol-readonly gpt56-sol-auto gpt56-sol-full; do
    src="$PROJECT_ROOT/config/codex/${profile}.config.toml"
    dst="$HOME/.codex/${profile}.config.toml"

    tmp_profile="$(mktemp)"
    cat "$src" > "$tmp_profile"

    if [[ -f "$dst" ]]; then
        preserved_projects="$(extract_codex_project_sections "$dst")"
        if [[ -n "$preserved_projects" ]]; then
            printf '\n%s\n' "$preserved_projects" >> "$tmp_profile"
            echo "   ~ ${profile}: preserving local [projects] trust entries"
        else
            echo "   ~ ${profile}: no local [projects] entries to preserve"
        fi
    fi

    install -m 0600 "$tmp_profile" "$dst"
    rm -f "$tmp_profile"
    echo "   ✓ ${profile} deployed (mode 600)"
done
echo "   ✓ All 4 Codex profiles deployed"
echo ""

# ─── 3. Deploy/merge Codex AGENTS.md ─────────────────────────────────────────
echo "3. Deploying Codex AGENTS.md..."
CODEX_AGENTS_SRC="$PROJECT_ROOT/config/codex/AGENTS.md"
CODEX_AGENTS_DST="$HOME/.codex/AGENTS.md"

if [[ -f "$CODEX_AGENTS_DST" ]]; then
    # Merge: keep existing content, append new rules not already present
    echo "   Existing AGENTS.md found — merging..."
    tmp_merged="$(mktemp)"

    # Copy existing content first
    cat "$CODEX_AGENTS_DST" > "$tmp_merged"

    # Append new rules from source that aren't in destination
    while IFS= read -r line; do
        if ! grep -qF "$line" "$CODEX_AGENTS_DST" 2>/dev/null; then
            echo "$line" >> "$tmp_merged"
        fi
    done < "$CODEX_AGENTS_SRC"

    mv "$tmp_merged" "$CODEX_AGENTS_DST"
    echo "   ✓ AGENTS.md merged"
else
    cp -v "$CODEX_AGENTS_SRC" "$CODEX_AGENTS_DST"
    echo "   ✓ AGENTS.md deployed (new)"
fi
echo ""

# ─── 4. Install FlowFoundry unified package ──────────────────────────────
echo "4. Installing FlowFoundry unified package..."
if [[ -f "$PACKAGE_ROOT/pyproject.toml" ]]; then
    if command -v pip3 &>/dev/null; then
        pip3 install --user -e "$PACKAGE_ROOT" 2>&1 | sed 's/^/   /'
        echo "   ✓ FlowFoundry package installed (pip install --user -e)"
    else
        echo "   ~ pip3 not found, skipping"
    fi
    # Legacy package maps old imports directly to canonical subpackages.
    PM_DST="$HOME/.local/share/ai-project-manager/ai_project_manager"
    mkdir -p "$PM_DST"
    cp -v "$PACKAGE_ROOT/src/ai_project_manager/"*.py "$PM_DST/" 2>/dev/null || true
else
    echo "   ~ FlowFoundry package root not found, skipping"
fi
echo ""

# ─── 5. Deploy systemd units ─────────────────────────────────────────────────
echo "5. Deploying systemd units..."
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
if [[ -d "$PROJECT_ROOT/config/systemd" ]]; then
    mkdir -p "$SYSTEMD_USER_DIR"
    cp -v "$PROJECT_ROOT/config/systemd/"*.service "$SYSTEMD_USER_DIR/" 2>/dev/null || true
    cp -v "$PROJECT_ROOT/config/systemd/"*.timer "$SYSTEMD_USER_DIR/" 2>/dev/null || true
    if command -v systemctl &>/dev/null && systemctl --user daemon-reload 2>/dev/null; then
        echo "   ✓ systemd units deployed and user manager reloaded"
    else
        echo "   ~ systemd units deployed; user manager unavailable, reload skipped"
    fi
else
    echo "   ~ No systemd configs found, skipping"
fi
echo ""

# ─── 6. Verification ─────────────────────────────────────────────────────────
echo "6. Running verification..."

VERIFY_OK=0
VERIFY_FAIL=0

verify_pass() { echo "   ✓ $1"; VERIFY_OK=$((VERIFY_OK+1)); }
verify_fail() { echo "   ✗ $1"; VERIFY_FAIL=$((VERIFY_FAIL+1)); }

# bash -n on deployed cc
bash -n "$HOME/.local/bin/cc" 2>/dev/null && verify_pass "cc bash syntax OK" || verify_fail "cc bash syntax ERROR"
bash -n "$HOME/.local/bin/cc-projects-maintain" 2>/dev/null && verify_pass "maintenance bash syntax OK" || verify_fail "maintenance bash syntax ERROR"

grep -q 'ai-workspace-manager.*managed.*true' "$HOME/.config/cc-projects/managed-projects" \
    && verify_pass "managed project policy deployed" \
    || verify_fail "managed project policy missing"

# Wrapper delegates to the unified public module.
grep -q 'python3 -m flowfoundry.cc' "$HOME/.local/bin/cc" \
    && verify_pass "cc delegates to flowfoundry.cc" \
    || verify_fail "cc unified module delegation MISSING"

# Provider menu and launch paths live in the Python runtime after unification.
grep -q 'Claude' "$PYTHON_LAUNCHER_SOURCE" && verify_pass "Claude mode preserved" || verify_fail "Claude mode MISSING"

grep -q 'DeepSeek' "$PYTHON_LAUNCHER_SOURCE" && verify_pass "DeepSeek mode preserved" || verify_fail "DeepSeek mode MISSING"

grep -q 'OpenAI Codex' "$PYTHON_LAUNCHER_SOURCE" && verify_pass "Codex mode preserved" || verify_fail "Codex mode MISSING"

# Codex profiles deployed
for profile in gpt56-sol-manual gpt56-sol-readonly gpt56-sol-auto gpt56-sol-full; do
    if [[ -f "$HOME/.codex/${profile}.config.toml" ]]; then
        verify_pass "Profile ${profile} deployed"
    else
        verify_fail "Profile ${profile} MISSING"
    fi
done

# Profile TOML validity
for profile in gpt56-sol-manual gpt56-sol-readonly gpt56-sol-auto gpt56-sol-full; do
    if grep -q 'model.*gpt-5.6-sol' "$HOME/.codex/${profile}.config.toml" 2>/dev/null; then
        verify_pass "Profile ${profile}: model = gpt-5.6-sol ✓"
    else
        verify_fail "Profile ${profile}: model = gpt-5.6-sol MISSING"
    fi

    profile_mode="$(stat -c '%a' "$HOME/.codex/${profile}.config.toml" 2>/dev/null || true)"
    if [[ "$profile_mode" == "600" ]]; then
        verify_pass "Profile ${profile}: permissions = 600"
    else
        verify_fail "Profile ${profile}: permissions are ${profile_mode:-unknown}, expected 600"
    fi
done

# AGENTS.md deployed
[[ -f "$HOME/.codex/AGENTS.md" ]] && verify_pass "AGENTS.md deployed" || verify_fail "AGENTS.md MISSING"

# CC_ACTIVE_PROJECT preserved
grep -q 'CC_ACTIVE_PROJECT' "$PYTHON_LAUNCHER_SOURCE" && verify_pass "CC_ACTIVE_PROJECT preserved" || verify_fail "CC_ACTIVE_PROJECT MISSING"

# Codex launch path (resolved binary preserves the native Codex TUI)
grep -q 'os.execv(codex_bin' "$PYTHON_LAUNCHER_SOURCE" && verify_pass "native Codex exec launch path" || verify_fail "native Codex exec MISSING"

# Installed package import verifies that the deployed wrappers can resolve the
# same public modules exercised from a source checkout.
if HOME="$HOME" python3 -c 'import flowfoundry.aiproj; import flowfoundry.workspace.cli.launcher' 2>/dev/null; then
    verify_pass "FlowFoundry launcher modules import"
else
    verify_fail "FlowFoundry launcher modules are not importable"
fi

# Exclude documentation/verification lines, then reject any file operation that
# targets auth.json.  The deploy must never read, copy, overwrite, or remove it.
if awk '!/auth[.]json/' "$PROJECT_ROOT/scripts/deploy.sh" | grep -Eq '(cp|mv|rm|install|chmod|chown|cat|sed)[[:space:]].*auth[.]json'; then
    verify_fail "auth.json file operation found in deploy"
else
    verify_pass "auth.json untouched by deploy"
fi

echo ""
echo "   Verification: ${VERIFY_OK} passed, ${VERIFY_FAIL} failed"
echo ""

# ─── 7. Summary ──────────────────────────────────────────────────────────────
echo "╔══════════════════════════════════════════════════════╗"
echo "║  DEPLOYMENT COMPLETE                                 ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "Deployed:"
echo "  ~/.local/bin/cc                  — unified launcher v3.1"
echo "  ~/.codex/gpt56-sol-manual.config.toml"
echo "  ~/.codex/gpt56-sol-readonly.config.toml"
echo "  ~/.codex/gpt56-sol-auto.config.toml"
echo "  ~/.codex/gpt56-sol-full.config.toml"
echo "  ~/.codex/AGENTS.md               — Codex global rules"
echo ""
echo "Backup: $BACKUP_DIR"
echo "Rollback: bash $BACKUP_DIR/rollback.sh"
echo ""
echo "Codex start commands:"
echo "  codex --profile gpt56-sol-manual    (手动确认)"
echo "  codex --profile gpt56-sol-readonly  (只读)"
echo "  codex --profile gpt56-sol-auto      (自动执行)"
echo "  codex --profile gpt56-sol-full      (完全访问)"
echo ""

# Return non-zero if verification failed
[[ $VERIFY_FAIL -eq 0 ]]
