# CI Fix Report

**Date:** 2026-08-05
**Branch:** `portfolio-migration`
**Fix commit:** `c535d43c804df634321099a00140d32b1005c035`
**Scope:** Phase 0 preparation only; no repository migration was performed.

## Outcome

The local equivalent of every job in `.github/workflows/tests.yml` is green.
The fix aligns the workspace-manager CI job with the unified FlowFoundry Python
runtime while preserving the existing launcher commands, provider choices,
permission mappings, deployment safeguards, and test coverage.

The remote GitHub Actions result was not re-run in this phase because the
branch was not pushed and GitHub API operations were explicitly out of scope.
The status in this report therefore means **locally verified CI-equivalent
green**, not a claim that a new remote Actions run has completed.

## Failure analysis

The red workspace job was caused by test and deployment assumptions left over
from the former standalone Bash implementation:

1. The job set `core/workspace-manager` as its working directory but invoked
   the unified package with `PYTHONPATH=src`. That path resolved inside the
   component directory, not the monorepo root, so `flowfoundry` was not
   importable.
2. `test-cc.sh` and the static checks in `test-cc-eof-fix.sh` searched the thin
   `bin/cc` wrapper for functions and menu text that now live in
   `src/flowfoundry/workspace/cc_launcher.py`.
3. The component deployment script treated `core/workspace-manager` as the
   Python package root. In the unified repository, the installable
   `pyproject.toml` and `src/flowfoundry` package are at the monorepo root.
4. Deployment verification assumed a live user systemd manager and inspected
   the retired Bash implementation rather than the installed Python runtime.
5. Synthetic Claude/DeepSeek test commands do not produce a real transcript.
   The launcher correctly reports that finalization limitation after the fake
   CLI is invoked, so the test needed to distinguish successful CLI dispatch
   from an expected synthetic finalizer result.

## Changes made

| Area | Change | Compatibility intent |
|---|---|---|
| GitHub Actions | Run workspace commands from the repository root and point discovery at `core/workspace-manager/tests`. | Makes `PYTHONPATH=src` resolve the existing unified package. |
| Public wrappers | Resolve a source checkout's monorepo root and prepend its `src` directory; installed deployments continue to use the installed package. | Keeps the existing `cc`, `aiproj`, and `cc-projects-maintain` commands. |
| Launcher tests | Replace static assertions against the retired 1,000-line shell body with 24 behavior-level contract tests. | Preserves coverage of project selection, recent projects, provider and permission menus, launch arguments, wrappers, and safety rules. |
| EOF/permission tests | Exercise the Python implementation and intercepted native Claude/DeepSeek/Codex commands. | Retains EOF, remote double-confirmation, config isolation, and native Codex TUI coverage. |
| Launcher behavior | Restore legacy non-zero cancellation semantics for invalid/closed launch confirmation and explicit remote-confirmation diagnostics. | No function signature, command name, provider value, profile name, or launch argument changed. |
| Deployment | Detect the monorepo package root, tolerate an unavailable user systemd manager, and verify unified Python modules. | Keeps profile preservation, permission mode, `CC_ACTIVE_PROJECT`, and `auth.json` non-modification safeguards. |
| Test artifacts | Keep temporary fixtures under `.test-tmp/` and ignore that directory. | Prevents tests from creating top-level project/session directories. |

## Public API compatibility

No public Python callable signature or console command was renamed or removed.
The verified public contract remains:

- Providers: Claude (`c`), DeepSeek (`d`), and OpenAI Codex (`o`).
- Claude-compatible permission modes: `default`, `acceptEdits`, `plan`,
  `auto`, and `bypassPermissions`.
- Codex profiles: `gpt56-sol-manual`, `gpt56-sol-readonly`,
  `gpt56-sol-auto`, and `gpt56-sol-full`.
- Project context: `CC_ACTIVE_PROJECT` and the selected project directory are
  passed to the launched tool.
- DeepSeek uses its isolated configuration directory; Codex launches through
  the native executable with `--profile`.
- Remote high-permission launches still require `remote-yes` plus the normal
  `yes` launch confirmation.

The only observable status correction is that invalid or closed launch
confirmation again returns non-zero, matching the pre-unification Bash CLI
behavior and the existing regression contract.

## Verification evidence

Commands were run from `/home/ryan/Projects/ai-workflow-foundry` unless noted.

| Check | Result |
|---|---:|
| `PYTHONPATH=src python3 -m flowfoundry validate` | 4 components, 1 workflow contract, 16 capabilities validated |
| Foundation unittest discovery | 51 passed |
| Workspace launcher contract | 24 passed |
| Workspace full Python discovery | 38 passed |
| Workspace EOF/remote/permission shell suite | 40 passed |
| Deployment profile-preservation suite | 4 passed |
| Confera media skills | 3 passed |
| Print-ready nameplate workflow | 3 passed |
| Feedback lint | passed |
| Feedback pytest suite | 90 passed |
| Workflow YAML parse | passed |
| `git diff --check` before commit | passed |

The 24 launcher contract tests are intentionally also included in the 38-test
workspace discovery run because CI checks both the focused launcher entrypoint
and the whole workspace Python suite.

## Files in the CI fix commit

- `.github/workflows/tests.yml`
- `.gitignore`
- `core/workspace-manager/bin/{cc,aiproj,cc-projects-maintain}`
- `core/workspace-manager/scripts/deploy.sh`
- `core/workspace-manager/tests/test-cc.sh`
- `core/workspace-manager/tests/test-cc-eof-fix.sh`
- `core/workspace-manager/tests/test-deploy-profile-preservation.sh`
- `core/workspace-manager/tests/test_cc_launcher.py`
- `src/flowfoundry/workspace/cc_launcher.py`

The untracked `core/workspace-manager/AGENTS.md` and
`core/workspace-manager/CLAUDE.md` files were deliberately left untouched and
were not included in the commit.

## Rollback

The fix is isolated in one commit on `portfolio-migration`. A recoverable
rollback is:

```bash
git switch portfolio-migration
git revert c535d43c804df634321099a00140d32b1005c035
```

This creates an auditable inverse commit. No reset, force push, merge, or main
branch modification is required.

## Phase 0 constraints honored

- No `git merge` or `git mv`.
- No repository or directory rename.
- No push and no GitHub API operation.
- No source repository was modified.
- No important code or user data was deleted.
- `main` remained at `bf6a4ad7157b9d8b35b7d7325ed609912c6b01d0`.
