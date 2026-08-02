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

### ai-project-manager (Python)
- **Path**: `src/ai_project_manager/` → `~/.local/share/ai-project-manager/ai_project_manager/`
- **Purpose**: Session tracking, project creation/cleanup/recovery, auto-naming, transcript processing

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
