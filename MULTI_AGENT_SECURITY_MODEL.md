# Multi-Agent Security Model

## Trust boundaries

The model/provider is an untrusted candidate producer. FlowFoundry owns routing,
path containment, state transitions, retries, persistence, redaction, approvals,
and aggregation. A reviewer is independent evidence, not permission to perform a
hazardous external action.

```text
untrusted task/model output
          |
          v
validated task/result schema
          |
          v
contained local run workspace
          |
          v
review decision ----> human action gate ----> explicitly enabled side effect
```

## Default controls

- Real providers are unavailable and disabled in the registry by default.
- CLI runs use a deterministic fake provider unless explicitly enabled.
- No adapter reads `~/.codex/auth.json` or searches for credentials.
- Run and task identifiers reject traversal characters; resolved paths cannot
  escape the configured run root.
- Run directories are mode 0700 and persisted files/locks are mode 0600.
- JSON writes redact recognized API keys, bearer tokens, passwords, private
  keys, credential-bearing URLs, and session tokens before atomic replacement.
- Manifest and mailbox mutations use file locks; JSON is written with `fsync`
  and same-filesystem atomic replacement.
- `.flowfoundry/runs/` is ignored by Git; transcript and credentials are not run
  artifacts by default.
- Completed input hashes prevent accidental duplicate execution after recovery.

## Human-gated actions

The following action classes require a scoped persisted approval:

- push and force-push;
- merge into a protected branch;
- file or repository deletion;
- repository rename;
- deployment and release;
- real external message delivery;
- credential access;
- high-risk shell execution.

Without approval the task becomes `skipped_pending_human`. Overnight mode never
waits for an approval and never silently downgrades the gate.

## Reviewer protocol

Every persisted review records the exact task ID, commit/reference, tests,
decision, blocking findings, and suggested fixes. Supported decisions are
`APPROVED`, `APPROVED_WITH_NOTES`, `BLOCKED`, and `REVIEW_PENDING`.
`BLOCKED` prevents dependent validation from running; `REVIEW_PENDING` preserves
state for a later resume. Approval of code review is separate from approval of a
release, deployment, push, or external message.

## Known MVP limits

- Redaction is defense in depth, not a substitute for excluding secrets from
  task inputs.
- The local-command adapter does not yet provide an OS sandbox, resource quota,
  or provider-native cancellation. It is disabled unless explicitly selected.
- File locks coordinate processes on the same compatible local filesystem; the
  MVP is not a distributed scheduler.
- Task directories isolate orchestration state, not a complete source worktree.
  A production provider adapter should provision an approved worktree/container
  matching the agent's declared workspace mode.
- Timeout is persisted and applied by the local command adapter, but remote
  provider cancellation semantics are future adapter work.

These limits are reasons to keep real execution opt-in; they do not affect the
offline deterministic test workflow.

