# Meeting Decision Adoption Model

Status: read-path inheritance implemented; decision write-back remains design only

## Implemented read path

FlowFoundry now performs the smallest safe inheritance step before an ordinary
task or bounded Meeting reaches a provider:

```text
Task
  → deterministic task profile and declared scope
  → validate Decision Ledger
  → resolve exact domain / affected-surface / project-scope matches
  → inject ACTIVE PROJECT DECISIONS
  → emit warnings for occupied slots and unresolved relevant decisions
  → continue task or Meeting
```

The implementation is deliberately `READ → VALIDATE → SELECT → INJECT → WARN`.
It does not create, promote, approve, write, or supersede a decision. A run
persists one bounded `artifacts/decision-context.json`; Meetings copy that
validated section into `artifacts/meeting/context-pack.json` before Round 1.
The preserved artifact is reused on resume so participants in one Meeting do
not receive changing authority context between rounds.

## Finding

FlowFoundry has durable Meeting execution and read-path decision inheritance,
but it still does not have automatic durable decision adoption.

The runtime preserves Context Packs, independent contributions, conflicts,
targeted cross-review, convergence, dissent, budgets, receipts, and experience.
What it still does not do is convert a new convergence into a typed project
decision with authority, adoption tasks, verification, or automatic write-back.
Previously reconciled typed decisions now do receive deterministic future
context injection.

That gap explains the observed failure:

```text
Meeting completed
    ↓
result stored under one run
    ↓
later task reads current README/docs only
    ↓
new language occupies the same semantic slot
    ↓
old decision remains on disk but leaves the product surface
```

The brand decisions were not lost because evidence vanished. They were lost
because the next task had no mandatory adoption contract and no relevant-
decision context pack.

## Required lifecycle

```text
Meeting
  ↓
Participant contributions (provider-attributed)
  ↓
Conflict set and targeted resolution
  ↓
Final convergence + dissent
  ↓
Decision candidate
  ↓
Authority/Human Gate classification
  ↓
Decision Ledger entry
  ↓
Affected-surface map
  ↓
Adoption tasks
  ↓
Surface verification
  ↓
Future context pack selection
```

## Data contract

Every completed Meeting that proposes a durable decision should emit a
`decision_candidate` separate from the ordinary result:

```json
{
  "decision_id": "provisional-or-existing-id",
  "scope": ["brand", "github-hero"],
  "decision": "exact normalized decision",
  "authority_requested": "BINDING",
  "participants": ["codex", "deepseek"],
  "originating_contribution": {
    "provider": "deepseek",
    "round": 1,
    "claim": "你定目标，AI组队实现"
  },
  "conflicts": ["conflict-001"],
  "final_round": 2,
  "dissent": [],
  "human_gate_required": false,
  "affected_surfaces": ["README hero", "brand guide", "campus poster"],
  "verification": ["exact-copy scan", "hero-order check"]
}
```

The runtime must not infer `BINDING` merely because a Meeting completed. The
authority resolver applies explicit rules:

1. Human-approved decision;
2. Meeting explicitly authorized to bind this scope;
3. adopted brief or implementation decision;
4. advisory proposal;
5. open/conflicting item requiring Human review.

## Adoption states

Meeting completion and product adoption are different states:

| State | Meaning |
|---|---|
| `CONVERGED` | Participants reached a final position |
| `CLASSIFIED` | Authority is BINDING, ADOPTED, ADVISORY, OPEN, or superseded |
| `LEDGERED` | Typed ledger entry exists with evidence and provenance |
| `ADOPTION_PLANNED` | Affected surfaces and owners are recorded |
| `ADOPTED` | Required surfaces changed or explicitly exempted |
| `VERIFIED` | Current surfaces match and no higher authority conflicts |
| `SUPERSEDED` | Later higher-precedence decision links back explicitly |

A run report must never equate `CONVERGED` with `VERIFIED`.

## Decision Ledger read contract

Schema v2 records explicit `project_scope`, `affected_surface`,
`semantic_slot`, `semantic_value`, `supersedes`, and `superseded_by` fields.
The runtime does not parse the narrative `current_surface` field to infer
authority. It also does not infer authority from provider identity or from the
free-text `authority` field. Trusted runtime code recognizes only the status
policy below:

- inherited as authority: `BINDING`, `ADOPTED`;
- never inherited as authority: `ADVISORY`, `OPEN`, `SUPERSEDED`, `LOST`,
  `CONFLICTING`, `NEEDS_HUMAN_REVIEW`.

`ADVISORY` can be requested explicitly as non-authoritative historical
context. It remains separately labeled and cannot enter the active item list.

The validator fails closed for malformed/stale JSON, duplicate IDs, missing
authoritative text or evidence references, unsupported statuses/domains/
surfaces, unsafe paths, symlinked or oversized ledgers, broken reverse links,
supersession cycles, and two active `BINDING` decisions in one exclusive
project semantic slot.

## Relevant-decision context packs

Before a later task or Meeting begins, the deterministic selector queries
the ledger by:

- domain and affected surface;
- active status (`BINDING` and `ADOPTED` by default);
- project and product scope;
- supersession chain;
- explicit declared global scope, when present; and
- explicit semantic-slot proposals, when present.

Applicability is exact: matching domain, matching affected surface, or an
explicitly included global scope. The first version uses no LLM and performs
no fuzzy semantic classification. Goal keywords provide a deterministic
default, while task input may declare `decision_scope` with domains, affected
surfaces, project scopes, and proposed slot values.

The task Context Pack contains a bounded `ACTIVE PROJECT DECISIONS` section:

```text
BINDING
- Product category: Local-first Adaptive AI Team Runtime
- Tagline: One goal. The smallest sufficient AI team.

ADOPTED
- Current stage label: AI Coordination Layer

OPEN
- Exact plain-Chinese explanation
```

Each active item carries ID, status, domain, surface, semantic slot, exact
decision text, authority, supersession, and source. Exact decision text is
never paraphrased or partially truncated. When the byte/character budget is
reached, whole lower-priority items are omitted; the pack records an omission
count and the bounded subset of omitted IDs that fits.
The ledger and decision text are treated as untrusted structured data: they
cannot widen permissions, select tools, execute code, or authorize effects.

Relevant `OPEN` and `NEEDS_HUMAN_REVIEW` entries produce warnings rather than
instructions. A proposed value that differs from an active `BINDING` value in
the same explicit semantic slot produces `DECISION_CONFLICT_WARNING`. The
runtime preserves the proposal and existing value and makes no replacement.

## Surface verification

Each ledger item declares machine-checkable surfaces where practical:

- exact phrase present/absent;
- required semantic order;
- link target exists;
- asset hash and SVG validity;
- maturity label present;
- implementation symbol/test exists;
- release ref remains unchanged.

Verification should report drift, never rewrite surfaces automatically unless
the task has explicit write authority and the decision is BINDING/ADOPTED.

## Supersession

A later task cannot silently replace a decision. It must provide:

- the prior `decision_id`;
- higher or equal authority;
- exact scope being replaced;
- rationale and evidence;
- unchanged adjacent layers; and
- a `superseded_by` link in both directions.

This is how the Council Mark can validly supersede SYNTHESIS without erasing
the tagline, Chinese headline, or smallest-sufficient principle.

## Implemented now / not implemented

Implemented now:

1. validate `.flowfoundry/decision-ledger.json`;
2. select active decisions by requested domain/surface;
3. inject their exact IDs, statuses, decisions, and evidence refs into the
   next task's Context Pack;
4. emit a warning when a task proposes language for an occupied BINDING slot;
5. preserve supersession provenance and exclude superseded authority;
6. persist proof that applicable IDs were present before provider reasoning.

Not implemented:

- model-generated automatic decisions;
- automatic promotion to `BINDING` or `ADOPTED`;
- automatic Human Gate approval;
- automatic ledger mutation or supersession;
- autonomous semantic-slot replacement; or
- autonomous GitHub changes based on inferred decisions.

Write-back, adoption tasks, surface verification, and Human Gate UI remain a
separate future governance phase.
