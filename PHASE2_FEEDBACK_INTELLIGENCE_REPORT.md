# Phase 2.2 — Feedback Intelligence Report

## Status

Phase 2.2 is complete locally on `portfolio-migration`. No push, remote rename,
release, deployment, database move, or user-data migration was performed.

The product now uses the canonical local identity
`feedback-intelligence-system`, while the existing public repository identity
and its history remain intact. `feedback-analysis-system` and
`social-negative-monitor` remain explicit compatibility aliases.

## Source and lineage

- Public baseline: `e8b9e3374521578702eed7b92ea67dd5a2c1f327`
- Isolated source branch: `migration/feedback-intelligence`
- Final source commit: `93b646baf6c92437b97abc0e13d6b6e53b8811eb`
- Final source tree: `2a2c2796a4176a0fc354ba94d73bdbe00e0f38c2`
- Initial history connection: `d3ee9544584e844a090ebda7463b047e32724e63`
- Final source follow-up connection: `c8bac35b8c9c8cb9725a2f3d9da743e43aa01d85`
- FlowFoundry application commit: `cde3d6b357c49c6ad2037577c60317a496d07bc8`

Both history connections are non-squash, `ours` strategy merges. Each merge
tree equals its first-parent tree. The application was then synchronized from a
Git archive; its staged subtree hash matched the standalone source root tree.

The local archive-only lineage was not connected because it contains tracked
session material. Its full graph is retained only in a repository-external Git
bundle with SHA-256
`8544ce02c43b1ac645d4993246985f14f24643c70427f63fb0e1b1d038c8183d`.

## Application changes

- Moved the bundled application to
  `applications/feedback-intelligence-system/`.
- Introduced the canonical `feedback_intelligence` package.
- Preserved `src.*` through module-object aliases, preventing duplicate
  configuration and SQLAlchemy metadata.
- Retained `app.py`, existing scripts, existing environment variables,
  Streamlit widget keys, table and column names, and export formats.
- Added a dependency-light FlowFoundry adapter contract.
- Added catalog aliases and collision validation.
- Updated capability providers and corrected the dashboard entry point from the
  nonexistent `app:server` to `app:main`.
- Registered the import → deduplicate → analyze → human review → export workflow
  with an explicit authoritative-export approval gate.

## Database compatibility

- `APP_DB_URL` remains supported; `FEEDBACK_DB_URL` is an additive canonical
  variable and has precedence only when explicitly set.
- The legacy default `sqlite:///data/social_monitor.db` remains unchanged.
- Relative SQLite paths are anchored to the application root instead of the
  launcher's current working directory.
- `sqlite:///:memory:` remains a real memory database and can no longer become a
  disk file named `:memory:`.
- Schema migrations create an empty database at the current schema, add only
  missing columns and indexes to old schemas, preserve existing rows, propagate
  failures, and are safe to repeat.
- No `*.db`, `*.sqlite`, `*.sqlite3`, WAL, SHM, export, cache, credential, or
  user database was imported.

## Compatibility tests

The Feedback suite covers analysis, deterministic mock-provider behavior,
manual review persistence, filters, empty and old-schema upgrades, repeated
migrations, preserved legacy rows, failure propagation, the legacy database
location, true in-memory SQLite, alternate working directories, import
validation, deduplication, export, legacy module identity, legacy environment
variables, Streamlit component IDs, and FlowFoundry registration.

## Validation results

| Validation | Result |
|---|---|
| FlowFoundry pytest | 117 passed, 53 subtests passed |
| Feedback pytest | 101 passed |
| FlowFoundry Ruff | Passed |
| Feedback Ruff | Passed |
| Shell syntax (`scripts/*.sh`) | Passed |
| `git diff --check` | Passed |
| `flowfoundry validate` | 4 components, 2 workflow contracts, 16 capabilities |
| Source/bundled tree equality | Passed |

## Review status

- Phase 2.1: `APPROVED_WITH_NOTES`, no P0/P1 findings.
- Feedback baseline lineage: `APPROVED`.
- Initial Feedback lineage connection: `APPROVED_WITH_NOTES`, no P0/P1.
- The review note about standard Feedback test discovery was fixed in
  `b6427ae`; the note about repeated migrations is covered by the 101-test suite.
- Later Phase 2.2 checkpoints may remain `REVIEW_PENDING`; no approval is
  inferred when a review file is absent.

## Risks and deferred human actions

- The GitHub repository still has its old remote name. Rename and redirect
  verification require explicit human action.
- No open-source license was invented; the repository continues to state
  learning/internal-use terms until the owner makes a license decision.
- Exact schema rollback uses the operator's pre-upgrade database backup. No
  destructive automatic down-migration is provided.
- A real demo screenshot has not been fabricated; the README provides a
  reproducible mock-mode demonstration instead.
- Push, GitHub topics, release creation, and deployment remain manual actions.

Phase 2.2 stops here. Feedback Intelligence is ready for review and for later
manual remote-identity work; no remote mutation is required for subsequent
independent local migration phases.
