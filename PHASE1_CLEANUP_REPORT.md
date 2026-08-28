# Phase 1.1 Workspace Cleanup Report

Date: 2026-08-05

Branch: `portfolio-migration`

Scope: Phase 1.1 architecture hygiene only; no Phase 2 or Feedback work

## Outcome

Phase 1.1 is complete. The Workspace implementation now imports canonical
subpackage modules directly, the obsolete root-level compatibility modules have
been removed after repository-wide dependency checks, runtime/cache artifacts
are ignored and removed, and minimum lifecycle, session, policy, recovery,
permission, isolation, and finalization tests are present.

No new runtime feature or architecture was introduced.

## 1. Import cleanup

All Python imports below `src/flowfoundry/workspace/` were checked.

- Imports within the same subpackage use direct relative imports, such as
  `.project`, `.git_manager`, `.finalize`, `.hooks`, and
  `.transcript_claude`.
- Imports across canonical Workspace subpackages use their explicit target,
  such as `..lifecycle.project`, `..sessions.finalize`,
  `..policy.runtime`, and `..maintenance.projects`.
- Internal modules no longer import through root-level Workspace shims.
- FlowFoundry CLI entry points and the capability registry now reference the
  canonical modules.
- The legacy `ai_project_manager` package maps historical names directly to
  canonical modules without relying on root-level Workspace files.

An architecture contract test parses the Workspace source AST and fails if an
internal import is added for any removed root-level shim.

## 2. Root shim cleanup

The architecture review described 14 root-level legacy files. Filesystem and
Git inspection found 15 shim files; the additional file was `cc_launcher.py`.
The complete verified set was:

1. `auto_name.py`
2. `cc_launcher.py`
3. `finalize.py`
4. `git_manager.py`
5. `hook_entry.py`
6. `hooks.py`
7. `launcher.py`
8. `maintain.py`
9. `maintain_cli.py`
10. `project.py`
11. `recovery.py`
12. `redact.py`
13. `transcript_claude.py`
14. `transcript_codex.py`
15. `utils.py`

The first repository-wide `git grep` identified consumers in FlowFoundry CLI
modules, the capability registry, deployment/wrapper scripts, Workspace tests,
and Workspace internals. Each consumer was migrated to a canonical module.
A second code search across Python, Shell, and JSON files returned no remaining
root-shim dependency before deletion.

All 15 shim files were then deleted. Public shell commands (`cc`, `aiproj`, and
`cc-projects-maintain`) remain in place and delegate to canonical entry points.
The change remains reversible through the Phase 1.1 Git commit.

Tracked source/test `__pycache__` directories and `*.pyc`/`*.pyo` files were
removed. `.gitignore` now ignores these artifacts recursively.

## 3. Test coverage added

Minimum Workspace runtime coverage now includes:

- **Lifecycle:** project structure, private-directory mode, ignore policy, and
  valid/invalid status transitions.
- **Sessions and recovery:** discovery of an interrupted running session whose
  session directory is missing.
- **Policy and permissions:** locked atomic JSON persistence, credential
  redaction, Claude permission modes, Codex profiles, and provider environment
  isolation.
- **Finalize pipeline:** transcript collection, private raw preservation,
  public transcript redaction, transcript hashing, conversation generation,
  and completed status for a non-Git fixture.
- **Finalize failure:** clean failure when project metadata is absent.
- **Architecture:** canonical import availability, root shim absence, forbidden
  internal shim imports, CLI export stability, and direct legacy-package
  mappings.

All tests use temporary project roots. Synthetic credentials are used only to
verify redaction and are never written to tracked files.

## 4. Validation results

| Check | Result |
|---|---:|
| Targeted Workspace cleanup tests | 14 passed, 26 subtests passed |
| `PYTHONPATH=src pytest` | 103 passed, 35 subtests passed |
| Focused launcher contract (`test-cc.sh`) | 24 passed |
| EOF, remote, provider, and permission suite | 40 passed, 0 failed |
| Isolated deployment/profile/auth preservation suite | 4 passed |
| `PYTHONPATH=src python -m flowfoundry validate` | 4 components, 1 workflow contract, 16 capabilities |
| Workspace cleanup Ruff scope | passed |
| `git diff --check` | passed |

The Ruff validation scope covers `src/flowfoundry/workspace`,
`src/ai_project_manager`, Workspace tests, and the two FlowFoundry CLI adapter
modules changed by this cleanup. Unrelated pre-existing foundation lint findings
outside the Phase 1.1 change set were not modified.

The deployment test used an isolated HOME and XDG state directory under the
project test area. No user-level deployment was performed.

## 5. Compatibility and risk

- Repository-owned consumers no longer depend on the deleted modules.
- Existing public command files remain available.
- Historical `ai_project_manager.<module>` imports continue to map directly to
  canonical implementations.
- Undiscovered third-party consumers that directly import a removed
  `flowfoundry.workspace.<legacy-module>` path will need to adopt the canonical
  subpackage path. Repository-wide search cannot prove the absence of external
  consumers.
- The finalization pipeline remains structurally large, as recorded in the
  architecture review. It was covered by an end-to-end fixture but deliberately
  not redesigned during migration cleanup.

## Stop boundary

Phase 1.1 stops here. Phase 2, Feedback, Huiying, and Multi-Agent functionality
were not entered.
