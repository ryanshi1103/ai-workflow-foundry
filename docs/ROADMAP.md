# Roadmap

FlowFoundry's roadmap moves from a tested coordination foundation toward a
user-controlled personal AI manager. Phases are capability gates, not calendar
promises. A phase is complete only when its acceptance criteria have reproducible
evidence.

Status vocabulary:

- **Implemented:** code and local test evidence exist.
- **Experimental:** code exists, but provider parity, portability, or user
  experience is incomplete.
- **Planned:** direction only; do not market as available.

## Phase 0 — Foundation

**Goal:** make AI work local-first, inspectable, recoverable, and safe to test.

### Implemented

- Component, capability, and workflow schemas with dependency-free validation.
- Project lifecycle and multi-provider launcher compatibility.
- Explicit permission modes, session records, finalization, and recovery.
- Offline fake provider and deterministic command execution.
- Durable run state, review decisions, approval records, artifacts, and reports.
- Reference media, feedback, and document workflows with explicit boundaries.

### Remaining exit criteria

- Reconcile adaptive-launcher regression contracts and pass all required suites.
- Resolve public-history privacy containment and Feedback licensing.
- Produce a clean, reproducible installation and first-run guide from a fresh
  approved publication candidate.
- Establish `SECURITY.md`, contribution governance, release notes, and a
  versioning decision.

## Phase 1 — Multi-agent orchestration

**Goal:** coordinate the minimum sufficient set of AI and deterministic
capabilities for a task.

### Implemented

- Rule-based task profiling and single/reviewed/team path selection.
- Explicit DAG planning, capability routing, bounded scheduling, retry, resume,
  cancellation, and aggregation.
- Bounded Meeting with one Context Pack, conflict detection, early stop,
  targeted cross-review, preserved dissent, and hard budgets.
- Provider readiness/auth discovery and workspace preflight.
- Managed Git worktree isolation for write-capable tasks.
- Bounded live evidence for a Codex writer and DeepSeek-compatible reviewer.

### Experimental / next

- Publish a stable provider adapter contract and conformance test kit.
- Add project-local provider and agent registry configuration without core edits.
- Verify direct Claude, live Meeting, live cancellation, and provider upgrade
  compatibility under capped test budgets.
- Add full request-level reason receipts for routing, exclusion, tool exposure,
  and budget decisions.
- Build a local operator view for plans, calls, candidates, approvals, and cost.

### Exit criteria

- At least three independent provider adapters pass the same offline contract
  suite and bounded live smoke policy.
- Interrupted writer, reviewer, approval, and cancellation paths recover without
  duplicating completed side effects.
- Real-provider runs have explicit context, network, cost, and permission receipts.
- No release-blocking security, privacy, license, or regression finding remains.

## Phase 2 — Personal context engine

**Goal:** provide user-owned context without turning chat history into an opaque
memory database.

### Planned

- Local knowledge collections with provenance, scope, freshness, and retention.
- Explicit preference and decision records, separate from inferred behavior.
- Task-specific retrieval receipts and provider disclosure policy.
- User controls for inspect, correct, export, expire, and forget.
- Local redaction/summarization before optional remote context use.
- Memory-disabled mode and project isolation by default.

### Exit criteria

- Every retrieved context item has provenance and a visible reason for inclusion.
- Users can export and delete all personal context without breaking base runtime.
- Sensitive context cannot cross a provider boundary without an explicit policy.
- Retrieval quality and privacy behavior have offline evaluation fixtures.

## Phase 3 — Adaptive AI manager

**Goal:** choose models, tools, and workflows using personal outcome evidence
while preserving hard policy and human authority.

### Planned

- Resource scheduler for cost, latency, quota, compute, privacy, and deadline.
- Task-specific provider quality evidence from validation and human review.
- Explainable recommendations for provider, workflow, review depth, and budget.
- Personal workflow templates learned only from confirmed successful outcomes.
- Reversible adaptations, confidence thresholds, and manual override.
- Broader local and remote provider ecosystem.

### Exit criteria

- Recommendations show evidence and never override permission, privacy, or budget
  constraints.
- The system demonstrates lower cost or better validated outcomes on repeatable
  user workflows than a fixed-provider baseline.
- Users can disable, reset, or export every adaptive policy.
- No optimization depends on hidden telemetry or mandatory cloud storage.

## Phase 4 — Personal Intelligence OS

**Goal:** provide an open coordination substrate across personal tools,
knowledge, devices, and workflows.

### Planned

- Portable capability and workflow ecosystem with signing and provenance.
- Cross-device coordination with clear local/remote data placement.
- Unified audit, approval, recovery, and resource views.
- Personal and organizational policy layers built on shared open contracts.
- Enterprise extensions for identity, tenancy, quotas, and compliance evidence.
- Community compatibility suite and independent workflow/provider certification.

### Exit criteria

- A user can move their context, policies, and workflow history between compatible
  installations without provider lock-in.
- Third-party capabilities pass public safety and lifecycle conformance tests.
- The platform remains useful with local-only components and no central service.
- Human authority, auditability, and reversible operation remain first-class.

## Near-term priorities

The next implementation sequence is intentionally narrower than the vision:

1. Close the history/privacy, license, and launcher regression launch gates.
2. Produce an approved, clean publication candidate and remote CI evidence.
3. Ship one polished offline AI Project Manager demo with deterministic output.
4. Extract provider adapters behind a stable, independently tested interface.
5. Add routing/tool/budget decision receipts before expanding provider count.
6. Prototype personal context only after the coordination and release substrate
   is stable.

See [Current Status](CURRENT_STATUS.md) for present evidence and
[Open-source Launch Plan](OPEN_SOURCE_LAUNCH.md) for release sequencing.
