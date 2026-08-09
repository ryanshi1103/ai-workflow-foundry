# Roadmap

The roadmap is capability-driven. Dates are intentionally omitted until each
stage has acceptance criteria and an owner.

## 0.1 — Foundation (implemented here)

- Bundled workspace lifecycle runtime with preserved history.
- Bundled media skills, feedback application, and document workflow with preserved histories.
- Component manifest schema and standard-library validator.
- Explicit integration modes and maturity labels.
- Cross-project pattern audit, architecture, and product map.
- Automated foundation and bundled-core regression tests.

## 0.2 — Portable workflow contract

- Versioned workflow, stage, artifact, review, and execution-approval schemas.
- Adapter contract for Codex/Claude skills and deterministic local commands.
- Capability registry that maps reviewed intent to trusted implementations.
- Cross-component workflow compatibility checks and shared lifecycle adapters.

Acceptance: a workflow pack can be validated without importing its application,
and a host can reject unsafe or incompatible declarations before execution.

## 0.3 — Local runner

- Plan-only mode before any side effect.
- Persisted state machine with retry, cancel, interrupt, and resume.
- Durable native execution handles with verified process-group cancellation,
  graceful termination, bounded escalation, and partial-result preservation.
- Content-addressed artifacts, idempotency keys, and immutable approval records.
- Local secret provider and deny-by-default network policy.
- Bounded adaptive Meeting with a shared context pack, deterministic conflict
  gate, early convergence, selective cross-review, hard budgets, durable
  dissent, call receipts, and experience records.

Acceptance: an interrupted sample workflow resumes without modifying its inputs
or duplicating a completed side effect.

## 0.4 — Operator experience

- Unified local dashboard and CLI over projects, stages, reviews, and artifacts.
- Extension discovery with provenance and license visibility.
- Exportable audit bundles and privacy-preserving diagnostics.
- Opt-in observability; no silent telemetry.

Acceptance: a non-developer can understand what AI proposed, what trusted code
will do, what changed, and how to recover.

## Longer-term opportunities

- Domain packs for media, customer feedback, structured documents, and data
  integrity workflows.
- Model-provider independence and local-model adapters.
- Team review policies without requiring cloud storage of source materials.
- A public compatibility suite for third-party workflow packs.
