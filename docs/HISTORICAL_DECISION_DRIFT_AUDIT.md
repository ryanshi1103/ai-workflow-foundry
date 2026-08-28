# Historical Decision Drift Audit

Audit target: productized candidate `e9692132c20285b348b261d3483c9ae04cfd362e`

This audit compares the evidence-backed [Decision Ledger](DECISION_LEDGER.md)
with the candidate README, product/architecture/roadmap documents, demos,
marketing copy, contributor surface, SVG assets, and release boundary.

## Classification

| Decision or surface | Classification before reconciliation | Evidence-based finding | Reconciliation |
|---|---|---|---|
| Official name FlowFoundry | PRESENT_AND_CORRECT | Name is consistent across GitHub, CLI, package, and docs | None |
| `KEEP FLOWFOUNDRY` provenance | MISSING | Current surface uses the name but does not preserve why it survived a real cross-provider challenge | Ledger/report only; do not turn README into history |
| Category: Local-first Adaptive AI Team Runtime | CONTRADICTED | Runtime remains compatible, but README hero substitutes “local-first AI coordination layer” in the category slot | Restore official category and retain coordination layer as current-stage explanation |
| Current stage: AI Coordination Layer | PRESENT_BUT_REPHRASED | Useful later layer; not a binding category replacement | Keep beneath official category |
| Core principle: smallest sufficient Agent or Team | PRESENT_BUT_WEAKENED | Appears below the first screen and in architecture, not in primary promise | Restore tagline and compact mechanism proof |
| English tagline | MISSING | `One goal. The smallest sufficient AI team.` disappeared from README/public brand guidance | Restore to hero and visual guide |
| “AI is moving from individual models…” | PRESENT_BUT_WEAKENED | Good launch-story insight but promoted into the binding tagline slot | Move to “Why now” framing |
| Chinese headline | MISSING | Verified DeepSeek-origin Round 2 decision survives only in local design evidence | Restore to brand/poster guidance; do not overload GitHub hero |
| Exact Chinese explanation | NEEDS_HUMAN_DECISION | Providers supplied different useful sentences; final compact convergence selected no exact sentence | Keep OPEN and queue one bounded Human choice |
| SYNTHESIS logo direction | SUPERSEDED_VALIDLY | Real Meeting decision, later rejected by Human visual judgment | Preserve provenance; do not reinstall |
| Human-approved Council Mark | MISSING | Final candidate assets exist locally, while GitHub still uses an older generic coordination/check mark | Install controlled-field app-icon SVG and publish its spec |
| Identity palette | CONTRADICTED | Current public visual guide describes an older navy/violet/cyan/green system | Separate Council identity palette from functional UI state colors |
| Visual anti-cliche rules | PRESENT_AND_CORRECT | Current guide rejects robots, brains, sparkles, and futuristic excess | Retain; clarify that the Council Mark's star geometry is controlled, not generic decoration |
| GitHub hero semantic hierarchy | PRESENT_BUT_WEAKENED | Mark/name, CTA, and proof diagram exist; binding tagline/category/workflow/proof row do not | Restore fewer authoritative layers |
| Compact workflow: Goal → Profile → Minimum Sufficient Team → Execute → Validate | MISSING | Architecture exists, but the adopted compact proof is absent | Restore one compact line in hero |
| Proof row: local-first, adaptive sizing, bounded meetings, execution, validation, recovery | MISSING | Capabilities appear later in prose/table, not as first-screen proof | Restore one small proof row |
| Campus poster hierarchy | MISSING | Prototype is preserved locally; public visual guide does not state the adopted order | Restore hierarchy to visual guide; no public poster claim |
| Minimum sufficient path modes | PRESENT_AND_CORRECT | README and architecture accurately describe bounded planning | Strengthen first-screen language only |
| Simple tasks avoid Meetings | PRESENT_BUT_WEAKENED | Architecture implies mode selection; README can sound team-centric | State single-agent path explicitly |
| Independent Round 1 views | MISSING | Current first screen never explains independence | Add concise bounded-Meeting proof in README mechanism section |
| Conflict detection and targeted Round 2 | MISSING | Architecture mentions it; README does not | Add concise proof, link to architecture |
| Early stop and dissent preservation | MISSING | Architecture mentions early convergence/dissent; README does not | Add concise proof, avoid detailed history |
| Physical cancellation | PRESENT_BUT_REPHRASED | Durable recovery comparison mentions cancellation; exact safety semantics live in architecture | No hero expansion; retain architecture authority |
| Durable recovery | PRESENT_AND_CORRECT | Present throughout current story | None |
| Workspace compatibility preflight | PRESENT_AND_CORRECT | Current architecture/status accurately separate preflight | None |
| Writer/worktree isolation | PRESENT_AND_CORRECT | Current README and architecture are accurate | None |
| Provider readiness | PRESENT_AND_CORRECT | Current status and architecture explain readiness boundaries | None |
| Permission versus tool exposure | PRESENT_BUT_WEAKENED | Both exist, but only architecture explains their independence | Retain detailed explanation in architecture |
| Cost truthfulness | PRESENT_AND_CORRECT | Current comparison says provider-reported and unknown remains unknown | None |
| Redacted request-envelope metrics | MISSING | Implemented Meeting-adopted diagnostic has no public explanation | Keep in ledger; too low-level for first screen |
| Adaptive `cc` launcher | PRESENT_AND_CORRECT | Candidate contains content-adaptive layout and safe Auto contract | None |
| Numeric project shortcuts | MISSING | Implemented and fixed in preserved UX branches but absent from candidate source/tests/docs | Classify LOST; do not modify runtime in this task |
| Personal AI Command Center | PRESENT_AND_CORRECT | Clearly marked designed/not implemented | None |
| Personal AI OS | PRESENT_AND_CORRECT | Clearly marked future | None |
| GitHub Release Assistant | PRESENT_AND_CORRECT | Demo is honest about fake providers and no publication effects | None |
| Sanitized history/candidate lineage | PRESENT_AND_CORRECT | Candidate docs distinguish incident-bearing history | None |
| No push/merge/tag/release authority | PRESENT_AND_CORRECT | Release and trust docs remain explicit | None |
| Exact-candidate release gates | PRESENT_AND_CORRECT | Current status remains blocked pending evidence | None |

## Category reconciliation

“Local-first Adaptive AI Team Runtime” and “local-first AI coordination layer”
are not mutually exclusive when assigned different jobs:

| Layer | Correct term | Purpose |
|---|---|---|
| Official product category | **Local-first Adaptive AI Team Runtime** | Binding identity and distinctive runtime promise |
| Current maturity/stage | **AI Coordination Layer** | Honest description of what the Alpha exposes today |
| Mechanism | Minimum sufficient path across eligible models/tools | Explains how the runtime behaves |
| Proof | Offline execution, bounded Meetings, review/validation, approval, recovery | What the candidate can demonstrate |
| Vision | Personal AI Command Center → Personal AI OS | Future direction, explicitly unshipped |

No later binding artifact was found that retired the official category. The
coordination-layer language is a legitimate explanatory improvement and is
retained, but its use as a silent replacement was unauthorized drift.

## Tagline reconciliation

The sentences serve different hierarchy levels:

- **Brand promise:** “One goal. The smallest sufficient AI team.”
- **Market insight:** “AI is moving from individual models to coordinated
  systems.”

The market insight improves the launch story but does not supersede the
cross-provider tagline. The reconciliation restores the brand promise to the
hero and keeps the insight under the problem/why-now narrative.

## Visual conflict

Three distinct visual states existed:

1. **SYNTHESIS** — a legitimate 2026-08-12 cross-provider convergence result.
2. **Council Mark** — the later 2026-08-13 human-approved visual direction,
   which supersedes SYNTHESIS under the stated precedence rules.
3. **Current candidate logo** — an older three-input/check/output coordination
   mark with navy/violet/cyan/green treatment.

The third state is neither the Meeting decision nor the later Human decision.
It is therefore product-surface drift, not a valid supersession. The approved
Council app-icon asset can be restored safely because it uses a controlled
field that works independently of GitHub light/dark theme. Its exact
production/accessibility validation remains a release asset gate.

## Runtime drift

No frozen runtime change is justified by this audit. The current deterministic
runtime preserves the main historical runtime decisions. Two exceptions need
tracking:

- **Numeric shortcuts** were implemented, reviewed, and fixed on preserved UX
  branches but are not in the sanitized/productized candidate. This is a real
  adoption loss requiring a later authorized runtime integration task.
- **Meeting adoption** is implemented only as per-run execution and experience
  evidence. The runtime does not automatically promote a completed Meeting
  decision into a typed, authoritative ledger and future context pack. This is
  the systemic defect behind the documentation drift.

## Safe changes applied

The reconciliation changes only documentation, decision data, schema, and
brand/product surfaces:

- restores the binding tagline and official category in the README hierarchy;
- retains coordination-layer and market-insight language at their correct
  layers;
- restores the compact workflow and proof row;
- documents Meeting semantics without changing runtime;
- installs the preserved human-approved Council app-icon SVG as the GitHub
  identity surface;
- separates identity colors from functional state colors;
- adds the Decision Ledger, provider adoption reports, adoption model, and
  bounded Human queue.

No source, test, provider logic, release candidate ref, frozen RC ref, or remote
state is modified.
