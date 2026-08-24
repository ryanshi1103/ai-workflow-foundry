# GitHub Release Assistant — 90-second Alpha demo

Maturity: **Alpha coordination demo**
Execution mode: deterministic fake providers
Network/provider cost: none
Release side effects: none

## Human problem

> “Prepare my GitHub release.”

Without a coordinator, a developer switches among code, test, documentation,
security, and release tools, then manually decides whether the evidence is good
enough to act. A release is not one model prompt.

FlowFoundry makes that coordination visible: one goal becomes a bounded task
graph, suitable roles receive each stage, evidence is persisted, and the run
stops before an approval-controlled action.

This demo exercises those coordination mechanics through the current runtime.
It does not claim that FlowFoundry already performs a complete repository audit,
runs the declared project test suite, builds wheel/sdist artifacts, writes
release notes into the project, pushes, tags, deploys, or publishes.

## Exact fixture

The demo uses:

`examples/personal-ai/github-release-assistant.json`

The fixture is an explicit task graph. FlowFoundry validates and executes that
graph; it does not pretend the natural-language sentence alone generated a
complete release workflow.

## Actual agent assignments

| Task | Routed identity | Current demo behavior |
|---|---|---|
| Analyze declared release context | Claude Architect | Fake-provider planning result; no cloud call |
| Prepare code-verification candidate | Codex Builder | Fake-provider candidate; no code is changed |
| Review security/release evidence | DeepSeek Reviewer | Fake-provider structured review; read-only role |
| Record test stage | Local Tester | Fake-provider test-stage record; project tests are not executed |
| Prepare evidence package | Codex Builder | Stops pending the built-in `release` approval class |

These are registry routing identities. The demo does not compare live model
quality or imply that provider credentials are configured.

## Before recording

Use a fresh approved checkout. Confirm the exact SHA and clean status without
showing private paths or unrelated terminal history:

```bash
git rev-parse HEAD
git status --short
```

Install and validate using the release's approved installation instructions.
Then inspect provider identities without exposing credential values:

```bash
flowfoundry validate
flowfoundry team providers
```

The provider status command reports readiness and credential-source names, not
credential values. Do not enable `--enable-real-provider` for this demo.

## 90-second public story

### 0–15 seconds — the problem

Show the release checklist—code, review, tests, evidence, and publication
authority—and say:

> Preparing a release means coordinating several tools and decisions. Today I
> have to carry the context, verify the evidence, and remember where human
> approval is required.

Do not begin with the architecture or provider registry.

### 15–30 seconds — one goal

Show the fixture goal:

> Prepare a reviewable GitHub release evidence package. Do not push, tag,
> deploy, publish, or enable a real provider.

Then run:

```bash
flowfoundry team plan examples/personal-ai/github-release-assistant.json
```

Show the five-task dependency path and the high-risk approval requirement on
`package`. Explain that this is a validated explicit plan, not an AI-generated
repository audit.

### 30–60 seconds — coordinate the AI team

Run:

```bash
flowfoundry team run \
  examples/personal-ai/github-release-assistant.json \
  --run-id github-release-assistant
```

Show that the first four tasks complete through deterministic fake-provider
execution and that `package` becomes `skipped_pending_human`.

Say:

> Claude Architect receives the planning task, Codex Builder the code-oriented
> candidate, DeepSeek Reviewer the security review, and Local Tester the test
> stage. FlowFoundry preserves the dependencies and review boundary. These are
> offline routing identities; no provider was called.

### 60–82 seconds — evidence and approval

Run:

```bash
flowfoundry team status github-release-assistant
flowfoundry team review github-release-assistant
flowfoundry team report github-release-assistant
```

Show task states, routed agent IDs, the persisted review decision, usage fields,
and the pending human action. The contained run directory is the demo's evidence
bundle. It is not a distributable release package.

Show the pending `package` task. Display the exact approval command, but do not
run it in the public demo:

```bash
flowfoundry team approve github-release-assistant package \
  --action release \
  --actor YOUR_NAME
```

The command records one scoped approval. It does not authorize push, tag,
deployment, publication, or a real provider.

### 82–90 seconds — human remains in control

End before approval and say:

> FlowFoundry coordinated the work, preserved the evidence, and stopped at the
> human boundary. The system can recommend and prepare; I still authorize the
> consequential action.

On screen, retain the limitation: real tests, current-SHA artifacts,
independent review, and separately authorized publication are still required.

## Optional approval-mechanism verification

Outside the 90-second public recording, the operator may verify the existing
approval/retry/resume lifecycle:

```bash
flowfoundry team approve github-release-assistant package \
  --action release \
  --actor YOUR_NAME
flowfoundry team retry github-release-assistant package
flowfoundry team resume github-release-assistant
flowfoundry team report github-release-assistant
```

The resulting `package` output is synthetic fake-provider output. It proves the
durable approval lifecycle, not release-package quality.

## Evidence checklist

The demo passes only when:

- the exact committed fixture is used;
- real-provider execution remains disabled;
- `analyze` routes to `claude-architect`;
- `code` routes to `codex-builder`;
- `analysis` routes to `deepseek-reviewer`;
- `test` routes to `local-tester`;
- `package` stops as `skipped_pending_human` before approval;
- the review decision is persisted;
- no tracked project file changes;
- no push, tag, deploy, publication, or financial action occurs; and
- the recording calls the output a synthetic coordination/evidence bundle, not
  a finished GitHub release.

## Known limitations

- Project state is supplied by the user/fixture; semantic repository analysis is
  not performed by this offline demo.
- Fake-provider completion does not run the project's actual test commands.
- The mobile approval card is designed but not implemented; the current
  approval surface is CLI and persisted JSON state.
- Claude, Codex, and DeepSeek labels identify routed roles, not live calls.
- Release notes and binary/source artifacts require separate real tooling and
  current-SHA verification.
