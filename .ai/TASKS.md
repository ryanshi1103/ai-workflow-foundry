# Tasks — FlowFoundry AI

## Active (this session)

| # | Task | Priority | Status |
|---|---|---|---|
| 1 | Clean up stray :memory: SQLite file | P0 | ✅ done |
| 2 | Set up .ai/ project hygiene files | P0 | ✅ done |
| 3 | Create portable workflow contract schema (0.2) | P1 | ✅ done |
| 4 | Create capability registry (0.2) | P1 | ✅ done |
| 5 | Create adapter contract for skills/commands (0.2) | P1 | ⏳ pending |
| 6 | Add cross-component compatibility validation | P1 | ⏳ pending |

## Roadmap 0.2 — Portable workflow contract

- [x] Versioned workflow, stage, artifact, review, and execution-approval schemas
- [ ] Adapter contract for Codex/Claude skills and deterministic local commands
- [x] Capability registry that maps reviewed intent to trusted implementations
- [ ] Cross-component workflow compatibility checks
- [ ] Shared lifecycle adapters

**Acceptance:** a workflow pack can be validated without importing its application,
and a host can reject unsafe or incompatible declarations before execution.

## Roadmap 0.3 — Local runner

- [ ] Plan-only mode before any side effect
- [ ] Persisted state machine with retry, cancel, interrupt, resume
- [ ] Content-addressed artifacts, idempotency keys, immutable approval records
- [ ] Local secret provider and deny-by-default network policy

**Acceptance:** an interrupted sample workflow resumes without modifying its inputs
or duplicating a completed side effect.

## Roadmap 0.4 — Operator experience

- [ ] Unified local dashboard and CLI over projects, stages, reviews, artifacts
- [ ] Extension discovery with provenance and license visibility
- [ ] Exportable audit bundles and privacy-preserving diagnostics
- [ ] Opt-in observability; no silent telemetry

**Acceptance:** a non-developer can understand what AI proposed, what trusted code
will do, what changed, and how to recover.

## Longer-term

- Domain packs for media, customer feedback, structured documents, data integrity
- Model-provider independence and local-model adapters
- Team review policies without cloud storage of source materials
- Public compatibility suite for third-party workflow packs
