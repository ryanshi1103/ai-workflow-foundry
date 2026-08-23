# Architecture — AI Project Workspace Manager

## Overview

The AI Project Workspace Manager is a unified project management, launch, and maintenance system for AI toolchains. It supports three AI tools natively: Claude (Anthropic), DeepSeek, and OpenAI Codex.

## Components

### cc — Unified Launcher
- **Path**: `bin/cc` → `~/.local/bin/cc`
- **Purpose**: Project selection, tool selection, permission mode selection, and launch
- **Tools**: Claude (c), DeepSeek (d), Codex (o)
- **Key env**: `CC_ACTIVE_PROJECT` (single source of truth for project directory)

### cc-projects-maintain
- **Path**: `bin/cc-projects-maintain` → `~/.local/bin/cc-projects-maintain`
- **Purpose**: Periodic maintenance of `~/Projects/` (hygiene, dedup, quarantine, indexing)
- **Schedule**: systemd user timers (weekly quick, monthly deep, quarantine cleanup)

### FlowFoundry workspace runtime (Python)

- **Path**: `src/flowfoundry/workspace/`
- **Purpose**: lifecycle, provider selection, session tracking, recovery,
  permissions, redaction, and maintenance
- **Compatibility**: `cc`, `aiproj`, and `cc-projects-maintain` keep their
  existing entry points; the legacy `ai_project_manager` package maps old
  imports directly to canonical subpackages

```text
workspace/
├── cli/           interactive and project command entry logic
├── providers/     portable provider/profile policy (never credentials)
├── lifecycle/     stable API for project, naming, Git, and shared launch core
├── sessions/      stable API for hooks, transcripts, and recovery
│   └── finalization/  validation, pipeline, output, hooks, failure recovery
├── policy/        local-state boundaries and redaction
└── maintenance/   inventory and retention operations
```

## Tool Integration Architecture

```
┌─────────────────────────────────────────────────┐
│                    cc Launcher                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  Claude  │  │ DeepSeek │  │  Codex (new) │  │
│  │  native  │  │  V4 Pro  │  │ GPT-5.6 Sol  │  │
│  └────┬─────┘  └────┬─────┘  └──────┬───────┘  │
│       │             │               │           │
│  permission_mode  permission_mode  approval    │
│  bypassPerm...    acceptEdits...   _policy +    │
│                                    sandbox_mode │
└───────┼─────────────┼───────────────┼───────────┘
        │             │               │
   ~/.claude-    ~/.claude-      ~/.codex/
   native/       deepseek/       (profiles)
```

## Data Flow

1. User runs `cc`
2. Project is selected (auto-detect, recent, browse, create, or manual)
3. Tool is selected (Claude/DeepSeek/Codex)
4. Permission mode is selected (tool-specific menus)
5. `CC_ACTIVE_PROJECT` is exported
6. Working directory is changed to the project
7. Native AI tool is launched via `exec`

## Key Design Decisions

1. **CC_ACTIVE_PROJECT is authoritative**: All hooks and AI Project Manager respect this variable
2. **No timestamp session dirs**: `cc` never creates `YYYYMMDD-HHMMSS-tool-shortid` directories
3. **Tool-native configs**: Each tool uses its own config system (Claude: env vars, Codex: TOML profiles)
4. **launch-here over launch-new**: Always opens the selected project, never creates new ones
5. **Codex uses profiles**: 4 pre-built profiles for different permission levels, no CLI arg passthrough
6. **Runtime state is external**: sessions, transcripts, caches, provider
   credentials, and user metadata stay in local state/config roots and are not
   vendored into the workspace package
7. **Provider policy is portable**: source code owns only stable profile and
   permission identifiers; generated profiles and authentication remain local
8. **Runtime APIs are explicit**: `lifecycle` and `sessions` export curated
   canonical callables while implementation modules remain independently testable
