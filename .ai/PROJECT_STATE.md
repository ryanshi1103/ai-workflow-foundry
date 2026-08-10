# Project State — FlowFoundry AI

Verified against the repository and tests on 2026-08-10. Git and executable
code take precedence over older migration reports.

## Identity and Git baseline

- **Name:** FlowFoundry AI
- **Repository:** `ai-workflow-foundry`
- **Version:** 0.2.0 (pre-v1 orchestration hardening)
- **Branch:** `portfolio-migration`
- **HEAD at Phase 4 start:** `f194dc3a88a9fea47631ffe139ecdbd79dc90bde`
- **Upstream:** `origin/portfolio-migration`
- **Working tree at audit start:** dirty; one pre-existing `.gitignore` change and
  multiple untracked owner reports were preserved.

## Current runnable state

| Layer | Verified status |
|---|---|
| Catalog and workflow validation | 5 components, 17 capabilities, 3 workflow contracts |
| Workspace and `cc` runtime | Claude, DeepSeek-via-Claude, and Codex launcher compatibility; 66 Python tests pass |
| Task intelligence | Rule-based task profile and `single_agent`, `single_agent_reviewer`, or `multi_agent` minimum path |
| Agent registry | Capability, tool, context, privacy, availability, auth-state, cost-class, and reliability metadata |
| Provider discovery | Runtime discovery without reading or printing credential values |
| Planner and DAG | Explicit JSON plans plus adaptive bounded plans |
| Team runtime | Atomic tasks, dependency scheduling, mailbox, review, approval, aggregation, retry, resume, and durable provider cancellation |
| Bounded Meeting | Durable state machine, one Context Pack, independent views, deterministic conflict gate, early stop, targeted cross-review, convergence with dissent, hard budgets, validation, cancellation, and resume receipts |
| Workspace isolation | Authoritative project root plus immutable-base managed Git worktrees for real writers; durable ownership, exclusive leases, candidate diff/validation, cancellation retention, recovery, and safe clean-only cleanup |
| Provider adapters | Structured Codex and Claude-compatible CLI envelopes with durable process handles and POSIX process-group cancellation; real execution remains explicit opt-in |
| Cost and performance | Per-attempt calls/token/latency/cost plus project-local agent statistics |
| Provider setup | Missing runtime becomes a persisted `setup_required` artifact instead of a crash |
| Foundation tests | 160 passed after managed writer isolation, including 24 Phase 4 fixture/integration tests |

## Honest v1 boundary

The offline single-agent and team paths are runnable and recoverable. Native
provider commands now have structured seams, but no billed provider call was
made during this audit, so live authentication, model availability, and
provider-specific token fields remain **unverified**. DeepSeek reuses the
existing isolated Claude-compatible runtime; it is not assumed to have a
standalone executable.

Adaptive `multi_agent` plans now enter a bounded Meeting; explicit legacy DAG
plans remain compatible. No billed provider call was made, so native structured
Meeting responses remain unverified against live models. Cancellation now
stops scheduling, verifies the persisted process identity, requests graceful
process-group termination, escalates only after a grace period, and preserves
partial output and accounting. Cross-process physical cancellation currently
depends on Linux `/proc` identity metadata; an unverifiable PID is never
signalled and its writer lease is not released automatically. Real write-capable
DAG tasks now run in FlowFoundry-owned Git worktrees and validators reuse the
exact candidate. Dirty main-worktree state is left untouched; tasks that
explicitly depend on it require a future snapshot capability. Automatic
candidate merge/push/PR, full submodule lifecycle support, local-model hardware
selection, and plugin loading from external registry files remain later work.

See `docs/V1-AUDIT.md` for the capability map and prioritized shortest path.
