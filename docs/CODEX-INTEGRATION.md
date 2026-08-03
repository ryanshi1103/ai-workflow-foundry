# Codex Integration — GPT-5.6 Sol

OpenAI Codex GPT-5.6 Sol is the third native tool in the `cc` launcher, alongside Claude and DeepSeek.

## Architecture

```
cc launcher
├── Project Selection (shared)
├── Tool Menu: c=Claude, d=DeepSeek, o=Codex, q=quit
│   └── Codex → Permission Menu: m/p/a/b
│       ├── m: Manual      → approval=on-request, sandbox=workspace-write
│       ├── p: Read-only   → approval=never,      sandbox=read-only
│       ├── a: Auto        → approval=never,      sandbox=workspace-write
│       └── b: Full access → approval=never,      sandbox=danger-full-access
```

## Profiles

Four profiles in `~/.codex/`:

| Profile | File | Approval | Sandbox |
|---------|------|----------|---------|
| Manual | `gpt56-sol-manual.config.toml` | on-request | workspace-write |
| Read-only | `gpt56-sol-readonly.config.toml` | never | read-only |
| Auto | `gpt56-sol-auto.config.toml` | never | workspace-write |
| Full | `gpt56-sol-full.config.toml` | never | danger-full-access |

All profiles use:
- `model = "gpt-5.6-sol"`
- `model_reasoning_effort = "high"`
- `model_reasoning_summary = "auto"`
- `model_verbosity = "medium"`

## Launch Commands

```bash
codex --profile gpt56-sol-manual
codex --profile gpt56-sol-readonly
codex --profile gpt56-sol-auto
codex --profile gpt56-sol-full
```

## Key Differences from Claude

- Codex uses `approval_policy` and `sandbox_mode` — NOT Claude's `permission_mode`
- Codex does NOT use `CLAUDE_CONFIG_DIR`, `ANTHROPIC_BASE_URL`, or `ANTHROPIC_AUTH_TOKEN`
- Codex sessions are stored in `~/.codex/sessions/`, not in project `.ai/sessions/`
- Codex config is TOML-based (`~/.codex/config.toml` + profiles)
- `CC_ACTIVE_PROJECT` is still exported and the working directory is set to the project

## Preflight Checks

Before launching Codex, `cc` runs:
1. `command -v codex` — binary exists
2. `codex --version` — version ≥ 0.144.0
3. Project directory exists
4. Profile TOML is valid
5. Network basic check

Results cached in `${XDG_STATE_HOME:-$HOME/.local/state}/cc-launcher/codex-preflight`.

## Model Unavailability

If GPT-5.6 Sol is not available for the account, `cc` shows:
- Clear error message (not silent fallback)
- Option 1: Return to tool menu
- Option 2: Use Codex default model (only with explicit user consent)
- Option q: Quit

## Requirements

- Codex CLI ≥ 0.144.0
- Authenticated via `codex login`
- GPT-5.6 Sol available for the account
