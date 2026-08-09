# Multi-Agent Operator Guide

## Run the offline example

From the FlowFoundry repository root:

```bash
PYTHONPATH=src python3 -m flowfoundry team run \
  examples/orchestration/codex-builder-deepseek-reviewer.json
```

The default provider is deterministic and synthetic. It creates a private run
under `.flowfoundry/runs/`, routes the Builder, Reviewer, and Tester identities,
persists the review and result, and does not invoke Codex, DeepSeek, Claude, a
local model, the network, or an account.

Supply `--run-id NAME` for a predictable local ID and `--runs-root PATH` for an
isolated test/operator root.

## Preview the minimum path

Goal-only files are profiled before a run. Preview the task profile, routing
reason, and estimated Agent calls without creating run state or invoking a
provider:

```bash
flowfoundry team plan goal.json
```

Use `execution_mode` in a goal file only when an operator intentionally needs to
override `single_agent`, `single_agent_reviewer`, or `multi_agent`. Explicit
task arrays remain unchanged and bypass automatic team construction.

When the selected mode is `multi_agent`, the preview also includes the bounded
Meeting Plan: capability-shaped participants, validation tasks, maximum three
rounds, Agent-call limit, token limit, wall-time limit, and optional cost limit.
Meeting is never the default for simple work.

## Bounded Meeting behavior

Adaptive meetings create one reusable `artifacts/meeting/context-pack.json`.
Round 1 views are independent. If their structured positions agree, confidence
is sufficient, and no acceptance blocker exists, the runtime early-stops and
converges without cross-review. Otherwise it writes a small conflict pack and
invites only the affected participants to one targeted Round 2.

The final `final/meeting-result.json` includes the decision, rationale, evidence
references, confidence, validation requirements, recommended next action, and
any unresolved minority dissent. `final/meeting-experience.json` records calls,
rounds, conflict/cross-review counts, early-stop, usage, latency, budget status,
and validation outcome. The project-local ledger is ignored by Git.

Inspect provider setup without exposing credential values:

```bash
flowfoundry team providers
```

An unavailable runtime blocks only the task that needs it and creates
`provider-setup/<task-id>.json` plus a human action. Credential variable names
may be reported; their values are never stored in the run.

## Inspect, resume, and report

```bash
flowfoundry team status <run-id>
flowfoundry team review <run-id>
flowfoundry team report <run-id>
flowfoundry team resume <run-id>
flowfoundry team cancel <run-id>
```

`resume` changes an interrupted `running` task back to `pending`, preserves
completed tasks, and continues only ready work. `report` is deterministic and
can be regenerated from persisted state.

Meeting status is embedded in the run manifest, including current state,
participants, completed rounds, conflicts, budget consumption, dissent, and
result references. `cancel` durably stops a meeting before its next provider
call. It does not yet kill an already-running native provider subprocess.

To retry a task after investigating its failure:

```bash
flowfoundry team retry <run-id> <task-id>
flowfoundry team resume <run-id>
```

## Human approval

Push, force-push, protected-branch merge, deletion, repository rename,
deployment, release, external messaging, credential access, and high-risk shell
actions are human-gated. An overnight run marks the task
`skipped_pending_human`, writes an approval request and a local
`HUMAN_ACTIONS_REQUIRED.md`, then continues independent tasks.

After inspecting the exact task, inputs, intended command, rollback, and run
state, an operator can record a scoped approval:

```bash
flowfoundry team approve <run-id> <task-id> \
  --action release --actor <operator-id>
flowfoundry team retry <run-id> <task-id>
flowfoundry team resume <run-id>
```

Approval does not itself execute a task. The actor and exact granted action are
persisted. Never approve a broader action than the task requires.

## Real provider commands

Real command execution is disabled by default. `--enable-real-provider` is an
explicit MVP adapter switch and must be used only after reviewing the Agent
Registry command templates and task directory. FlowFoundry does not read
`auth.json` or discover provider credentials. Authentication, if required, must
already be configured through the provider's approved operator environment.

The current local-command seam is for controlled development, not unattended
production use. Prefer the offline provider for CI and examples.

Real runs use the current directory as their shared project workspace. Supply
`--workspace PATH` to select another project explicitly. Real provider tasks are
currently serialized because worktree isolation is not yet implemented.

Codex and Claude-compatible adapters request a structured result envelope.
DeepSeek reuses the workspace manager's isolated Claude-compatible runtime.
Token and cost fields are aggregated when the CLI reports them; otherwise the
report says `unavailable` rather than estimating unsupported numbers.

## Task file

A task file may contain only `{ "goal": "..." }` to use the rule planner, or a
full schema-versioned plan. Full tasks declare IDs in dependency order. See
`examples/orchestration/codex-builder-deepseek-reviewer.json` for the portable
format.

## Recovery checklist

1. Inspect `manifest.json` and the exact task result/review.
2. Run `team status` and `team review` before retrying.
3. Confirm no completed task's input changed unexpectedly.
4. Resolve a `BLOCKED` review rather than bypassing it.
5. Record human approval only for a reviewed hazardous action.
6. Run `team resume`, then regenerate `team report`.

For meetings, also inspect `meeting.state`, `budget_status`, conflict packs, and
the final dissent list. A `budget_exhausted` run is intentionally partial and
must not be treated as a successful decision.

Run directories contain task inputs and operational metadata. Keep them local,
back them up according to project policy if needed, and never commit them.
