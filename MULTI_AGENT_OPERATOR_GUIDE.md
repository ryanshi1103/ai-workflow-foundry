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

## Inspect, resume, and report

```bash
flowfoundry team status <run-id>
flowfoundry team review <run-id>
flowfoundry team report <run-id>
flowfoundry team resume <run-id>
```

`resume` changes an interrupted `running` task back to `pending`, preserves
completed tasks, and continues only ready work. `report` is deterministic and
can be regenerated from persisted state.

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

Run directories contain task inputs and operational metadata. Keep them local,
back them up according to project policy if needed, and never commit them.

