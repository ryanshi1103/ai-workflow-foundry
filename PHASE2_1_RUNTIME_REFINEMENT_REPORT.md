# Phase 2.1 Runtime Refinement Report

Date: 2026-08-05

Branch: `portfolio-migration`

Approved baseline: `2bf7258` (`PHASE1_RELEASE_APPROVAL.md`)

Scope: Workspace Runtime refinement only. Feedback Intelligence was not entered.

## Outcome

Phase 2.1 is complete. Session finalization is now composed from isolated,
unit-testable stages; lifecycle and session packages expose curated canonical
APIs; and both launcher modes use one execution/finalization core while keeping
their existing public signatures and command behavior.

This phase adds no user-facing capability and changes no provider, permission,
workflow, or Feedback behavior.

## 1. Finalization decomposition

The approved baseline described `sessions/finalize.py` as approximately 679
lines. The checked-in Phase 1.1 file was 882 lines. It is now a five-line public
compatibility façade that continues to export `finalize_session` from the same
canonical module path.

Implementation responsibilities now live under
`sessions/finalization/`:

| Module | Responsibility |
|---|---|
| `pipeline.py` | Locking and deterministic stage orchestration |
| `validation.py` | Stable result shape, path checks, metadata and session context |
| `recovery.py` | Failure metadata needed for retry and interrupted-session recovery |
| `output.py` | Transcript sync/hash/parse/redaction and session/project documentation |
| `hooks.py` | Safe Git finalization, final commit recording, staging diagnostics and rename hook |

The pipeline retains the original order and invariants:

1. Acquire the project finalization lock.
2. Validate project/session metadata and idempotent completion state.
3. Copy the raw transcript into private storage.
4. Hash and parse the transcript.
5. Generate a redacted transcript and conversation output.
6. Extract the deterministic goal, accomplishments, and decisions.
7. Write session and project documentation.
8. Synchronize tracked final metadata.
9. Safely stage and commit when the project is a Git repository.
10. Record the final commit only in ignored private/global state.
11. Record failure metadata without discarding recoverable data.

The `use_ai` argument remains accepted for API compatibility. Finalization
continues to use deterministic summarization, matching the approved behavior.

## 2. Stable Workspace APIs

`lifecycle/__init__.py` now provides a curated `__all__` covering project
discovery, project/session creation, metadata/status operations, Git lifecycle,
and launcher entry points.

`sessions/__init__.py` now provides a curated `__all__` covering finalization,
hook configuration/dispatch, interrupted-session discovery, and recovery.

Launcher exports in `lifecycle` are loaded lazily. This keeps the stable
canonical imports available while preventing an import-order cycle when a fresh
interpreter imports `sessions` before `lifecycle`. A subprocess regression test
verifies both import orders in a clean interpreter.

## 3. Launcher refinement

The public functions and parameter order are unchanged:

- `launch_new(tool, cli_path, extra_args, env, model, provider, permission_mode, workflow_contract_id)`
- `launch_here(tool, project_dir, cli_path, extra_args, env, model, provider, permission_mode)`

Shared behavior is now implemented once:

- provider executable resolution and validation;
- protected child environment construction;
- provider argument assembly;
- working-directory transition;
- subprocess exit-code handling;
- keyboard interrupt and launch exception handling;
- unconditional safe finalization.

Mode-specific behavior remains separate: `launch_new` performs startup recovery,
project creation and workflow-contract binding; `launch_here` resolves
`CC_ACTIVE_PROJECT` and initializes or continues a session in the selected
project. The existing CC-selected-project redirect remains intact.

## 4. Tests added

The new Phase 2.1 suite covers:

- the identity of the public `finalize_session` façade and pipeline callable;
- finalization context validation;
- isolated pipeline stage orchestration and completion hooks;
- non-Git finalization hook behavior;
- stable lifecycle and sessions canonical exports;
- cycle-free sessions-first imports in a fresh interpreter;
- exact `launch_new` and `launch_here` public signatures;
- protected launcher tracking variables and custom environment propagation;
- subprocess argument and non-zero exit-code preservation;
- `CC_ACTIVE_PROJECT` redirect compatibility;
- both new-project and existing-project delegation to the shared launch core.

The Phase 1 end-to-end finalize fixture remains unchanged and passes, covering
private raw transcript retention, public redaction, hashing, documentation, and
completed metadata.

## 5. Validation results

| Check | Result |
|---|---:|
| Phase 2.1 targeted runtime/architecture tests | 26 passed, 44 subtests passed |
| `PYTHONPATH=src pytest` | 115 passed, 53 subtests passed |
| Focused launcher contract (`test-cc.sh`) | 24 passed |
| EOF, remote, provider, and permission suite | 40 passed, 0 failed |
| Isolated deployment/profile/auth preservation suite | 4 passed |
| Workspace Runtime Ruff scope | passed |
| `git diff --check` | passed |
| `PYTHONPATH=src python -m flowfoundry validate` | 4 components, 1 workflow contract, 16 capabilities |

The deployment test used an isolated HOME and XDG state directory below the
project test area. No user-level deployment occurred.

## 6. Compatibility and risks

- `flowfoundry.workspace.sessions.finalize.finalize_session` remains the public
  implementation entry point used by existing callers and legacy mappings.
- Shell commands and CLI routing are unchanged.
- Public launcher signatures and exit-code rules are contract-tested.
- Finalization private helpers moved to internal stage modules. They were not a
  documented public API; consumers must use `finalize_session` or the new
  canonical package exports.
- The pipeline is structurally easier to extend, but Git staging and document
  generation still perform real filesystem operations. Unit tests isolate these
  stages, while the existing end-to-end fixture verifies their integration.
- Ruff validation is scoped to the Workspace Runtime, its compatibility package,
  adapters, and Workspace tests. Unrelated foundation lint findings outside this
  phase were not modified.

## Stop boundary

Phase 2.1 stops here. No files under `applications/feedback-analysis-system/`
were read or modified, and Feedback Intelligence migration was not started.
