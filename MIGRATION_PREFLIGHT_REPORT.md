# Migration Preflight Report

**Date:** 2026-08-05
**Integration branch:** `portfolio-migration`
**Mode:** Read-only source inspection plus local test execution; no migration.

## Executive summary

All three product groups have usable source and green code baselines, but none
should enter actual migration until its identity and privacy gates are closed.
Three requested repository names are not separate local checkouts; they are
public repository identities or aliases of another checkout. Treating those
names as aliases is necessary to avoid importing the same history twice.

| Group | Requested name | Local representation | Readiness | Primary gate before migration |
|---|---|---|---|---|
| Workspace | `ai-project-workspace-manager` | Standalone checkout | Yellow | Quarantine untracked session records before any history operation. |
| Workspace | `ai-workspace-manager` | No standalone checkout; remote plus bundled `core/workspace-manager` | Yellow | Reconcile stale cached ref, live remote head, and the two workspace histories. |
| Workspace | `claude-switcher-setup` | Standalone checkout | Red | Dirty tree, no remote/upstream, and user/network configuration require an explicit preservation and privacy decision. |
| Feedback | `feedback-analysis-system` | Public remote plus bundled application | Yellow | Declare public remote `main` as canonical and keep runtime databases out of migration. |
| Feedback | `social-negative-monitor` | Standalone checkout with archive and public lineages | Yellow | Current branch tracks an unavailable archive remote; public branch is locally stale. |
| Huiying | `huiying-media-workbench` | GitHub identity of `meeting-media-auto` | Yellow | Do not double-import; record the local one-commit-ahead source snapshot. |
| Huiying | `meeting-media-auto` | Standalone checkout | Yellow | Make its Python environment reproducible without user-site leakage. |
| Huiying | `meeting-media-desktop` | Standalone checkout | Yellow | Generate the hash-locked Windows dependency file before release consolidation. |

`Red` here means “do not start history-changing operations yet,” not that code
should be deleted or archived.

## Inspection method and boundaries

- Git status, branches, cached tracking refs, commit relationships, manifests,
  ignore rules, and test entrypoints were read locally.
- Live remote heads were checked with read-only Git protocol
  (`git ls-remote`). No `fetch`, push, or GitHub API call was made.
- High-confidence credential patterns were scanned by filename and tracked
  content. Candidate values were never printed. Apparent Huiying hits were
  verified as the substring `task-...`, not credentials.
- `.ai-session/private/` was excluded and not read.
- Tests used temporary HOME/TMP locations under the active FlowFoundry project.
  Source repository Git status was checked again afterward.

## Repository identity map

### Workspace

#### `ai-project-workspace-manager`

- **Checkout:** `~/Projects/ai-project-workspace-manager`
- **Current branch/HEAD:** `main` at `ea19e49c93a8`
- **Tracking:** `origin/main`; cached behind/ahead `0/0`
- **Live remote:** `origin/main` at `ea19e49c93a8` — synchronized
- **Working tree:** six untracked `.ai-session` records: project metadata plus
  one session's events, heartbeat, metadata, redacted transcript, and checksum
- **Dependencies:** no `pyproject.toml` or requirements file; Bash plus Python
  standard-library runtime
- **Test baseline:** 64 launcher structure checks, 35 EOF/permission checks,
  4 deployment-preservation checks, and 14 Python tests — all passed
- **Migration target:** source/reference lineage for the workspace, `cc`, Codex
  integration, and AI Project Manager module entering `core/workspace-manager`
- **Gate:** preserve these uncommitted session records outside the public import
  set without deleting them; create a clean source snapshot only after approval

#### `ai-workspace-manager`

- **Standalone checkout:** absent under `~/Projects`
- **Representations available:**
  - bundled module: `core/workspace-manager`
  - FlowFoundry remote: `workspace`
  - cached `workspace/main`: `5715e2e927d0`
  - live remote `main`: `190771ea12f6`
- **Branch/working tree:** not applicable as a standalone repository
- **Remote state:** the cached remote ref is stale and the live commit is not
  present in the active object database because this phase did not fetch
- **Test baseline:** bundled runtime is green: 24 focused launcher tests,
  38 total workspace Python tests, 40 EOF/permission checks, and 4 deployment
  checks
- **Migration target:** remain the workspace module inside
  `ai-workflow-foundry`; do not create a new platform repository
- **Gate:** after approval, fetch to a temporary migration ref and produce an
  ancestry/path comparison against both `ai-project-workspace-manager/main` and
  the already bundled history before selecting commits

#### `claude-switcher-setup`

- **Checkout:** `~/Projects/claude-switcher-setup`
- **Current branch/HEAD:** `master` at `aaaa66738947`
- **Tracking/remotes:** no upstream and no Git remote configured
- **Working tree:** eight tracked files modified and two untracked files
  - modified: `.ai-session` project/session records, `.ai/project.json`, README
  - untracked: `config/clash-verge/Script.js` and
    `docs/mobile-network-repair-2026-08-02.md`
- **Dependencies/tests:** no package manifest and no formal automated test
  suite; no tracked shell scripts were available for a syntax baseline
- **Migration target:** extract reusable provider/config switching rules into a
  bounded adapter under the FlowFoundry workspace runtime; keep machine/network
  repair material outside the public module unless explicitly approved
- **Gate:** first create a local preservation commit or bundle on a user-chosen
  private branch/location, because there is currently no remote recovery point

### Feedback

#### `feedback-analysis-system`

- **Standalone checkout:** absent under `~/Projects`
- **Representations available:**
  - public remote `feedback/main` at live and cached `e8b9e3374521`
  - bundled application at `applications/feedback-analysis-system`
- **Working tree/branch:** not applicable as a standalone checkout; the bundled
  copy is governed by `portfolio-migration`
- **Dependencies:** same dependency and dev-tool declarations as the public
  `social-negative-monitor` source
- **Test baseline:** Ruff passed; 90 pytest tests passed in the bundled copy
- **Migration target:** become the canonical product identity
  `feedback-intelligence-system`, with the existing bundled application as the
  initial implementation boundary
- **Gate:** document the rename/compatibility mapping before any repository
  rename; actual repository rename remains out of scope

#### `social-negative-monitor`

- **Checkout:** `~/Projects/social-negative-monitor`
- **Current branch/HEAD:** `main` at `62a1e00efa75`
- **Working tree:** clean
- **Current tracking:** cached `archive/main`, behind/ahead `0/0`
- **Archive remote:** live lookup returns “repository not found”; it is not a
  dependable recovery target
- **Public line:** local `public-main` and cached `origin/main` are at
  `06ab1d8`, while live public `origin/main` is `e8b9e3374521`; local public
  tracking is stale and exact ahead/behind cannot be computed without fetch
- **Lineage divergence:** relative to the cached public line, current `main`
  carries local handoff/session documentation and deletes `.env.example`; it
  must not be assumed to be the same release line
- **Dependencies:** Python `>=3.11`; Streamlit, SQLAlchemy, Pydantic, OpenAI,
  pandas, Plotly, HTTPX, Apify, APScheduler, dotenv, and Tenacity; pytest,
  pytest-cov, and Ruff for development
- **Test baseline:** Ruff passed and 90 pytest tests passed
- **Migration target:** reusable ingestion, deduplication, analysis, severity,
  repository, and export capabilities for `feedback-intelligence-system`
- **Gate:** select the live public line as code baseline, review the five local
  archive-line commits separately, and exclude ignored local runtime data

### Huiying

#### `huiying-media-workbench`

- **Standalone checkout:** absent; this is the `origin` repository identity of
  `~/Projects/meeting-media-auto`
- **Live default branch:** `master` at `28f2f74e1a7b`
- **Migration meaning:** product/workbench identity, not an additional source
  tree
- **Gate:** import or map the `meeting-media-auto` history exactly once

#### `meeting-media-auto`

- **Checkout:** `~/Projects/meeting-media-auto`
- **Current branch/HEAD:** `master` at `a02d112c07af`
- **Working tree:** clean
- **Tracking:** `origin/master`; cached behind/ahead `0/1`
- **Live remote:** `huiying-media-workbench/master` at `28f2f74e1a7b`; local
  checkout contains one unpushed commit
- **Dependencies:** Python `>=3.11`; Pillow, PyYAML, NumPy, FastAPI, Uvicorn,
  Jinja2, multipart, QR code, and defusedxml; OpenCV is an OS dependency
- **Test baseline:** 496 unittest tests passed
- **Migration target:** shared offline media domain, pipeline, review gates,
  API, and workbench services for the unified Huiying product architecture
- **Gate:** preserve/tag the unpushed local commit and build from an isolated,
  fully declared environment

#### `meeting-media-desktop`

- **Checkout:** `~/Projects/meeting-media-desktop`
- **Current branch/HEAD:** `product/windows-desktop` at `a78e8b3e9ec2`
- **Working tree:** clean
- **Tracking/live remote:** `origin/product/windows-desktop`, behind/ahead
  `0/0`; live default branch is the same commit
- **Other branch:** local and live `master` at `55d0281f64ec`
- **Dependencies:** shares the media stack and adds `cryptography`, pywebview,
  PyInstaller, Windows wheels, WebView2, and packaged FFmpeg concerns
- **Test baseline:** 546 unittest tests passed
- **Migration target:** desktop shell, Windows packaging, support/recovery, and
  platform adapters over the common Huiying media core
- **Gate:** replace the placeholder `requirements-windows.lock.txt` with a
  complete hash-locked Windows CPython 3.11 graph before release consolidation

## Git status and remote risk matrix

| Repository/check-out | Dirty state | Upstream state | Risk |
|---|---|---|---|
| `ai-workflow-foundry` | Phase 0 reports plus two excluded untracked instruction files after CI commit | `portfolio-migration` intentionally has no upstream; `main` is locally 2 commits ahead of `origin/main` | Do not push or merge until review. |
| `ai-project-workspace-manager` | 6 untracked session files | synchronized | Session data can be accidentally included by broad staging. |
| `ai-workspace-manager` | no checkout | cached ref differs from live remote | History comparison is incomplete until an approved fetch. |
| `claude-switcher-setup` | 8 modified, 2 untracked | no remote/upstream | Highest recovery risk; no remote copy of current work. |
| `social-negative-monitor` | clean | archive unavailable; public cache stale | Current branch name hides lineage divergence. |
| `meeting-media-auto` | clean | 1 local commit ahead | Preserve the unpushed commit before integration. |
| `meeting-media-desktop` | clean | synchronized | Low Git risk; packaging reproducibility remains. |

## Dependency conflict assessment

| Boundary | Finding | Required treatment |
|---|---|---|
| FlowFoundry root vs applications | Root package is dependency-free and Python `>=3.11`; Feedback and Huiying carry substantial app dependencies. | Keep component environments isolated; do not flatten all requirements into the root package. |
| Feedback aliases | `pyproject.toml` and `requirements.txt` dependency declarations match between bundled and standalone source. | Preserve one canonical manifest; later rename the distribution from `social-negative-monitor` deliberately. |
| Huiying common core | Main dependencies align. `defusedxml` is `>=0.7.1` in auto and `>=0.7` in desktop. | Normalize on the stricter lower bound after compatibility testing. |
| Huiying desktop | Adds `cryptography>=46,<50`, pywebview, PyInstaller, and platform binaries. | Keep desktop/build extras separate from the common runtime. |
| Windows lock | `requirements-windows.lock.txt` is explicitly pending and contains no resolved hashes. | Block reproducible release claims until generated on Windows x64 CPython 3.11. |
| Existing Huiying venvs | Both `.venv` interpreters resolve `qrcode` from a user-level `site-packages`; isolated HOME initially caused 115/118 import errors. With that existing user-site made explicit, all tests passed. | Rebuild clean venvs from manifests and prove tests pass with user-site disabled before migration. |
| Workspace/Claude setup | No formal dependency manifests. | Add explicit runtime prerequisites and config schema when extracting adapters. |

## Privacy and public-display assessment

| Area | Finding | Risk/control |
|---|---|---|
| Credential scan | No high-confidence tracked credential, private-key, token, or sensitive filename was found in current trees or sensitive-name history scan. | Repeat with a dedicated history scanner before push; current check is a preflight, not a security certification. |
| Huiying false positives | Five files in each Huiying tree matched an `sk-...` heuristic only because ordinary strings contained `task-...`. | Classified as false positives without printing candidate values. |
| Workspace sessions | `ai-project-workspace-manager` has untracked redacted transcript/session metadata. | Never use broad `git add .`; preserve privately and explicitly exclude from import. |
| Claude setup | Modified session files plus network/proxy repair material may reveal machine-specific topology or operational details. | Manual privacy review and private preservation are mandatory before extracting reusable code. |
| Feedback runtime | Ignored local `data/social_monitor.db` and a SQLite `:memory:`-named artifact exist in the standalone workspace; `.env` is ignored. | Treat databases and exports as user data; do not copy them into the portfolio repository. |
| Meeting media | No sensitive tracked filenames or dirty media files were detected; desktop signing keys and vendor binaries are ignored. | Before migration, scan originals, outputs, diagnostics, EXIF, faces, and event metadata by path without publishing assets. |
| Active private area | `.ai-session/private/` was not read or modified. | Maintain this exclusion throughout migration. |

## Test baseline summary

| Source/product | Baseline | Result |
|---|---:|---|
| FlowFoundry foundation | 51 unittests | Pass |
| Bundled workspace | 24 focused / 38 full Python / 40 EOF / 4 deploy | Pass |
| `ai-project-workspace-manager` | 64 structure / 35 EOF / 4 deploy / 14 Python | Pass |
| `claude-switcher-setup` | No formal tests; 0 tracked shell scripts to syntax-check | No baseline available |
| Bundled Feedback | Ruff + 90 pytest | Pass |
| `social-negative-monitor` | Ruff + 90 pytest | Pass |
| `meeting-media-auto` | 496 unittest | Pass with existing user-site explicitly exposed |
| `meeting-media-desktop` | 546 unittest | Pass with existing user-site explicitly exposed |
| Integrated media/nameplate in FlowFoundry | 3 + 3 unittest | Pass |

## Required gates before actual migration

1. **Freeze identities:** approve the alias map in this report so
   `ai-workspace-manager`, `feedback-analysis-system`, and
   `huiying-media-workbench` are not double-imported.
2. **Preserve dirty work:** create private, recoverable snapshots for
   `claude-switcher-setup` and the untracked workspace session records without
   adding private data to public history.
3. **Refresh refs deliberately:** after approval, fetch source heads into
   namespaced temporary refs and record exact SHAs. Do not merge them directly.
4. **Reconcile lineages:** compare workspace histories and split the Feedback
   archive-only commits into code, documentation, and session-data categories.
5. **Make environments reproducible:** rebuild Huiying venvs with user-site
   disabled and generate the Windows hash lock.
6. **Create migration commits by module:** history import, path integration,
   compatibility adapters, tests, and documentation must be separate commits.
7. **Run the privacy gate before staging:** stage explicit paths only, inspect
   `git diff --cached`, then run tests before each commit.

## Phase 0 Git operation journal

Executed:

```text
main bf6a4ad7157b
  \
   portfolio-migration
     c535d43 fix(ci): align workspace tests with unified runtime
     <documentation commit containing this report>
```

- Created local branch `portfolio-migration` from `main`.
- Created one isolated CI fix commit.
- Created the preparation reports as a separate documentation stage.
- Used `git ls-remote` only for live remote-head inspection.

Not executed:

- `git merge`
- `git mv`
- repository or directory rename
- `git fetch`, push, force push, or pull
- GitHub API operation
- source-repository commit or working-tree edit

## Rollback strategy

- CI code fix: `git revert c535d43c804df634321099a00140d32b1005c035`
- Reports: revert their documentation commit independently after it is created.
- Source repositories: no rollback is needed because no source repository was
  changed by Phase 0.
- `main`: no rollback is needed; its ref remained at
  `bf6a4ad7157b9d8b35b7d7325ed609912c6b01d0`.

No actual file movement, history import, merge, rename, or repository deletion
is authorized by this report. The next action requires explicit confirmation.
