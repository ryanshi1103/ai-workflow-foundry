#!/bin/bash
# deploy-to-final.sh — Complete the core project deployment from staging
# Run this OUTSIDE the Claude Code sandbox (or after sandbox exits)
set -euo pipefail

STAGING="$HOME/Projects/13/staging-core"
FINAL="$HOME/Projects/ai-project-workspace-manager"

if [ ! -d "$STAGING" ]; then
    echo "Error: Staging directory not found: $STAGING"
    echo "The staging directory may have been cleaned up."
    echo "Source files are also available at:"
    echo "  ~/.local/share/ai-project-manager/ai_project_manager/"
    echo "  ~/.local/bin/cc"
    echo "  ~/.local/bin/cc-projects-maintain"
    exit 1
fi

echo "Deploying from staging to final project..."
echo "  Source: $STAGING"
echo "  Target: $FINAL"

mkdir -p "$FINAL"/{src/ai_project_manager,bin,config/systemd,docs,tests,scripts,.ai}

cp -v "$STAGING/src/ai_project_manager/"*.py "$FINAL/src/ai_project_manager/"
cp -v "$STAGING/bin/cc" "$FINAL/bin/cc"
cp -v "$STAGING/bin/cc-projects-maintain" "$FINAL/bin/cc-projects-maintain"
cp -v "$STAGING/bin/aiproj" "$FINAL/bin/aiproj"
cp -v "$STAGING/config/"*.example "$FINAL/config/" 2>/dev/null || true
cp -v "$STAGING/config/systemd/"*.service "$FINAL/config/systemd/" 2>/dev/null || true
cp -v "$STAGING/config/systemd/"*.timer "$FINAL/config/systemd/" 2>/dev/null || true
cp -v "$STAGING/tests/"* "$FINAL/tests/" 2>/dev/null || true
cp -v "$STAGING/scripts/deploy.sh" "$FINAL/scripts/" 2>/dev/null || true
chmod +x "$FINAL/bin/"*

echo ""
echo "Deployment complete. Verifying..."
find "$FINAL" -type f | sort
echo ""
echo "File count: $(find "$FINAL" -type f | wc -l)"
echo ""
echo "Next steps:"
echo "  1. cd $FINAL"
echo "  2. git init && git add -A && git commit -m 'Initial commit: AI Project Workspace Manager'"
echo "  3. ./scripts/verify.sh"
