# Personal AI Manager — 90-second launch demo

Maturity: **Alpha coordination slice**.

This is the launch recording script. The detailed reproducibility contract and
expected evidence remain in
[the verified demo guide](demos/personal-ai-manager-demo.md).

## Recording contract

- Record from a disposable clean checkout of the exact approved release tag.
- Use `examples/personal-ai/personal-ai-manager.json` unchanged.
- Keep real-provider execution disabled and network access unnecessary.
- Show the full command and relevant output; do not hide errors with edits.
- Add captions and a transcript. Keep terminal text readable at the published
  resolution.
- Do not show credentials, personal paths, usernames, private repositories,
  notifications, shell history, or unrelated files.
- Do not imply that fake-adapter text measures live-model quality.

## Pre-record setup

From the disposable checkout:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install .
flowfoundry validate
```

Prepare three terminal tabs before recording:

1. the synthetic JSON fixture;
2. a terminal at the repository root; and
3. the normalized expected evidence in
   `docs/assets/demos/personal-ai-manager-demo-output.txt`.

Run once off-camera to confirm the exact tagged checkout passes. Start the
recording from a fresh disposable checkout so the fixed run ID does not collide
with earlier state.

## Timed script

### 0–12 seconds — the problem

**On screen:** FlowFoundry README title, then the fixture goal.

**Say:**

> AI work needs more than a prompt. I want one documentation change, independent
> review, no cloud call, and an inspectable result before anything is applied.

### 12–27 seconds — explicit constraints

**On screen:** `examples/personal-ai/personal-ai-manager.json`. Highlight
`privacy_requirement: high` and `single_agent_reviewer`.

**Say:**

> This fixture is synthetic. It marks privacy as high and explicitly asks for a
> builder plus reviewer. There is no credential, personal data, or real-provider
> flag.

### 27–43 seconds — minimum sufficient plan

**Run:**

```bash
flowfoundry team plan examples/personal-ai/personal-ai-manager.json
```

**On screen:** `mode: single_agent_reviewer`, `estimated_agent_calls: 2`, the
builder permissions, and the reviewer's read-only permissions.

**Say:**

> FlowFoundry chooses the requested two-step path. The builder is scoped to read
> and write; the independent reviewer can only read. The plan is
> deterministic and creates no run state.

### 43–70 seconds — offline execution and report

**Run:**

```bash
flowfoundry team run examples/personal-ai/personal-ai-manager.json \
  --run-id personal-ai-manager-demo
flowfoundry team report personal-ai-manager-demo
```

**On screen:** `status: completed`, completed tasks `build` and `review`, and
`human_actions_required: false`.

**Say:**

> Now both roles execute through deterministic fake adapters. The report shows a
> completed build and review. The two estimated calls are fixture invocations,
> not cloud requests or billed model calls.

### 70–82 seconds — evidence and human control

**On screen:** task-result paths, `provider executions: none`, and `commits:
none` in the normalized evidence.

**Say:**

> The run preserves task results and a reviewable record. It makes no commit and
> does not merge, push, publish, or change the main working tree.

### 82–90 seconds — honest close

**On screen:** Current Status link and repository URL.

**Say:**

> This Alpha proves bounded coordination—not personal memory or full provider
> parity. Try the offline path and test the controls.

## Acceptance check

The recording is publishable only when:

- its visible tag and commit match the approved release;
- the plan matches `docs/assets/demos/personal-ai-manager-plan.json`;
- both tasks complete and `provider_executions` remains empty;
- the recording contains no jump that hides a command failure;
- captions and transcript match the spoken wording;
- no private or machine-local information is visible; and
- a second reviewer confirms every capability and limitation claim.
