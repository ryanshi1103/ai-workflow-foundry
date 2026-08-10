# Real Provider Smoke Report

Verified on 2026-08-10 against the `portfolio-migration` branch, starting from
`b00f0019222ee4fb3bb25bead7202d95d6c0f1bc`. No credential file or secret value
was read or recorded.

## Outcome

The controlled smoke reached its hard limit of four real Provider attempts and
then stopped. A Codex writer completed a one-line Python fix in a
FlowFoundry-owned managed worktree. FlowFoundry independently ran the declared
unit test and `git diff --check` in that exact candidate; both exited zero. The
fixture's main worktree retained its original committed source. A
DeepSeek-compatible read-only reviewer independently returned `APPROVED` from
the bounded task, diff, validation, and primary result.

Live Meeting, live cancellation, direct Claude, and Grok validation were
deferred. The deterministic cancellation suite remains the authoritative
coverage for physical cancellation.

## Provider discovery and calls

| Provider path | Runtime | Discovery | Live result |
|---|---|---|---|
| Codex | `codex-cli 0.147.0` | installed, auth initially unverified | live auth/model verified; writer completed |
| DeepSeek-compatible | Claude Code `2.1.224` with isolated DeepSeek configuration | installed, auth initially unverified | live auth/model verified; reviewer approved |
| Claude | Claude Code `2.1.224` | installed, auth unverified | not directly called |
| Grok | no registered Provider | unavailable | deferred without adapter work |

| Call | Purpose | Result | Latency | Usage |
|---:|---|---|---:|---|
| 1 | Codex writer | rejected invalid strict JSON schema | 12,119 ms | tokens/cost unavailable |
| 2 | Codex writer after schema fix | structured result and isolated one-file diff | 62,602 ms | tokens/cost unavailable |
| 3 | DeepSeek-compatible review | `APPROVED` | 97,132 ms | 31,640 input, 2,429 output, USD 0.466533 |
| 4 | required writer rerun after validator fix | completed with two independent validators | 52,773 ms | tokens/cost unavailable |

Total locally observed Provider latency was 224,626 ms. Total token and cost
accounting is incomplete because Codex did not expose usage; unknown values
remain unavailable rather than being converted to zero. The measured subset is
34,069 tokens and USD 0.466533.

All four task plans used `retry_limit=0`. Calls 2 and 4 were explicit,
operator-visible same-smoke reruns after a diagnosed adapter/runtime defect,
not hidden scheduler retries.

## Track A evidence

- Strategy: `single_agent`.
- Base: one clean commit containing `calculator.py` and one `unittest`.
- Candidate: one tracked file changed, replacing subtraction with addition.
- Isolation: Provider cwd was the managed worktree; candidate base SHA, branch,
  status, diff stat, patch artifact, and lease were persisted.
- Validation: `python -m unittest -q` exited 0 with one test; `git diff
  --check` exited 0. Both command receipts were stored on the candidate.
- Main integrity: the fixture main worktree still contained `return a - b`.
- Result: `completed`; candidate retained dirty until disposable-fixture
  teardown, with no merge, commit, push, or PR.
- Experience: marked `execution_kind=real`, Provider `codex`, strategy,
  isolation, attempts, changed-file count, and validation.

## Track B evidence

The reviewer received only the task, acceptance criteria, base reference,
one-line candidate diff, deterministic validation result, and primary
structured result. It used read-only isolation, made no file change, returned a
schema-compliant `APPROVED` decision, and persisted measured usage and cost.

## Compatibility findings and fixes

### Codex strict output schema

- Observation: the first live call returned `invalid_json_schema`; every object
  in Codex structured output must be closed with
  `additionalProperties: false`, with all properties explicitly required.
- Root cause: the shared Provider schema allowed an unconstrained `outputs`
  object and omitted nullable properties from required lists.
- Fix: close all response objects and use a small generic details/artifact
  envelope with explicit nullable Meeting fields.
- Regression: the adapter test recursively verifies strict object closure and
  complete required-property lists.

### Candidate validation hierarchy

- Observation: the first successful writer run was marked completed while its
  persisted validation object was empty.
- Root cause: validation commands were reported and handed off to explicit
  tester tasks, but a single-writer plan did not execute them independently.
- Fix: after releasing the writer lease, run declared commands as parsed argv
  without a shell in the same candidate worktree, bound output, persist exit
  codes, and let validation failure override Provider success.
- Regression: candidate-cwd success and provider-success/validator-failure
  cases are both covered.

### Mock versus real memory

- Observation: performance memory had no execution-kind dimension.
- Root cause: offline and live runs shared aggregate agent counters.
- Fix: record `mock` and `real` buckets and select only the matching bucket for
  reliability routing, retaining the minimum-sample threshold.
- Regression: three mock failures cannot change a real-only score.

### Claude-compatible result envelope

The DeepSeek-compatible CLI returned the structured payload and measured usage
in its stdout JSON wrapper instead of a Codex-style last-message file. The
existing common parser handled this correctly; no Provider-specific workaround
was added.

### Cross-run worktree observability

- Observation: a status report for the final rerun described the earlier
  retained candidate as an unowned orphan because leases were looked up only
  inside the current run.
- Root cause: managed worktrees are repository-scoped while durable lease files
  are run-scoped.
- Fix: status safely recognizes validated FlowFoundry ownership records across
  sibling runs without taking them over; dirty candidates also report retained
  consistently.
- Regression: one run no longer claims another run's owned dirty candidate.

## Idempotency and safety

Repeated terminal `status`, `report`, and real-enabled `resume` left attempts at
one and execution receipt count unchanged. No additional Provider call,
Experience record, or candidate artifact was created. Discovery and reporting
did not expose credentials. The FlowFoundry repository's pre-existing
`.gitignore` edit, untracked reports, and user-created worktree were not
modified, staged, cleaned, or removed.

## Deferred coverage

- Live cancellation was not attempted after the call budget was consumed; the
  11 deterministic native cancellation tests pass.
- A live two-participant Meeting required more remaining calls and was
  deferred.
- Direct Claude and Grok/External Intelligence were not called.
- Codex token/cost fields remain unavailable in this CLI path.
