# Installation

## Prerequisites

- Claude CLI (for Claude native support)
- DeepSeek API key configured (for DeepSeek support)
- OpenAI Codex CLI ≥ 0.144.0 (for Codex GPT-5.6 Sol support)

## Quick Deploy

```bash
git clone https://github.com/ryanshi1103/ai-workspace-manager.git
cd ai-workspace-manager
bash scripts/deploy.sh
```

## What Gets Deployed

| Source | Destination |
|--------|------------|
| `bin/cc` | `~/.local/bin/cc` |
| `bin/cc-projects-maintain` | `~/.local/bin/cc-projects-maintain` |
| `bin/aiproj` | `~/.local/bin/aiproj` |
| FlowFoundry editable package | user Python package directory |
| `src/ai_project_manager/__init__.py` | legacy import compatibility directory |
| `config/codex/*.config.toml` | `~/.codex/` |
| `config/codex/AGENTS.md` | `~/.codex/AGENTS.md` (merged) |
| `config/systemd/*` | `~/.config/systemd/user/` |

## Codex Setup

1. Install Codex CLI:
   ```bash
   npm install -g @openai/codex
   ```

2. Log in:
   ```bash
   codex login
   ```

3. Verify:
   ```bash
   codex --version  # Should be ≥ 0.144.0
   ```

4. Deploy profiles:
   ```bash
   bash scripts/deploy.sh
   ```

## Verification

```bash
# Syntax check
bash -n ~/.local/bin/cc

# Run cc and test Codex menu
cc
# Select: project → o (Codex) → p (read-only) → yes
```

## Codex Profile Files

After deployment, these files exist in `~/.codex/`:

- `gpt56-sol-manual.config.toml`
- `gpt56-sol-readonly.config.toml`
- `gpt56-sol-auto.config.toml`
- `gpt56-sol-full.config.toml`

## Rollback

```bash
bash <backup-dir>/rollback.sh
```
