# Portfolio Migration Plan

> Owner: Ryan Shi  
> Target platform: `ai-workflow-foundry`  
> Plan date: 2026-08-05  
> Status: **PROPOSED — NOT EXECUTED**  
> Scope: repository lineage, target architecture, file-movement plan, risks, validation gates, rollback, and proposed Git operations.

## 1. Confirmed decisions

This plan implements the following confirmed architecture without performing it yet:

1. `ai-workflow-foundry` remains the flagship platform. No parallel platform repository will be created.
2. `ai-project-workspace-manager`, `ai-workspace-manager`, and `claude-switcher-setup` become source lineages for modules owned by FlowFoundry.
3. `social-negative-monitor` and `feedback-analysis-system` converge on the product identity `feedback-intelligence-system`.
4. `meeting-media-auto` and `meeting-media-desktop` converge on one private product architecture with shared core and platform-specific distributions.
5. No repository will be deleted. Source repositories remain available as history, rollback sources, and—where useful—read-only release mirrors.
6. Every migration is performed on an integration branch, split into reviewable commits, tested before merge, and reversible with `git revert` or recovery branches.

## 2. Non-negotiable migration rules

- No force push.
- No history rewrite with `git filter-branch`, `git filter-repo`, rebasing of published branches, or squash-only imports.
- No `git reset --hard` as a rollback method.
- No deletion or renaming of local project directories during an active migration.
- No source repository is archived, made public/private, renamed on GitHub, or converted to a mirror without a separate confirmation.
- No uncommitted source files are copied into a target repository.
- `.ai-session/private/`, authentication files, `.env`, provider keys, live server configuration, real media, real participant data, signing material, and machine-specific state are excluded from migration.
- A repository-level merge and a file-layout refactor are separate commits.
- A repository rename and a Python package/module rename are separate operations.
- Compatibility paths remain available for at least one tagged release after a public identifier or import path changes.

## 3. Current-state blockers that must be resolved before execution

The following facts were observed during planning. They are not modified by this document.

| Repository | Current condition | Required preflight decision |
|---|---|---|
| `ai-workflow-foundry` | `main` is ahead of `origin/main` by the analysis/plan commits; latest GitHub Actions run is red in the stale workspace shell test | Review and push documentation commits separately; repair baseline CI before code migration |
| `ai-project-workspace-manager` | Tracked branch is clean, but `.ai-session/` is untracked | Confirm session data remains excluded; do not use `git add -A` |
| `claude-switcher-setup` | Tracked and untracked changes exist; no remote; only one committed historical root | Decide which non-session docs/config are real source, commit them on a preservation branch, and create a verified Git bundle |
| `meeting-media-auto` | Local `master` is one commit ahead of its remote | Review whether the local commit belongs to product history before creating the integration branch |
| `meeting-media-desktop` | Clean on `product/windows-desktop` | Tag this exact release candidate before merging |
| `social-negative-monitor` | Contains two parallel histories: local/archive `main` and public `origin/main` | Connect both histories explicitly; do not overwrite either branch |

No migration begins while the relevant source or target working tree is dirty.

## 4. Repository migration matrix

| Source repository | Canonical destination | Migration mode | Repository after migration |
|---|---|---|---|
| `ai-workflow-foundry` | Itself | Flagship target | Active canonical integration repository |
| `ai-project-workspace-manager` | `src/flowfoundry/workspace/`, `core/workspace-manager/`, selected `docs/` | Connect unrelated history, then reconcile unique files | Retained; later README may point to FlowFoundry after verification |
| public `ai-workspace-manager` | Already represented by `core/workspace-manager/` and FlowFoundry history | No second import; validate existing ancestry and use as temporary release mirror | Retained; no deletion or immediate archive |
| `claude-switcher-setup` | Selected provider/network documentation and safe configuration under workspace operations docs | Commit unique material, connect unrelated history, then selective migration | Retained locally; no public exposure as-is |
| `social-negative-monitor` | Standalone `feedback-intelligence-system` history | Connect parallel history and preserve old product lineage | Retained as a historical checkout/branch |
| public `feedback-analysis-system` | Renamed canonical standalone repository `feedback-intelligence-system` | In-place GitHub repository rename after code/test preparation | Same repository and history under a new name; old URL redirect expected but must be verified |
| FlowFoundry `applications/feedback-analysis-system` | `applications/feedback-intelligence-system` | `git mv`, catalog alias, then controlled subtree/vendor sync | Active bundled reference application |
| `meeting-media-auto` / private `huiying-media-workbench` | Canonical Huiying product repository | Normal merge from shared ancestor; shared-core refactor | Active private canonical product |
| `meeting-media-desktop` / private `huiying-desktop-release` | Canonical Huiying product as Windows/Android platforms | Merge complete history, then move platform-specific files | Retained as a release/history repository; not deleted |

## 5. Target architecture

### 5.1 FlowFoundry flagship

FlowFoundry owns the shared platform contract and workspace runtime. It does not absorb protected Huiying product source.

```text
ai-workflow-foundry/
├── src/flowfoundry/
│   ├── workspace/                 # canonical workspace runtime
│   │   ├── cli/                   # interactive and command entry logic
│   │   ├── providers/             # Claude, DeepSeek, Codex adapters/policy
│   │   ├── lifecycle/             # project, Git, naming, finalization
│   │   ├── sessions/              # hooks, transcripts, recovery, operational memory
│   │   ├── policy/                # permissions, redaction, network/secret boundaries
│   │   └── maintenance/           # project inventory and retention operations
│   ├── catalog.py
│   ├── capability_registry.py
│   └── workflow_contract.py
├── core/workspace-manager/
│   ├── bin/                       # compatibility wrappers
│   ├── config/                    # portable profiles and systemd examples
│   ├── scripts/                   # backup-first deployment/verification
│   ├── docs/                      # public portable operations docs
│   └── tests/                     # wrapper, deployment, compatibility tests
├── applications/
│   └── feedback-intelligence-system/
├── components/
│   └── confera-media-skills/
├── workflows/
├── catalog/
└── docs/migrations/               # lineage manifests and migration decisions
```

The subpackages under `workspace/` are the desired end state, not the first commit. The current flat modules remain import-compatible during migration through re-export shims. Physical splitting happens one subsystem at a time only after the baseline CI is green.

### 5.2 Feedback Intelligence System

The standalone application remains independently runnable and is vendored into FlowFoundry through a documented one-way sync process.

```text
feedback-intelligence-system/
├── src/feedback_intelligence/
│   ├── connectors/                # CSV, JSON, Apify, synthetic/demo
│   ├── analysis/                  # provider client, prompts, classification
│   ├── review/                    # human decisions and audit records
│   ├── storage/                   # SQLAlchemy models/repositories/migrations
│   ├── export/                    # audited CSV/JSON exports
│   ├── schemas.py
│   └── config.py
├── apps/streamlit/
│   ├── app.py
│   └── pages/
├── scripts/
├── tests/
├── pyproject.toml
└── README.md
```

The package move from generic `src.*` imports to `feedback_intelligence.*` is a separate compatibility stage. Repository rename, product-label rename, component-ID rename, package rename, and database migration must not occur in one commit.

### 5.3 Unified Huiying meeting-media product

The existing private workbench becomes the canonical product repository during migration. No new repository is required.

```text
huiying-media-workbench/
├── src/mediaflow/                 # shared product/domain core
│   ├── workflow/                  # tasks, revisions, candidates, approvals
│   ├── providers/                 # Claude/DeepSeek/local provider adapters
│   ├── media/                     # FFmpeg, transcription, inspection
│   ├── storage/                   # SQLite, backup, recovery
│   ├── web/                       # shared FastAPI/Jinja application
│   └── platforms/
│       ├── linux_web/             # service/user installation adapter
│       └── windows_desktop/       # pywebview, desktop lifecycle, credentials
├── android/                       # companion client
├── packaging/
│   ├── linux/
│   └── windows/
├── deploy/
│   ├── linux/
│   └── windows/
├── docs/
│   ├── architecture/
│   ├── platforms/
│   └── commercial/                # remains private
└── tests/
    ├── core/
    ├── linux_web/
    ├── windows_desktop/
    └── android_contract/
```

FlowFoundry receives only a sanitized architecture case study and Confera-compatible contracts. Raw commercial source, vendor payloads, signing information, and protected test artifacts remain in the private product repository.

## 6. Workspace lineage migration

### 6.1 Historical facts

- Public `ai-workspace-manager/main` is already an ancestor of FlowFoundry `main`; importing it again would duplicate history.
- `ai-project-workspace-manager` and FlowFoundry have no common commit hashes even though their source is closely related.
- `claude-switcher-setup` and FlowFoundry have no common commit hashes.
- The private workspace source and current FlowFoundry workspace share 15 module paths; 9 are identical and 6 have diverged.

### 6.2 File movement and reconciliation plan

| Source | Target | Rule |
|---|---|---|
| `ai-project-workspace-manager/src/ai_project_manager/*.py` | `src/flowfoundry/workspace/` logical subpackages | Diff behavior module-by-module; port only unique fixes. Never bulk overwrite newer FlowFoundry modules. |
| `bin/cc`, `bin/aiproj`, `bin/cc-projects-maintain` | `core/workspace-manager/bin/` | Keep thin wrappers; runtime logic belongs in the Python package. |
| `config/codex/` | `core/workspace-manager/config/codex/` | Reconcile portable keys only; preserve user-generated profile sections at deploy time. |
| `config/systemd/` | `core/workspace-manager/config/systemd/` | Keep user-level units and examples; remove machine-specific paths from public templates. |
| `scripts/deploy.sh`, `scripts/verify.sh` | `core/workspace-manager/scripts/` | Merge backup/rollback behavior before changing install paths. |
| Portable architecture/install docs | `core/workspace-manager/docs/` | Migrate with source attribution in a lineage manifest. |
| Unique mobile/network diagnostics | `core/workspace-manager/docs/operations/` | Rewrite as sanitized diagnostics; do not copy live addresses, credentials, routes, or local config. |
| Session records and machine inventory | No target | Explicitly excluded. Source repository retains them according to its own policy. |

### 6.3 Proposed commit sequence

| Commit | Purpose | Acceptance gate |
|---|---|---|
| W0 `fix(ci): align workspace tests with unified runtime` | Repair current red baseline without changing product behavior | All current FlowFoundry jobs green |
| W1 `chore(history): connect private workspace lineage` | Merge private workspace history with the `ours` strategy; working tree unchanged | Tree hash before/after W1 is identical; source commit is an ancestor afterward |
| W2 `chore(history): connect claude switcher lineage` | Connect committed legacy history; working tree unchanged | Tree hash unchanged; bundle and merge parent verified |
| W3 `docs(workspace): record repository lineage and ownership` | Add commit/path/source manifest | Manifest resolves exact source commit IDs |
| W4 `fix(workspace): reconcile deployment and profile preservation` | Port unique portable deploy/config behavior | Deployment tests pass in isolated test home; auth files untouched |
| W5a `refactor(workspace): isolate provider adapters` | Move provider-specific logic and retain compatibility imports | Launcher tests for Claude/DeepSeek/Codex pass |
| W5b `refactor(workspace): isolate project lifecycle` | Move project/Git/naming modules | Lifecycle and maintenance tests pass |
| W5c `refactor(workspace): isolate session recovery` | Move hooks/transcripts/finalize/recovery | Interrupted-session and redaction tests pass |
| W5d `refactor(workspace): isolate policy and maintenance` | Move policy/maintenance code | Permission, dry-run, and retention tests pass |
| W6 `docs(workspace): mark predecessor repositories as migrated` | Add non-destructive pointer READMEs only after release | Source repos remain intact; links and release tags verified |

### 6.4 Proposed Git operations — not executed

```bash
# Target preflight
git status --short --branch
git fsck --full
git switch -c integration/workspace-lineage
git tag -a portfolio-migration/before-workspace-v1 -m "Before workspace lineage migration"

# Public workspace: verify only; do not import again
git merge-base --is-ancestor workspace/main HEAD

# Private workspace: fetch as a temporary remote and connect history without tree changes
git remote add workspace-private https://github.com/ryanshi1103/ai-project-workspace-manager.git
git fetch workspace-private main
git merge --no-ff --allow-unrelated-histories -s ours workspace-private/main \
  -m "chore(history): connect private workspace lineage"

# Legacy local-only repo: create and verify a bundle before importing its committed branch
mkdir -p .git/migration-bundles
git -C ~/Projects/claude-switcher-setup bundle create \
  ~/Projects/ai-workflow-foundry/.git/migration-bundles/claude-switcher.bundle --all
git bundle verify .git/migration-bundles/claude-switcher.bundle
git remote add claude-switcher .git/migration-bundles/claude-switcher.bundle
git fetch claude-switcher master
git merge --no-ff --allow-unrelated-histories -s ours claude-switcher/master \
  -m "chore(history): connect claude switcher lineage"
```

Before W1 and W2, record `git rev-parse HEAD^{tree}`. The same tree hash after each history-only merge proves that no target files were silently replaced.

### 6.5 Workspace risks and rollback

| Risk | Mitigation | Rollback |
|---|---|---|
| New FlowFoundry source is overwritten by older private code | Never use bulk checkout; reconcile each module via reviewed diff | Revert only the affected reconciliation commit |
| `ours` merge preserves graph but obscures file provenance | Add a lineage manifest mapping source commits/files to target modules | Revert the merge commit with `git revert -m 1 <merge>`; source repo remains intact |
| Import path changes break deployed `aiproj` or hooks | Keep top-level compatibility modules and entry points for one release | Revert the subsystem move commit; wrappers continue using old import path |
| Deploy script modifies user authentication/profile state | Test with an isolated home and auth sentinel before any deployment | Do not deploy; revert W4. Existing user deployment remains untouched |
| Machine-specific config leaks into public target | Allowlist files and scan staged diff; never stage `.ai-session`, `.env`, auth, generated profiles | Unstage before commit; if committed locally, revert before push |

## 7. Feedback Intelligence migration

### 7.1 Historical facts

- The local repository contains an older `social-negative-monitor` history and a separate public `feedback-analysis-system` history.
- The two histories have similar content but unrelated commit hashes until the public line was imported into FlowFoundry.
- FlowFoundry already contains the public feedback history as an ancestor and bundles the application at `applications/feedback-analysis-system`.

### 7.2 Canonical ownership

- Standalone repository after rename: `ryanshi1103/feedback-intelligence-system`.
- Standalone repository is canonical for application code and releases.
- FlowFoundry vendors a reviewed snapshot under `applications/feedback-intelligence-system` and owns integration/catalog compatibility.
- Direct edits to the vendored application are prohibited; fixes start in the standalone repository and are synced into FlowFoundry.

### 7.3 File movement plan

| Current path or identity | Target | Compatibility requirement |
|---|---|---|
| Product labels `Social Negative Monitor` / `Feedback Analysis System` | `Feedback Intelligence System` | UI and docs may show “formerly Feedback Analysis System” for one release |
| `src/connectors/` | `src/feedback_intelligence/connectors/` | Temporary imports/re-exports if external scripts use `src.connectors` |
| `src/services/` | Split among `analysis/`, `review/`, and `export/` | Move one service group per commit |
| `src/repositories/`, `database.py`, `models.py` | `src/feedback_intelligence/storage/` | Preserve schema and migration behavior |
| `src/prompts/` | `src/feedback_intelligence/analysis/prompts/` | Prompt version identifiers remain stable |
| root `app.py` and `pages/` | `apps/streamlit/` | Keep a root compatibility launcher for one release |
| `data/social_monitor.db` default | Continue recognizing existing path; introduce new default only with migration | Never silently create a fresh empty database when old data exists |
| `APP_*` and existing environment variables | Accept old names; introduce `FIS_*` or final prefix only after deprecation design | Secrets remain environment-only |
| FlowFoundry path `applications/feedback-analysis-system/` | `applications/feedback-intelligence-system/` via `git mv` | Keep component-ID alias for old workflows |
| Catalog ID `feedback-analysis-system` | `feedback-intelligence-system` | Add explicit alias/deprecation tests before switching provider references |

### 7.4 Proposed commit sequence

| Commit | Repository | Purpose |
|---|---|---|
| F0 `test: lock feedback baseline behavior` | Standalone | Record current test count, mock behavior, exports, and DB compatibility |
| F1 `chore(history): connect social monitor lineage` | Standalone | Start from public history and merge local/archive lineage with `ours` |
| F2 `docs: rename product to Feedback Intelligence System` | Standalone | Product text and architecture only; no import/path change |
| F3 `refactor: introduce feedback_intelligence package` | Standalone | Move package with compatibility imports |
| F4 `fix(storage): preserve legacy database and environment compatibility` | Standalone | Add explicit migration/alias tests |
| F5 `chore(repo): prepare GitHub repository rename` | Standalone | Update URLs, badges, package metadata after rename approval |
| F6 `refactor(feedback): rename bundled application path` | FlowFoundry | `git mv` application path only |
| F7 `feat(catalog): add feedback intelligence ID and legacy alias` | FlowFoundry | Update catalog, capabilities, tests, docs |
| F8 `chore(feedback): sync canonical application snapshot` | FlowFoundry | Vendor exact tagged standalone release |
| F9 `docs: record feedback migration provenance` | Both | Record source tags, target tag, and sync procedure |

### 7.5 Proposed Git operations — not executed

```bash
# In the local feedback repository, start from the public branch
git status --short --branch
git switch -c integration/feedback-intelligence origin/main
git tag -a portfolio-migration/feedback-public-before-unification \
  -m "Public feedback line before unification" origin/main
git tag -a portfolio-migration/social-monitor-before-unification \
  -m "Social monitor line before unification" main

# Connect the unrelated legacy history while keeping the public tree
git merge --no-ff --allow-unrelated-histories -s ours main \
  -m "chore(history): connect social monitor lineage"

# Later, after code and CI are green, rename the existing GitHub repository.
# The actual `gh repo rename` command is deliberately omitted from execution
# until the exact target and visibility are re-confirmed.
```

For FlowFoundry, the bundled-path rename must use `git mv` in its own commit. A subsequent commit updates catalog IDs, capability providers, CI paths, README links, and compatibility aliases.

### 7.6 Feedback risks and rollback

| Risk | Mitigation | Rollback |
|---|---|---|
| Parallel histories are accidentally overwritten | Branch from `origin/main`, tag both tips, merge with `ours` | Revert F1 merge with `git revert -m 1`; both tagged histories remain |
| GitHub rename breaks links/badges/install docs | Inventory all URLs first; rely on redirect only after verification; update references in a separate commit | Rename repository back; revert F5/F7 URL commits |
| Package move breaks imports | Compatibility package and import tests | Revert F3; product-name docs remain independently valid |
| Existing SQLite data appears missing | Detect legacy DB path before creating new DB; test copies of old schema | Revert F4 and continue using legacy path; never delete DB |
| Component-ID rename breaks workflows | Add alias lookup and deprecation window | Revert F7; bundled path rename can remain or be reverted separately |
| Standalone and vendored copies drift | Store upstream tag/commit in a lineage file and enforce a diff check in CI | Re-sync from last known good tag; source repo remains canonical |

## 8. Unified meeting-media migration

### 8.1 Historical facts

- `meeting-media-auto` and `meeting-media-desktop` share 91 commits.
- Their latest common commit is `55d0281` (`feat(tasks): add recoverable and permanent deletion`).
- The workbench has two later local commits, including one not pushed to the remote.
- The desktop line has 14 later product/packaging commits.
- Of 86 common source paths, 69 are byte-identical and 17 have diverged.

Because the repositories share ancestry, a normal non-squash merge is the correct history-preserving operation. `--allow-unrelated-histories` and subtree import are not appropriate here.

### 8.2 Canonical ownership

- Canonical private repository during migration: existing `huiying-media-workbench` / local `meeting-media-auto`.
- Shared `mediaflow` core, web application, provider runtime, workflow state, and storage live once.
- Windows desktop, Linux/web installation, and Android companion are platform modules/distributions.
- Existing `huiying-desktop-release` remains intact as a history and release repository. Whether it later becomes an automated release mirror is a separate decision.
- FlowFoundry documents the product architecture and hosts compatible skill contracts only; it does not ingest protected product code.

### 8.3 File movement plan

| Source | Target in canonical product | Notes |
|---|---|---|
| Both `src/mediaflow/` trees | One reconciled `src/mediaflow/` | Merge shared code first; no copy-overwrite |
| Provider/model candidate code | `src/mediaflow/providers/` and workflow candidate modules | Preserve provider routing, manifest locks, and audit hashes |
| Shared FastAPI/Jinja web code | `src/mediaflow/web/` | Platform-neutral web UI remains shared |
| Desktop-only app/lifecycle/credential code | `src/mediaflow/platforms/windows_desktop/` | Keep Windows Credential Manager and shutdown semantics isolated |
| Linux user-service/install logic | `src/mediaflow/platforms/linux_web/`, `deploy/linux/` | Preserve systemd and local browser workflow |
| `scripts/windows/`, Inno Setup, PyInstaller specs | `packaging/windows/` and `deploy/windows/` | Keep signing inputs outside version control |
| Android/Gradle project | `android/` | Remains a separate client build target |
| Commercial docs and dependency audits | `docs/commercial/` | Private; retain licensing and release blockers |
| Vendor FFmpeg/WebView artifacts | Existing private vendor area or release storage | Never move into FlowFoundry; checksums and notices remain required |
| Duplicate tests | `tests/core/` plus platform suites | Deduplicate identical tests; preserve platform-specific acceptance tests |

### 8.4 Proposed commit sequence

| Commit | Purpose | Acceptance gate |
|---|---|---|
| M0 `chore: establish meeting product migration baseline` | Resolve/preserve the unpushed workbench commit, tag both tips, record test baselines | Both repositories clean; all pre-merge tests recorded |
| M1 `merge: connect Windows and Android product history` | Normal `--no-ff` merge of desktop branch into workbench integration branch | Merge graph includes both tips; no secrets/vendor surprises staged |
| M2 `refactor: establish one shared mediaflow core` | Resolve the 17 divergent shared files by behavior, not by choosing an entire tree | Core/unit/E2E tests pass |
| M3 `refactor: isolate Linux web platform` | Move Linux installation/runtime adapters | Linux install/backup/recovery tests pass |
| M4 `refactor: isolate Windows desktop platform` | Move pywebview, credentials, shutdown, build adapters | Windows static/package tests pass |
| M5 `refactor: isolate Android companion` | Normalize Android boundary and API contract | Android contract/build checks pass |
| M6 `ci: add product platform matrix` | Core, Linux/web, Windows packaging, Android contract jobs | All required jobs green |
| M7 `docs: publish sanitized Huiying architecture case study` | Add non-sensitive case study to FlowFoundry | No commercial source, real media, secrets, or signing details included |
| M8 `docs: mark desktop repository as retained release lineage` | Add pointer only after canonical release validation | Old repository remains cloneable and tagged |

### 8.5 Proposed Git operations — not executed

```bash
cd ~/Projects/meeting-media-auto
git status --short --branch
git fsck --full
git switch -c integration/unified-huiying-product
git tag -a portfolio-migration/workbench-before-unification \
  -m "Workbench before Huiying unification"

git remote add desktop-product https://github.com/ryanshi1103/huiying-desktop-release.git
git fetch desktop-product product/windows-desktop
git tag -a portfolio-migration/desktop-before-unification \
  -m "Desktop product before Huiying unification" \
  desktop-product/product/windows-desktop

# Shared ancestry is already proven; use a normal merge and review conflicts.
git merge --no-ff --no-commit desktop-product/product/windows-desktop

# Review and resolve intentionally, run the baseline suite, then create M1.
# Do not use a whole-tree checkout from either side to resolve conflicts.
```

### 8.6 Meeting risks and rollback

| Risk | Mitigation | Rollback |
|---|---|---|
| Shared files choose desktop defaults that break Linux/web | Resolve the 17 divergent files individually; add platform-default tests | Revert M2 or the relevant platform commit |
| Product data roots, ports, or app identity collide | Keep platform profiles and migration logic explicit | Revert M3/M4; existing installations continue from pre-migration repository |
| Vendor or signing material is exposed | Stage allowlisted paths only; scan commit diff; keep canonical repo private | Cancel before commit; if locally committed, revert and rotate any exposed secret before push |
| Windows packaging claims exceed validation | Preserve current PENDING/release-blocker language | Revert documentation claim; code history remains |
| Merge is too large to review | M1 only connects histories; M2–M5 reorganize one boundary at a time | Revert the latest focused commit; do not revert unrelated validated stages |
| Old release consumers lose source | Keep desktop repository and tags untouched | Point consumers back to old tagged release; no repository deletion is involved |

## 9. Cross-repository validation gates

Each migration stage must pass the gates relevant to its scope before the next commit.

### 9.1 Git and provenance

- `git status --short` is empty before and after tests.
- `git fsck --full` passes in source and target repositories.
- Pre-migration annotated tags resolve to recorded commit IDs.
- History-only merge commits leave the target tree hash unchanged.
- Source tips are reachable from the target only where the plan explicitly connects histories.
- A lineage document records source repository, source commit, target path, migration commit, and license.

### 9.2 Security and privacy

- No `.ai-session/private/`, auth file, `.env`, token, private key, live endpoint, real participant list, real media, database, or signing material is staged.
- Public docs use synthetic paths, fake credentials, and non-routable example addresses.
- Licenses and third-party notices remain attached to imported code/assets.

### 9.3 FlowFoundry

```bash
PYTHONPATH=src python3 -m flowfoundry validate
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m unittest discover \
  -s core/workspace-manager/tests -p 'test_*.py' -v
python3 -m unittest discover -s components/confera-media-skills/tests -v
python3 -m unittest discover -s workflows/print-ready-nameplate-generator/tests -v
```

The current stale shell tests and deployment test must be repaired and made green in W0 before they can serve as migration gates.

### 9.4 Feedback Intelligence

- Ruff and pytest pass in the standalone repository.
- Mock mode completes import → analysis → review → export without credentials.
- A copy of the legacy SQLite schema opens without data loss or silent replacement.
- Old and new import paths pass during the compatibility window.
- The vendored FlowFoundry copy matches the recorded standalone release tag.

### 9.5 Huiying

- Shared core tests pass once, independent of platform adapters.
- Linux/web install, backup, restore, local processing, and browser flow pass.
- Windows package/static tests and desktop lifecycle tests pass without signing secrets.
- Android API/permission contract checks pass.
- Synthetic end-to-end media tests preserve originals and require explicit export approval.
- No external model call, paid provider use, or real media access occurs without separate authorization.

## 10. Rollback model

Rollback is commit-based and non-destructive.

### 10.1 Before every migration line

1. Create an annotated tag on each source tip and target tip.
2. Create an integration branch; never work directly on the default branch.
3. For a repository without a remote, create and verify a Git bundle inside the target repository's `.git/migration-bundles/` directory.
4. Record commit IDs and tree hashes in `docs/migrations/`.
5. Keep all original repositories and local directories unchanged.

### 10.2 Reverting focused commits

```bash
git switch integration/<migration-name>
git revert <focused-commit>
```

### 10.3 Reverting a history merge

```bash
git revert -m 1 <merge-commit>
```

This removes the merge's effect from the current line without deleting either parent's history or rewriting published commits.

### 10.4 Recovering without changing the current branch

```bash
git switch -c recovery/<migration-name> portfolio-migration/<pre-migration-tag>
```

The recovery branch can be tested and compared before any default-branch decision.

### 10.5 GitHub repository rename rollback

If the confirmed Feedback Intelligence rename causes unacceptable integration breakage, rename the same repository back through GitHub settings/CLI and revert only the URL/badge/catalog commits. Do not create a replacement repository and do not force-push history.

## 11. Recommended execution order

| Stage | Migration line | Why this order |
|---|---|---|
| 0 | Push reviewed planning commits; repair FlowFoundry CI baseline | A red baseline cannot validate later migrations |
| 1 | Workspace lineage and canonical module ownership | Establishes the flagship's core and migration discipline |
| 2 | Feedback Intelligence identity and package migration | Public application is relatively bounded and already tested |
| 3 | FlowFoundry feedback path/catalog sync | Occurs only after a tagged standalone canonical release |
| 4 | Huiying history merge and shared-core refactor | Highest complexity and private; benefits from proven migration process |
| 5 | Sanitized Huiying case study in FlowFoundry | Only after unified architecture is validated |
| 6 | Predecessor pointer READMEs and portfolio navigation | Last step; no repo is deleted or hidden |

Do not execute workspace, feedback, and meeting merges concurrently. Each line changes source-of-truth rules and should finish its acceptance gate before the next begins.

## 12. Expected commit ledger

The migration should produce a ledger similar to the following. Exact hashes are filled only after execution.

| Stage | Repository | Branch | Pre-tag | Commits | Tests | Result |
|---|---|---|---|---|---|---|
| W0–W6 | `ai-workflow-foundry` | `integration/workspace-lineage` | `portfolio-migration/before-workspace-v1` | Pending | Pending | Not started |
| F0–F5 | `feedback-intelligence-system` | `integration/feedback-intelligence` | Two lineage tags | Pending | Pending | Not started |
| F6–F9 | `ai-workflow-foundry` | `integration/feedback-intelligence` | Pending | Pending | Pending | Not started |
| M0–M8 | `huiying-media-workbench` | `integration/unified-huiying-product` | Workbench + desktop tags | Pending | Pending | Not started |

## 13. Approval gates

Execution requires explicit confirmation at four points:

1. Approve this migration plan and target layouts.
2. Approve cleanup/preservation commits in currently dirty source repositories.
3. Approve each history merge after tags, bundles, and tree-hash evidence are shown.
4. Approve external GitHub changes separately: repository rename, default branch update, release mirror behavior, or predecessor README changes.

Until those confirmations are received, this document is the only deliverable. No file movement, merge, repository rename, remote write, or source-repository modification is authorized.
