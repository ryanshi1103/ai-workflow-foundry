# Demo 1 — Personal AI Manager

**Maturity:** Alpha coordination slice. Goal profiling, minimum-path selection,
offline execution, review, usage records, and recovery exist. Personal semantic
memory and adaptive long-term preference learning do not.

## Problem

A person uses several AI tools but should not need to decide manually which one
to call, how much context to disclose, whether a reviewer is justified, or how
to preserve evidence after the task.

This demo asks FlowFoundry to coordinate a small, privacy-sensitive README
improvement without a real provider or network call.

## Input

The versioned synthetic input is
`examples/personal-ai/personal-ai-manager.json`:

```json
{
  "goal": "Review one project README locally and propose one clearer sentence. Preserve the original, use no real provider or network, and require an independent review before presenting the result.",
  "execution_mode": "single_agent_reviewer",
  "task_profile": {
    "privacy_requirement": "high"
  }
}
```

No user profile, personal document, credential, or historical transcript is
required.

## Workflow

```mermaid
flowchart LR
    G[Human goal and constraints] --> P[Deterministic task profile]
    P --> D[Minimum-path decision]
    D --> B[Bounded builder candidate]
    B --> R[Independent review]
    R --> O[Result and usage report]
    O --> H[Human decides next action]
```

Preview the plan without creating run state:

```bash
flowfoundry team plan examples/personal-ai/personal-ai-manager.json
```

Run the synthetic lifecycle without a network or billed model call:

```bash
flowfoundry team run examples/personal-ai/personal-ai-manager.json \
  --run-id personal-ai-manager-demo
```

Do not add `--enable-real-provider` to the official offline demo.

## Agent coordination

- The rule-based analyzer records task type, privacy requirement, and expected
  execution path without a model call.
- The operator explicitly requests `single_agent_reviewer`, so the planner
  creates a bounded builder and an independent reviewer.
- Offline mode uses synthetic registry readiness and the fake provider. Provider
  names in the record are identities used to exercise routing, not evidence
  that those cloud services were called.
- The builder has a write-capable task declaration; the reviewer is read-only.
- A human receives the result and remains responsible for accepting or applying
  any change.

## Output

The plan command emits JSON containing:

- the analyzed task profile;
- routing decision and reason;
- expected provider-call count;
- two bounded tasks with capabilities, permissions, and dependencies.

The run command creates a local run record with task states, synthetic outputs,
review state, usage fields, and a final report. The official demo should show
that provider calls are fake/offline and that no main-worktree change occurred.

## Limitations

- This is not a complete personal AI manager UI.
- It does not remember the person's writing preferences across sessions.
- It does not retrieve a personal knowledge base or infer private context.
- It does not compare live model quality, price, or latency.
- Fake-provider output demonstrates orchestration state, not content quality.
- Applying a proposed edit, merging, pushing, or publishing remains a separate
  human-authorized action.

## Release verification

- [ ] Plan output matches the documented two-task path.
- [ ] Run completes with zero real-provider and network calls.
- [ ] No credentials, personal paths, or private content enter the run record.
- [ ] Output clearly labels synthetic provider usage.
- [ ] Main working tree is unchanged.
- [ ] Recording includes limitations and a human decision frame.

