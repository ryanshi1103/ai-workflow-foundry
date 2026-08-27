# FlowFoundry Decision Ledger

Status: historical reconciliation against candidate `e9692132c20285b348b261d3483c9ae04cfd362e`

This ledger records decisions, not every old proposal. Runtime claims follow
current source and tests. Product and brand claims follow explicit Human
decisions first, then completed cross-provider convergence, then approved
briefs and participant artifacts. Historical reports remain evidence rather
than automatic current truth.

The machine-readable authority is
`.flowfoundry/decision-ledger.json`, validated by
`schemas/decision-ledger.schema.json`.

## Status rules

- **BINDING** — currently authoritative and not superseded.
- **ADOPTED** — accepted and in force, but not promoted to the same authority
  as a binding Human or converged Meeting decision.
- **ADVISORY** — useful direction that must not be described as shipped or
  mandatory.
- **OPEN** — deliberately unresolved.
- **SUPERSEDED** — once valid, then replaced by higher-precedence evidence.
- **LOST** — approved or implemented historically but absent from the current
  candidate without superseding evidence.
- **CONFLICTING** — current authorities directly disagree.
- **NEEDS_HUMAN_REVIEW** — evidence cannot resolve the decision safely.

No `OPEN` or `ADVISORY` item is treated as binding in this reconciliation.

## Summary

| Domain | Decisions |
|---|---:|
| Product | 8 |
| Brand | 6 |
| Runtime | 10 |
| UX | 4 |
| Release | 4 |
| Future | 2 |
| Architecture | 2 |
| **Total** | **36** |

| Status | Count |
|---|---:|
| BINDING | 8 |
| ADOPTED | 21 |
| ADVISORY | 4 |
| OPEN | 1 |
| SUPERSEDED | 1 |
| LOST | 1 |
| CONFLICTING | 0 |
| NEEDS_HUMAN_REVIEW | 0 |

## Product and identity

| ID | Decision | Status | Authority | Current result |
|---|---|---|---|---|
| `FF-PRODUCT-001` | Keep the name **FlowFoundry** | BINDING | Brand Council convergence | Present |
| `FF-PRODUCT-002` | Category: **Local-first Adaptive AI Team Runtime** | BINDING | Fixed binding input to Visual Identity Council | Runtime remains accurate; exact category was displaced from hero |
| `FF-PRODUCT-003` | Core principle: the smallest sufficient Agent or Team | BINDING | Fixed Meeting input plus runtime | Implemented; hero weakened it |
| `FF-PRODUCT-004` | Tagline: **One goal. The smallest sufficient AI team.** | BINDING | Visual Identity Council convergence | Missing from current hero |
| `FF-PRODUCT-005` | Chinese headline: **你定目标，AI组队实现** | BINDING | DeepSeek origin; targeted Round 2 convergence | Missing from public brand guidance |
| `FF-PRODUCT-006` | One exact plain-Chinese explanation | OPEN | Providers proposed different sentences; final artifact did not select one | Human choice remains |
| `FF-PRODUCT-007` | **AI Coordination Layer** is the current-stage explanatory layer | ADOPTED | Later productization | Useful, but incorrectly occupies category slot |
| `FF-PRODUCT-008` | “AI is moving…” is launch-story framing | ADVISORY | Later marketing proposal | Useful under “Why now,” not as primary tagline |

The correct product hierarchy is therefore:

```text
FlowFoundry
One goal. The smallest sufficient AI team.
Local-first Adaptive AI Team Runtime
Current product stage: local-first AI coordination layer
Mechanism and current proof
Long-term Personal AI direction
```

This preserves the stronger later explanation without allowing it to erase the
earlier binding category or tagline.

## Brand and visual design

| ID | Decision | Status | Authority | Current result |
|---|---|---|---|---|
| `FF-BRAND-001` | SYNTHESIS convergence-to-finished-work mark | SUPERSEDED | Visual Identity Council | Real Meeting result, later rejected by Human visual judgment |
| `FF-BRAND-002` | Council Mark: one principal star above three equal council stars | ADOPTED | Preserved human-approved final-candidate spec | Assets exist locally; not installed in `e969213` |
| `FF-BRAND-003` | Midnight/Charles Blue/ivory/ice-blue identity palette | ADOPTED | Human-approved final-candidate spec | Current public logo/docs use an older palette |
| `FF-BRAND-004` | Decisive, adaptive, grounded, capable, clear, constructive personality | ADVISORY | Participant briefs and Round 2 brief | Partly represented |
| `FF-BRAND-005` | GitHub hero semantic hierarchy | ADOPTED | Cross-provider overlap and Round 2 brief | Materially weakened |
| `FF-BRAND-006` | Student-first campus poster hierarchy | ADOPTED | Round 2 brief and preserved prototype | Historical prototype only |

`SYNTHESIS` must not be erased from project memory: it was the legitimate
cross-provider result on 2026-08-12. It also must not be reinstalled as the
official mark, because the later Human-approved Council Mark has higher
precedence. The current generic three-input/check/output logo is not evidence
that either decision was implemented.

The approved Council Mark still carries an installation caveat: the preserved
spec calls its values final-candidate working values and requires production
contrast validation. The safe public use in this reconciliation is the
self-contained app-icon SVG on its controlled midnight field.

## Runtime

| ID | Decision | Status | Implementation |
|---|---|---|---|
| `FF-RUNTIME-001` | Profile goal; select single, reviewed, or bounded-team path | ADOPTED | Implemented and tested |
| `FF-RUNTIME-002` | Context Pack → independent views → conflict gate → targeted Round 2 or early stop → decision and dissent | ADOPTED | Implemented; live brand/visual receipts exist |
| `FF-RUNTIME-003` | Verified physical cancellation with partial-result preservation | ADOPTED | Implemented; unverifiable PID is never signalled |
| `FF-RUNTIME-004` | Durable recovery across tasks, approvals, provider handles, and candidates | ADOPTED | Implemented |
| `FF-RUNTIME-005` | Provider readiness is separate from workspace compatibility | ADOPTED | Implemented; preflight can stop with zero calls |
| `FF-RUNTIME-006` | Immutable-base, leased Git worktrees for real writers | ADOPTED | Implemented; no automatic integration |
| `FF-RUNTIME-007` | Permission boundary is separate from minimum-tool exposure | ADOPTED | Implemented; strict unsupported policy fails closed |
| `FF-RUNTIME-008` | Measured, estimated, and unavailable cost states remain distinct | ADOPTED | Implemented; unknown never becomes zero |
| `FF-RUNTIME-009` | Measure redacted request envelopes before truncation | ADOPTED | Cross-provider C1 decision integrated by `f1606f8` |
| `FF-RUNTIME-010` | Fake/local default; real provider is explicit opt-in | ADOPTED | Implemented and public-demo safe |

Important runtime mechanisms did not disappear from code. The drift is mostly
explanatory: the GitHub first screen says “bounded path” but does not show why a
Meeting is exceptional or how independent views, conflict detection, targeted
Round 2, early stop, and dissent work.

## UX

| ID | Decision | Status | Candidate result |
|---|---|---|---|
| `FF-UX-001` | Content-adaptive `cc` layout with CJK-aware degradation | ADOPTED | Present |
| `FF-UX-002` | Visible `1`–`9`,`0` project shortcuts, scoped to viewport and unable to bypass gates | LOST | Implemented/fixed on preserved UX branches; absent from `e969213` |
| `FF-UX-003` | Safe Auto resolution; full/bypass always reopens permission gate | ADOPTED | Present; later hardening branch is separate |
| `FF-UX-004` | Personal AI Command Center is approval-first, mobile/PWA, no secrets or shell | ADVISORY | Designed only and correctly labeled |

The numeric-shortcut loss is not safe to repair here: restoring it requires
runtime and test integration into the sanitized candidate, which this task
explicitly forbids.

## Release, future, and architecture

| ID | Decision | Status | Result |
|---|---|---|---|
| `FF-RELEASE-001` | Sanitized new-root allowlist candidate | BINDING | Implemented in candidate lineage |
| `FF-RELEASE-002` | Push/merge/tag/release/remote mutation require Human authority | BINDING | Enforced; zero remote writes here |
| `FF-RELEASE-003` | Exact-candidate package/CI/review/privacy/license/publication gates | BINDING | Still pending |
| `FF-RELEASE-004` | GitHub is a concise product surface, not a history archive | ADOPTED | Retained during reconciliation |
| `FF-FUTURE-001` | User-owned Personal AI OS direction | ADVISORY | Future only |
| `FF-FUTURE-002` | Validate Alpha/users before personal-data ingestion | ADOPTED | Roadmap sequencing retained |
| `FF-ARCHITECTURE-001` | Monorepo integration with independent boundaries | ADOPTED | Implemented; sanitized exclusions remain |
| `FF-ARCHITECTURE-002` | Catalog/contracts declare intent; trusted code owns effects | ADOPTED | Implemented |

## Human Gate interpretation

The Brand and Visual Identity Meetings were launched with tasks that expressly
called their results binding. No separate durable post-Meeting Human Gate
receipt was found for the name, tagline, category, or Chinese headline. The
ledger therefore records their authority as completed convergence and records
`human_gate.status` as `NOT_RECORDED`; it does not invent an approval receipt.

The later Council Mark is different. Its preserved asset specification
explicitly says “human-approved visual direction,” and project-local session
events preserve the iterative Human-driven path. The raw approving user turn is
not available in the project-local redacted record, so the ledger limits the
claim to that preserved spec and keeps production contrast validation open.

## Evidence boundary

Durable `.flowfoundry/runs/`, `.flowfoundry/design/`, and project-local
`.ai-session/` artifacts are local historical evidence and are not automatically
publication-safe. This public reconciliation cites them by logical path but
does not copy participant payloads, machine paths, private session bodies, or
incident material into the release candidate.
