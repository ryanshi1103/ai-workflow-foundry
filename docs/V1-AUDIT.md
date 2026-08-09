# FlowFoundry v1 Repository Audit

Audit date: 2026-08-10
Source of truth: branch `portfolio-migration`, HEAD
`8285a60c54c3b2dfb30b1092aa82322d00273574`, executable code, and tests.

## Current State

The repository already contained substantially more than the older project
state described. It had a resumable orchestration MVP with a capability
registry, DAG planner, deterministic router, parallel scheduler, atomic local
mailbox, review protocol, approval gate, result aggregation, retry/resume, and
an offline provider. It also contained the integrated workspace manager and
compatible `cc`/`aiproj` entry points.

The audit-start worktree was not clean. A `.gitignore` addition for
`.flowfoundry/agent-performance.json` and multiple owner reports were already
present. They were preserved. No private session content or Codex auth file was
read.

Executable discovery at audit time found Codex and Claude. DeepSeek is provided
through the workspace manager's isolated Claude-compatible configuration, not
through a separate `deepseek` command. Authentication was deliberately not
probed with a billed or network call.

## Capability Map

| Area | State | Repository fact and v1 boundary |
|---|---|---|
| Runtime | PARTIAL | `cc` compatibility and explicit native CLI seam exist; live provider calls remain unverified |
| Workspace | EXISTS | project root, Git context, private run state, artifacts, logs, outputs, and recovery state are local and shared |
| Registry | PARTIAL | rich static metadata and runtime discovery exist; external plugin-file loading and quota probes do not |
| Router | PARTIAL | capabilities, permissions, availability, role preference, cost class, and mature history are used; no full price/latency optimizer |
| Planner / DAG | EXISTS | explicit schema plus adaptive minimum-path plans and dependency validation |
| Team | EXISTS | bounded offline teams execute and recover; real shared writers are intentionally serialized |
| Meeting | EXISTS | adaptive multi-agent plans use one bounded Context Pack, independent structured views, deterministic conflict detection, early stop, one selective cross-review, convergence with dissent, hard budgets, call receipts, validation, cancellation, and experience records |
| Messaging | PARTIAL | atomic mailbox and bounded dependency artifacts exist; providers do not yet consume a general inbox protocol |
| Executor | PARTIAL | fake, deterministic command, Codex, and Claude-compatible structured seams exist; no process cancellation or container quotas |
| Reviewer | EXISTS | stable decisions, persisted findings, source blocking, and dependent propagation |
| Human Approval | EXISTS | hazardous action classes create scoped, persisted gates |
| Cost | PARTIAL | calls, token fields, latency, and cost are aggregated without inventing unavailable values; provider pricing is not configured |
| Memory | EXISTS | simple per-agent/category success, retry, latency, token, cost, and review statistics; no ML |
| Recovery | EXISTS | interrupted repair, input reconciliation, bounded retry, approval retry chain, and resume |
| Provider Setup | PARTIAL | executable/auth-state discovery and on-demand setup artifacts exist; automated install/login is not implemented |
| CLI | EXISTS | catalog, workflow, project, adaptive plan, provider status, team run/status/review/report/retry/resume/cancel/approve |

## Duplicate and compatibility findings

- `src/ai_project_manager` and `aiproj` are compatibility surfaces, not a second
  workspace implementation. Keep them while compatibility is inexpensive.
- `core/workspace-manager/bin/cc` is a public wrapper over the integrated Python
  runtime. It should not be rewritten independently; source changes belong in
  the repository runtime and deploy through the existing script.
- `capability_registry.py` describes workflow-component capabilities, while
  `orchestration/registry.py` describes runnable agents. Their similar names do
  not make them interchangeable.
- Historical migration, release, and incident reports are evidence, not current
  runtime truth. They should not override Git, code, tests, or this verified
  state.

## Gap Analysis and Minimum Path

The audit-start P0 was that every goal used Builder → Reviewer → Tester even
when one Agent was sufficient. The implemented shortest path was:

1. Add a no-model task profile and explainable execution-mode decision.
2. Persist that decision and expose a no-side-effect `team plan` preview.
3. Record real call/token/latency/cost fields, leaving unknown data unknown.
4. Discover provider/runtime state and persist setup requirements only when a
   task actually needs an unavailable provider.
5. Bind real commands to one persisted project workspace and serialize real
   writers until worktree isolation exists.
6. Reuse native Codex and Claude-compatible structured-output features and pass
   bounded dependency artifacts instead of repeated full context.
7. Make capabilities the routing gate and roles a preference rather than a
   provider lock.
8. Feed simple, minimum-sample performance history back into routing.

## Highest-value next actions

1. Add provider-native process termination so `team cancel` can interrupt an
   already-running real provider command, not only prevent the next call.
2. Add project-local registry configuration and adapter entry points so a new
   OpenAI-compatible or local provider does not require core edits.
3. Validate native adapters with operator-approved, capped-cost smoke calls;
   until then their live auth/model status is `unverified`.
4. Add worktree provisioning before enabling parallel real writers.

Local-model hardware discovery, dashboard work, and broad provider coverage are
deferred until this v1 path is proven with real bounded tasks.

## Validation

- FlowFoundry foundation: 125 tests passed.
- Workspace manager runtime: 66 tests passed.
- Confera Media Skills contracts: 3 tests passed.
- Print-ready Nameplate Generator: 3 tests passed.
- Catalog validation: 5 components, 3 workflow contracts, 17 capabilities.
- Python compilation and `git diff --check`: passed.
- Ruff was not installed in the active environment, so a Ruff invocation could
  not be completed locally.
