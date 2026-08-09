# Multi-Agent Collaboration Architecture

## Scope

The FlowFoundry Multi-Agent MVP coordinates bounded local tasks. It does not
create an unconstrained autonomous conversation loop and it does not make real
provider calls by default. The durable unit is a run manifest plus individually
addressable task state, messages, reviews, approvals, artifacts, and reports.

```mermaid
flowchart LR
    G[User goal or task file] --> I[Task profile + minimum path]
    I --> P[Rule-based planner]
    P --> Q{Minimum sufficient path}
    Q -->|single / review| DAG[Dependency DAG]
    Q -->|multi_agent| MP[Bounded Meeting Plan]
    MP --> C[Single Context Pack]
    C --> R1[Independent Round 1]
    R1 --> F{Deterministic conflict check}
    F -->|none| E[Early convergence]
    F -->|conflict| R2[Targeted Cross Review]
    R2 --> E
    E --> Z[Decision + dissent + validation]
    DAG --> R[Capability router]
    R --> S[Bounded scheduler]
    S --> B[Builder task context]
    S --> V[Reviewer task context]
    S --> T[Tester task context]
    B --> M[Atomic mailbox]
    V --> M
    T --> M
    V --> D{Review decision}
    D -->|APPROVED / WITH_NOTES| A[Result aggregator]
    D -->|BLOCKED| X[Block source and dependents]
    D -->|REVIEW_PENDING| W[Persist and resume later]
    S --> H{Human approval gate}
    H -->|hazard| Q[skip_pending_human]
    Q --> A
    M --> A
```

## Modules and responsibility

| Module | Responsibility |
|---|---|
| `models` | Versionable Agent, Task, Plan, ProviderResult, status, risk, and review vocabulary |
| `intelligence` | No-model task profile and single / reviewed / team path selection |
| `registry` | Agent metadata, capability/permission matching, role preference, history, cost preference, fallback, and concurrency limits |
| `planner` | Adaptive bounded plans and explicit JSON DAG loading |
| `router` | Deterministic task-to-agent selection |
| `providers` | Fake/dry, deterministic local command, Codex, and Claude-compatible structured seams |
| `discovery` / `provider_setup` | Runtime/auth-state inspection and on-demand setup artifacts without credential values |
| `workspace` | Contained run paths, schema version, 0700 directories, 0600 atomic redacted files, and manifest locking |
| `mailbox` | Locked, ordered, schema-versioned agent messages |
| `approvals` / `policies` | Default human gates for dangerous action classes |
| `scheduler` | Dependency readiness, parallel independent tasks, per-agent concurrency, retry, review transitions, and skip propagation |
| `meeting` | Durable states, one bounded context pack, independent views, zero-model conflict rules, selective cross-review, convergence, budgets, cancellation, and resume receipts |
| `evaluator` | `APPROVED`, `APPROVED_WITH_NOTES`, `BLOCKED`, and `REVIEW_PENDING` record protocol |
| `recovery` | Interrupted-state repair, explicit retry, and input-hash reconciliation |
| `aggregator` | Completed/unfinished tasks, tests, risks, human actions, generated files, commits, and next step |
| `memory` | Minimum-sample agent/category success, retry, latency, token, cost, and review statistics |
| `cli` | Additive `flowfoundry team` interface; existing project/cc/aiproj behavior is unchanged |

## Agent registry

Every agent declares an ID, display name, provider/model/mode, role hint,
capabilities, tools, ability hints, command template, cost class, concurrency
limit, permission profile, context/privacy/locality metadata, availability,
authentication state, reliability/quota fields, workspace mode, and enabled
flag. The bundled examples
are `codex-builder`, `deepseek-reviewer`, `claude-architect`, and
`local-tester`.

Capabilities and permissions are hard requirements; role is a preference, not a
provider lock. Real agents are unavailable by default. Offline runs create an in-memory
synthetic view of the registry and route the same identities through the fake
provider. This tests routing without implying that a provider account or binary
is configured.

## Planning and scheduling

Task plans are dependency ordered and schema-versioned. Each task includes its
dependencies, role, required/preferred capabilities, inputs, expected outputs,
risk, approval requirements, validation commands, retry bound, timeout metadata,
and optional fallback agent. Explicit plans may include independent tasks; the
scheduler executes ready tasks in parallel while a semaphore enforces each
agent's concurrency limit.

A generated plan is selected from:

```text
simple:       build → aggregate
risk/quality: build → review → aggregate
complex:      bounded meeting → [validation] → aggregate
```

Adaptive `multi_agent` plans carry a `MeetingPlan`; explicit legacy JSON DAGs
without one keep their existing execution semantics. Participant tasks describe
required capabilities, while the Registry chooses the actual Agent. Providers
are not hard-coded to roles.

The meeting state machine is:

```text
PLANNED → CONTEXT_READY → ROUND1_RUNNING → ROUND1_COMPLETE
        → CONFLICT_CHECKED → [ROUND2_RUNNING → ROUND2_COMPLETE]
        → CONVERGING → [VALIDATING] → COMPLETED
```

`BLOCKED`, `FAILED`, `CANCELLED`, and `BUDGET_EXHAUSTED` are terminal exits.
Transitions are validated and persisted. Round 1 participants receive the same
addressable Context Pack and cannot see peer outputs. Structured position,
confidence, reasons, risk, assumptions, blockers, and evidence drive a
deterministic conflict check without another model call.

No conflict means immediate convergence. A conflict creates one bounded pack
and calls only affected participants for a single cross-review; there is no
free-form Round 3 debate. Convergence may preserve minority dissent. The plan
owns hard round, Agent-call, token, wall-time, and optional cost budgets.
Unknown usage remains unavailable rather than becoming zero.

`REVIEW_PENDING` stops dependents without discarding state. `BLOCKED` blocks the
reviewed source and skips tasks that depend on it. A retry never exceeds the
task's declared limit.

## Durable run layout

```text
.flowfoundry/runs/<run-id>/
├── manifest.json
├── tasks/<task-id>/{task.json,result.json}
├── artifacts/
│   └── meeting/{context-pack.json,conflicts/,calls/,round2/}
├── messages/
├── reviews/
├── logs/
├── approvals/
├── provider-setup/
├── final/{meeting-result.json,meeting-experience.json,report.json,report.md}
└── HUMAN_ACTIONS_REQUIRED.md  # only when a gate is encountered
```

The run root is ignored by Git. Writes use same-directory temporary files,
`fsync`, and atomic replacement. Manifest and mailbox updates are lock-protected.
IDs and all resolved paths are contained below the configured root. Per-call
receipts make accounting idempotent and let Round 1 or Round 2 resume without
repeating completed calls. Meeting summaries are upserted into a project-local
experience ledger, and small usefulness counters extend Agent Performance
Memory.

## Extension boundary

The provider protocol is intentionally small: execute one structured task
against a persisted project root, retain private metadata in its task directory,
and return a serializable result. Native commands remain explicit opt-in. Real
tasks are serialized until worktree isolation exists. Future adapters can add
streaming, provider-process termination, and worktree/container provisioning
without changing task, review, mailbox, or report schemas. `team cancel`
prevents the next meeting call; it does not yet terminate an already-running
native provider process.
