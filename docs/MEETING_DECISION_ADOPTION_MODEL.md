# Meeting Decision Adoption Model

Status: design only; no frozen runtime change in this reconciliation

## Finding

FlowFoundry currently has durable Meeting execution, not durable decision
adoption.

The runtime preserves Context Packs, independent contributions, conflicts,
targeted cross-review, convergence, dissent, budgets, receipts, and experience.
What it does not do is convert an accepted convergence into a typed project
decision with authority, affected surfaces, adoption tasks, verification, and
automatic future context injection.

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

## Relevant-decision context packs

Before a later task or Meeting begins, a deterministic selector should query
the ledger by:

- domain and affected surface;
- active status (`BINDING` and `ADOPTED` by default);
- project and product scope;
- supersession chain;
- freshness/current implementation state; and
- explicit user exclusions.

The task Context Pack should include a small `prior_decisions` section:

```text
BINDING
- Product category: Local-first Adaptive AI Team Runtime
- Tagline: One goal. The smallest sufficient AI team.

ADOPTED
- Current stage label: AI Coordination Layer

OPEN
- Exact plain-Chinese explanation
```

Advisory material should be opt-in by relevance. Superseded decisions should
appear only when provenance or conflict analysis requires them. This keeps
context bounded without forgetting authority.

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

## Minimal future implementation

The smallest low-risk implementation after release is a read-only context-pack
step, not automatic mutation:

1. validate `.flowfoundry/decision-ledger.json`;
2. select active decisions by requested domain/surface;
3. inject their exact IDs, statuses, decisions, and evidence refs into the
   next task's Context Pack;
4. emit a warning when a task proposes language for an occupied BINDING slot;
5. require an explicit supersession record before verification can pass.

Write-back, automatic adoption tasks, and Human Gate UI can follow after the
read-only selector proves useful. This reconciliation intentionally does not
alter the frozen runtime.
