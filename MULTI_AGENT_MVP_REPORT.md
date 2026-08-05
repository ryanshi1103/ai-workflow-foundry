# Multi-Agent Collaboration MVP Report

Date: 2026-08-05  
Status: implemented and offline-testable on `portfolio-migration`

## Delivered

- Agent Registry profiles for Codex Builder, DeepSeek Reviewer, Claude
  Architect, and Local Tester without credentials.
- Deterministic required/preferred capability matching with provider
  availability, roles, permission profiles, cost ordering, concurrency limits,
  and fallback agents.
- Rule-based Builder → Reviewer → Tester planning plus explicit JSON DAG plans.
- Parallel scheduling for independent ready tasks, bounded retry, dependency
  propagation, timeout metadata, and all required task/review states.
- A schema-versioned, atomic, lock-protected, redacted local run workspace with
  per-task contexts and an agent mailbox.
- Human gates that skip dangerous operations during overnight execution and
  persist the exact pending action.
- Stable reviewer protocol and deterministic result aggregation.
- Interrupted-run recovery, explicit failed-task retry, and input-hash
  reconciliation that preserves unchanged completed tasks.
- Additive `flowfoundry team run/status/resume/review/report/retry/approve`
  commands without changing legacy project, `cc`, or `aiproj` behavior.
- Public Codex Builder + DeepSeek Reviewer example that runs fully offline with
  fake providers.

## Offline test coverage

The orchestration suite covers registry fields, capability/permission/cost
matching, concurrency rejection and fallback, dependency planning, path
containment, private permissions, atomic redaction, concurrent mailbox writers,
approval skip and explicit approval, retry, approved/notes/blocked/pending
review decisions, dependency skipping, resume, changed-input reconciliation,
aggregation, CLI smoke paths, and synthetic end-to-end execution.

At implementation checkpoint, **31 orchestration tests passed**. Final repository
totals and clean-environment results are recorded in `FINAL_TEST_MATRIX.md` after
the complete migration validation.

## Safety posture

The default CLI never invokes a real provider. Real command execution requires
the explicit `--enable-real-provider` switch and still respects human approval
records. The runtime does not read `auth.json`, write credentials, commit run
state, push, deploy, release, or send external messages.

## Known limits and next engineering steps

- Add provider-native adapters with explicit process cancellation and structured
  streaming while preserving the current provider protocol.
- Provision real source worktrees/containers according to `workspace_mode`;
  current task contexts isolate orchestration state only.
- Add resource quotas and stronger process sandboxing before unattended real
  command execution.
- Evolve the rule planner behind the existing schema; keep offline tests free of
  model/network dependencies.
- Consider a signed schema migration strategy if the run format advances beyond
  version 1.

These are post-MVP refinements, not prerequisites for the local offline
collaboration workflow delivered here.

