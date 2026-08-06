# Project State — FlowFoundry AI

## Identity

- **Name:** FlowFoundry AI
- **Repository:** `ai-workflow-foundry`
- **Version:** 0.2.0 (Unified Workspace + Workflow Contracts)
- **License:** MIT (bundled components retain their own licenses)

## What this is

A local-first, open foundation for designing and operating bounded AI workflows.
It combines a real project/workspace runtime, media skills, a feedback-intelligence
application, deterministic document automation, and a validated component contract
in one monorepo.

## Current runnable state

| Layer | Status |
|---|---|
| Catalog validator (`flowfoundry validate`) | ✅ 5 components + 17 capabilities + 3 workflow contracts |
| CLI (`flowfoundry list/show/workflows/capabilities`) | ✅ functional |
| Capability Registry (`src/flowfoundry/capability_registry.py`) | ✅ 17 capabilities registered |
| Workflow Contract (`src/flowfoundry/workflow_contract.py`) | ✅ schema validation + CLI commands |
| Foundation tests (94 tests) | ✅ all passing |
| Workspace runtime tests | ✅ passing |
| Confera media skills tests (3 tests) | ✅ all passing |
| Nameplate generator tests (3 tests) | ✅ all passing |
| Feedback application tests (101 tests) & lint | ✅ all passing |
| CI pipeline (GitHub Actions) | ✅ 3 jobs defined |

## Catalog components

1. **AI Workspace Manager** (`core/workspace-manager/`) — beta core-runtime
2. **Confera Media Skills** (`components/confera-media-skills/`) — beta workflow-pack
3. **Feedback Intelligence System** (`applications/feedback-intelligence-system/`) — beta reference-application
4. **Print-ready Nameplate Generator** (`workflows/print-ready-nameplate-generator/`) — stable reference-workflow
5. **Huiying / MediaFlow** (`applications/mediaflow/`) — beta compatible-extension (public contract only)

## Remaining issues

- Workflow contracts are still needed for AI Workspace Manager and Confera Media Skills
- No local workflow runner (roadmap 0.3)
- No unified operator dashboard (roadmap 0.4)
- No model-provider independence layer

## Architecture summary

```text
real project + controlled inputs
             |
             v
  workspace and permission runtime
             |
             v
     bounded workflow component
             |
             v
AI candidate / immutable revision
             |
             v
human review + explicit approval
             |
             v
validated artifact + audit record
```
