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
| Catalog validator (`flowfoundry validate`) | ✅ 4 components + 16 capabilities + 1 workflow contract |
| CLI (`flowfoundry list/show/workflows/capabilities`) | ✅ functional |
| Capability Registry (`src/flowfoundry/capability_registry.py`) | ✅ 16 capabilities registered |
| Workflow Contract (`src/flowfoundry/workflow_contract.py`) | ✅ schema validation + CLI commands |
| Foundation tests (51 tests) | ✅ all passing |
| Workspace runtime tests | ✅ passing |
| Confera media skills tests | ✅ passing |
| Nameplate generator tests | ✅ passing |
| Feedback application tests & lint | ✅ passing |
| CI pipeline (GitHub Actions) | ✅ 3 jobs defined |

## Components bundled

1. **AI Workspace Manager** (`core/workspace-manager/`) — beta core-runtime
2. **Confera Media Skills** (`components/confera-media-skills/`) — beta workflow-pack
3. **Feedback Analysis System** (`applications/feedback-analysis-system/`) — beta reference-application
4. **Print-ready Nameplate Generator** (`workflows/print-ready-nameplate-generator/`) — stable reference-workflow

## Remaining issues

- More workflow contracts needed for the other 3 components
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
