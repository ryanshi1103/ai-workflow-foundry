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
- **Schedule**: systemd user timers (weekly quick, monthly deep, daily quarantine
  review; verified items become eligible for purge after 14 days)

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
│   Auto          Claude       DeepSeek       Codex │
│     │           native         V4 Pro    GPT-5.6  │
└─────┼─────────────┼─────────────┼────────────┼─────┘
      │             │             │            │
 FlowFoundry   permission_mode  permission_mode  profile
 goal path     ~/.claude-native ~/.claude-deepseek ~/.codex
```

## Data Flow

1. User runs `cc`
2. Project is selected (auto-detect, recent, browse, create, or manual)
3. Auto or a direct tool is selected (Auto/Claude/DeepSeek/Codex)
4. Auto selects one four-level session ceiling and enters the existing
   FlowFoundry goal path; direct tools retain their native permission menus
5. `CC_ACTIVE_PROJECT` is exported
6. Auto routes and evaluates each goal; direct choices launch the native tool
7. Project/session/recovery behavior remains owned by the existing workspace runtime

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
9. **Auto is the backend seam**: it reuses FlowFoundry context, capability
   selection, Worker permission bounding, execution, and evidence; it does not
   add a second coordinator or provider framework
