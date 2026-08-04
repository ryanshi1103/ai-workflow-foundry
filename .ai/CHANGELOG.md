# Changelog — FlowFoundry AI

## 2026-08-04 — v0.2.0 Workflow Contracts

### Added
- Capability Registry module (`src/flowfoundry/capability_registry.py`)
- Workflow Contract module (`src/flowfoundry/workflow_contract.py`)
- JSON Schema for capability registry and workflow contracts
- Capability registry data with 16 capabilities
- Nameplate generation workflow contract
- Tests for capability registry and workflow contract
- **Unified workspace-workflow package**: workspace manager merged into `flowfoundry.workspace`
- **Unified CLI**: `flowfoundry project` subcommand group for full project lifecycle
- Python port of cc launcher (`src/flowfoundry/workspace/cc_launcher.py`)
- Backward-compat `ai_project_manager` import shim
- Workflow-contract-aware project creation (`--workflow` flag)

### Changed
- `pyproject.toml` bumped to v0.2.0; added `aiproj` entry point
- `bin/cc`, `bin/aiproj`, `bin/cc-projects-maintain` → thin Python wrappers
- Capability registry entry points updated for unified package
- `workspace/cli.py` → `run(argv) -> int` for composable CLI dispatch

### Removed
- `AGENTS.md` — duplicate of `CLAUDE.md`
- 1000+ line bash launcher in `bin/cc` (replaced by Python port)

## 2026-08-03 — v0.1.0 Foundation

### Added
- AI Workspace Manager bundled at `core/workspace-manager/` with preserved Git history
- Confera Media Skills bundled at `components/confera-media-skills/` with preserved Git history
- Feedback Analysis System bundled at `applications/feedback-analysis-system/` with preserved Git history
- Print-ready Nameplate Generator bundled at `workflows/print-ready-nameplate-generator/` with preserved Git history
- FlowFoundry catalog system: JSON Schema validator, Python library, CLI (`flowfoundry`)
- 4 component manifests in `catalog/`
- 15 foundation tests
- CI pipeline (GitHub Actions): foundation tests, workspace runtime tests, integrated component tests
- Documentation: README, ARCHITECTURE.md, PRODUCT-LINES.md, PROJECT-PATTERN-AUDIT.md, ROADMAP.md
- Branding assets

### Integrated
- Merged PR #1: agent/integrate-ai-workflow-monorepo
- Grouped and synced managed projects
- Synced integrated workspace runtime

## Historical (pre-monorepo)

- `a16bf40` — publish portable AI workspace manager
- `026310d` — publish editable nameplate generator
- `50dfbd7` — publish safety-bounded media skills
- `06ab1d8` — docs: add Feedback Analysis project logo
- `c1fa96a` — test: use unmistakably fake API credentials
- `a082a9d` — feat: publish feedback analysis system
