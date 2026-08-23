# 90-second Personal AI Manager demo

Maturity: **Alpha coordination slice**. This demo proves offline planning,
bounded builder/reviewer coordination, durable status, and reporting. It does
not prove personal memory, live-model quality, autonomous editing, or a finished
consumer UI.

## Deterministic assets

- input: `examples/personal-ai/personal-ai-manager.json`;
- expected plan: `docs/assets/demos/personal-ai-manager-plan.json`;
- normalized run evidence: `docs/assets/demos/personal-ai-manager-demo-output.txt`.

The fixture contains no personal data, credentials, network dependency, or
provider-enabled flag.

## Recording script

### 0–15 seconds — problem and boundary

Say: “I have a small private documentation task. I want a candidate plus an
independent review, but I do not want to choose or call a cloud model.”

Show the JSON fixture. Point to `privacy_requirement: high` and
`single_agent_reviewer`.

### 15–35 seconds — deterministic plan

Run:

```bash
flowfoundry team plan examples/personal-ai/personal-ai-manager.json
```

Show `mode: single_agent_reviewer`, `estimated_agent_calls: 2`, the write-scoped
builder, and the read-only reviewer. Compare the output with the committed
expected-plan asset.

### 35–65 seconds — offline execution

Run from a clean candidate checkout:

```bash
flowfoundry team run examples/personal-ai/personal-ai-manager.json \
  --run-id personal-ai-manager-demo
flowfoundry team report personal-ai-manager-demo
```

Show `status: completed`, completed tasks `build` and `review`, and
`human_actions_required: false`. Explain that the two provider-call counters
refer to deterministic fake-adapter invocations; the run records no real
provider execution and makes no network request.

### 65–82 seconds — evidence and control

Show the generated task-result paths and the empty commit list. Say: “The demo
preserves a reviewable run record but does not apply, merge, push, or publish a
change.”

### 82–90 seconds — honest limitation

Say: “This Alpha coordinates a bounded workflow. Personal preference memory,
live provider comparisons, and a polished personal-manager interface are still
planned.”

## Verification

The demo passes when:

- plan output exactly matches the committed deterministic plan fixture;
- the run and report commands exit zero with both tasks completed;
- `provider_executions` is empty and no real-provider flag is present;
- no tracked file changes after the run; and
- generated run state is removed after verification.
