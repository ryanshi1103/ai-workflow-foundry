# Phase 1 Workspace Integration Report

**Date:** 2026-08-05

**Repository:** `ai-workflow-foundry`

**Branch:** `portfolio-migration`

**Scope:** Workspace Integration only

**Status:** Complete locally; not pushed

## Outcome

Phase 1 makes `src/flowfoundry/workspace/` the canonical implementation for
the workspace lineage represented by `ai-project-workspace-manager`, the
public `ai-workspace-manager`, and `claude-switcher-setup`.

The integrated runtime now has explicit boundaries for:

- workspace lifecycle;
- session hooks, transcripts, finalization, and recovery;
- permission and redaction policy;
- Claude, DeepSeek, and Codex provider configuration;
- project inventory and maintenance;
- interactive and compatibility CLI entry points.

No Multi-Agent orchestration, new workflow engine, Feedback change, Huiying
change, GitHub rename, repository deletion, or remote push was performed.

## Git lineage and recovery evidence

| Source | Source tip | Preservation treatment | Target evidence |
|---|---|---|---|
| Public `ai-workspace-manager` | `190771ea12f662a76d0f5347061d55d03abb8ede` | Fetched and connected without replacing the target tree | merge `0169a1bd8a494c57c139b0839e68aa40bea356fc` |
| Private `ai-project-workspace-manager` | `ea19e49c93a8acfb6d77fabfe633d3d2b048ba47` | Connected with an unrelated-history `ours` merge | merge `f1ce8501fcd5cfd6970dbb8c036c77c7928969b6` |
| Local-only `claude-switcher-setup` | `aaaa66738947449601f9fdede5c91b251a28fcaf` | Complete, verified private Git bundle; sensitive history not connected to the public branch | `.git/migration-bundles/claude-switcher-backup.bundle` |

The target tree hash was
`c193d8f0eb7eb2d89b127e3b93d3192f9f024233` before both history merges and
remained exactly the same after each merge. This proves the lineage operations
did not overwrite current FlowFoundry files.

The verified Claude switcher bundle has SHA-256:

```text
1f8ca528a3e3084ad0c62ab01b73463df33bb2c5b16cec0f667cc5a30ae425c7
```

The pre-migration annotated tag is
`portfolio-migration/before-workspace-v1`, resolving to tag object
`944de8741dc7b734369f4285bf2173685e775ae1` and target commit
`e3f42ecc8ced2d6621878f070f69d9399a0d7bb8`.

### Claude switcher privacy decision

The committed `claude-switcher-setup` root contains session records, a
redacted transcript, checksums, and local project metadata. Connecting that
commit as a parent would make those objects reachable from a branch intended
for a public repository. The complete history was therefore preserved in the
required private bundle but deliberately not merged into the branch.

Its uncommitted session changes, local metadata, README change, Clash script,
and mobile-network repair document were not copied, staged, modified, or
committed. Portable provider switching behavior is represented by the new
provider policy module and the existing tested launcher behavior, without
copying machine-specific state.

## Canonical workspace layout

```text
src/flowfoundry/workspace/
├── cli/           interactive launcher, project CLI, maintenance CLI
├── providers/     portable provider/profile/permission configuration
├── lifecycle/     project, naming, Git, and launch lifecycle
├── sessions/      hooks, transcripts, finalization, and recovery
├── policy/        local-state utilities and redaction policy
└── maintenance/   inventory, retention, and workspace maintenance
```

The original flat modules remain present as compatibility aliases. Existing
imports such as `flowfoundry.workspace.launcher`,
`flowfoundry.workspace.finalize`, and `flowfoundry.workspace.maintain` resolve
to the canonical implementations. Existing `cc`, `aiproj`,
`cc-projects-maintain`, and hook entry paths were not removed.

## Provider and privacy boundaries

`providers/config.py` owns only portable names and policies:

- the five existing Claude-compatible permission values;
- the four existing Codex profile identifiers;
- isolated Claude and DeepSeek config directory selection;
- removal of conflicting Anthropic environment values when native Claude is
  selected.

It does not contain credentials, provider keys, generated profile contents,
live endpoints, session state, transcripts, caches, or user metadata.

The migration explicitly excluded:

- `.ai-session/` and transcript records from source working trees;
- `.ai-session/private/` (not read or modified);
- `__pycache__`, generated caches, and test runtime data;
- uncommitted `.ai/project.json` changes and other machine-local metadata from
  the Claude switcher checkout;
- `auth.json`, `.env`, keys, tokens, and local provider profiles;
- the uncommitted network repair and Clash configuration files.

## Compatibility and test changes

- Added import-identity tests for every legacy flat workspace module.
- Added provider isolation and stable permission/profile contract tests.
- Updated static launcher/deployment verification to inspect the canonical
  `cli/launcher.py` implementation.
- Added a functional `python -m flowfoundry.workspace.maintain_cli` entry point.
- Scoped root pytest discovery to the foundation and workspace suites; the
  independently managed Feedback application retains its own dependency and
  test environment.
- Added a root Ruff policy for import, syntax, and Pyflakes validation.
- Fixed two pre-existing undefined-name defects exposed by Ruff
  (`GENERIC_TITLES` scope and the missing maintenance `re` import).

## Verification

| Check | Result |
|---|---:|
| `PYTHONPATH=src pytest` | 94 passed |
| Focused launcher contract (`test-cc.sh`) | 24 passed |
| EOF, remote confirmation, provider, permission suite | 40 passed |
| Isolated deployment/profile/auth preservation suite | 4 passed |
| `PYTHONPATH=src python3 -m flowfoundry validate` | 4 components, 1 workflow contract, 16 capabilities |
| Canonical and compatibility CLI `--help` smoke checks | passed |
| `ruff check` | passed |
| `git diff --check` | passed |

All deployment checks used an isolated HOME and XDG state directory below the
project test area. No user-level deployment was performed.

The private workspace lineage already tracks its own project-level `.ai`
metadata. That historical object remains part of its preserved, connected Git
history because rewriting or squashing the source was prohibited; it was not
checked out or copied into the FlowFoundry working tree. Untracked session and
user runtime records were excluded.

## Rollback

The migration remains commit-revertible and the source repositories remain
unchanged.

1. Revert the final workspace integration commit with `git revert <commit>`.
2. Revert the private lineage merge, if required, with
   `git revert -m 1 f1ce8501fcd5cfd6970dbb8c036c77c7928969b6`.
3. Revert the public lineage merge, if required, with
   `git revert -m 1 0169a1bd8a494c57c139b0839e68aa40bea356fc`.
4. Create a recovery branch from
   `portfolio-migration/before-workspace-v1` for comparison or restoration.
5. Recover the local-only Claude switcher history from the verified bundle;
   the original checkout also remains intact.

No reset, rebase, squash, force push, main-branch update, repository rename, or
history deletion is needed for rollback.

## Remaining risks

- Flat compatibility aliases are transitional and should remain for at least
  one tagged release before any removal is proposed.
- The legacy deployment copy under the historical `ai_project_manager` name is
  retained for compatibility; the installed FlowFoundry package is canonical.
- A bundle stored below `.git/` is intentionally not included in a normal
  commit or push. It must be backed up separately if the local target clone is
  removed.
- Dirty, uncommitted Claude switcher files remain only in their original local
  checkout and were intentionally not migrated.
- Provider reachability and real CLI authentication were not exercised because
  Phase 1 tests are offline/synthetic and must not use user credentials.

## Next stage

Stop after this report and the Phase 1 commit. The recommended next action is
review and explicit approval of this workspace migration before beginning the
separate Feedback migration stage. Do not begin Feedback or Huiying work from
this report alone.
