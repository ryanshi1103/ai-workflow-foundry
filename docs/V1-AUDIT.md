# FlowFoundry v1 Repository Audit

Audit reconciled: 2026-08-14
Canonical source: `.ai/PROJECT_STATE.md`, current deterministic runtime/status
commands, current durable evidence, then historical reports.

## Executive state

FlowFoundry is a local-first adaptive AI team runtime. Its operating rule is to
select the smallest sufficient Agent or Team, execute in a real workspace, use
deterministic validation where possible, retain evidence, and bound calls,
cost, retries, and irreversible actions.

The local privacy-safe publication history passed at
`2ffa817cba37cfa876d19e5b60a31a1bfe2efc8b`. Public release remains blocked:
GitHub historical exposure and PR #2 are unresolved, and no remote replacement
has been authorized.

## Capability map

| Area | Current state | Verified boundary |
|---|---|---|
| Provider identity | VERIFIED | Codex uses `codex_native`; DeepSeek-compatible uses `deepseek_compatible`; Claude-native is not authenticated and is not READY |
| Minimum path | IMPLEMENTED | Task profiling chooses no model, one Agent, or a minimum sufficient bounded team |
| Workspace | VERIFIED | Compatibility preflight and managed immutable-base writer worktrees preserve the user worktree |
| Process identity | IMPLEMENTED | Durable Process Identity v2 distinguishes verified live, gone, mismatch, and unverified native processes |
| Cancellation | LIVE VERIFIED | Cross-process physical cancellation is bounded and fail-closed |
| Meeting | LIVE VERIFIED | Independent bounded views, deterministic conflict detection, optional targeted Round 2, convergence, dissent, receipts, and recovery |
| Durable reconciliation | IMPLEMENTED / VERIFIED IN C3A | Stale `RUNNING` is reconciled from receipts, validation, candidate, lease, process, and integration evidence |
| Status | IMPLEMENTED | Exposes effective semantic state, activity, terminality, retention, validation, integration state, confidence, and required human action |
| Recovery | IMPLEMENTED | Reconciles before resume and does not restart terminal or evidence-conflicted execution |
| Cost evidence | IMPLEMENTED | Records available calls, tokens, latency, and cost without inventing unavailable telemetry |
| Experience | IMPLEMENTED | Persists bounded execution and Meeting evidence for future routing decisions |

## Durable run state contract

Top-level manifest state is an operational cache, not sole proof of liveness.
Reconciliation uses this evidence order:

1. terminal native execution records and task/provider receipts;
2. deterministic validation;
3. candidate commit and terminal result artifacts;
4. writer lease and retained-worktree state;
5. Durable Process Identity v2 liveness;
6. integration and recovery metadata;
7. the manifest's stale `RUNNING` observation.

The implementation preserves `observed_original_state`, appends an auditable
reconciliation record, records its evidence hash and reason, and is idempotent.
A verified live process remains `STILL_RUNNING`. Completed validated candidates
can be `COMPLETED_AWAITING_INTEGRATION`. Explicit failed or cancelled execution
with a retained candidate becomes a corresponding retained terminal state.
Missing PID evidence alone never means success, and conflicting or incomplete
terminal evidence becomes `RECONCILIATION_BLOCKED`.

Execution terminality and integration terminality are intentionally separate.
A retained worktree may be a validated candidate awaiting integration, failed
review evidence, or an abandoned/recoverable candidate; retention alone proves
neither success nor failure.

## Known retained manifests

The two known stale manifests were inspected read-only in C3A and dry-run
classified using the same runtime implementation. Their source artifacts remain
unchanged pending explicit C3B authorization. Canonical state must not claim
that those durable artifacts have already been repaired.

## Brand and product surface

- Official name: FlowFoundry.
- Naming decision: KEEP FLOWFOUNDRY.
- Category: Local-first Adaptive AI Team Runtime.
- Final visual candidate and campus poster candidate exist.
- Product assets, README surface, and GitHub branding are not yet reconciled or
  installed.

## Privacy and release boundary

The sanitized local history has zero local privacy blockers and passed current
tree, reachability, fresh-clone, ref-surface, privacy, and deterministic product
verification. This does not close the remote incident. Pull refs, cached commit
pages, host-retained objects, forks, clones, and mirrors require Gate D planning
and GitHub-side verification.

No force push, PR mutation, remote ref deletion, merge, release, or publication
is authorized by this audit.

## Validation baseline

- Foundation: 228 passed.
- Workspace launcher/contracts: 26 passed.
- Workspace provider-launch shell: 40 passed.
- Workspace profile/deploy preservation: 4 passed.
- Workspace Python: 68 passed.
- Confera contracts: 3 passed.
- Nameplate contracts: 3 passed.
- Product total: 372 passed, 0 failed.
- Ruff: unavailable in the verified environment.
- Feedback optional pytest extras: unavailable in the verified environment.

## Highest-value remaining work

1. Apply the two approved durable manifest reconciliations only after C3B owner
   authorization, then re-verify the sanitized canonical baseline.
2. Prepare Gate D's remote replacement and rollback plan for human review.
3. Install the approved visual identity and reconcile product-facing surfaces.
4. Continue the deny-by-default network and local-secret foundation.
5. Add project-local Provider Registry and adapter entry points before broad
   provider expansion.
6. Build Operator Experience 0.4 after the release baseline is safe.

Historical reports are retained as evidence, not deleted or rewritten into
current truth.
