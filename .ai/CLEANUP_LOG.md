# Cleanup Log — FlowFoundry AI

## 2026-08-04 — Initial hygiene session

### Removed
- `applications/feedback-analysis-system/:memory:` — stray SQLite database file (4 KiB).
  Already covered by `.gitignore` rule `:memory:`. Not tracked by Git.
  Likely created during a test run with an in-memory SQLite URL.

### Created
- `.ai/` project hygiene directory with standard state files
- `PROJECT_STATE.md`, `TASKS.md`, `DECISIONS.md`, `CHANGELOG.md`, `CLEANUP_LOG.md`
- `project.json`, `hygiene-state.json`

### Verified
- All 15 foundation tests pass
- All 4 catalog components validate
- `flowfoundry validate` reports: "validated 4 FlowFoundry components"
- Working tree clean

## 2026-08-04 — Second hygiene session

### Removed
- `AGENTS.md` — exact duplicate of `CLAUDE.md` (only first line differed: `# AGENTS.md` vs `# CLAUDE.md`).
  In Claude Code, `AGENTS.md` is for agent definitions, not project rules.
  The file contained project rules only — no agent definitions.

### Updated
- `.gitignore` — added patterns for workspace-manager device files (`.bashrc`, `.zshrc`, etc.),
  IDE configs (`.idea`, `.vscode`), `.claude/`, and `.mcp.json`
- `TASKS.md` — marked workflow contract schema and capability registry as done
- `CHANGELOG.md` — added v0.2.0 entries
- `PROJECT_STATE.md` — bumped version to 0.2.0, added new modules

### Verified
- Working tree clean after two commits
- No duplicate files remain
- No stale cache or temp files
- `.ai-session/` properly gitignored
