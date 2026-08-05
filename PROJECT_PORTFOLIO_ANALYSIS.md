# GitHub Portfolio Analysis

> Owner: Ryan Shi  
> Analysis date: 2026-08-05  
> Scope: Phase 1 only — read-only inventory, technical assessment, duplication analysis, public-readiness review, scoring, and A/B/C recommendations.  
> No repository was deleted, renamed, moved, archived, merged, or made public during this phase.

## 1. Executive assessment

Ryan's strongest portfolio thesis is already visible:

> **Local-first AI systems that turn model output into reviewable, permissioned, recoverable workflows.**

The portfolio is not short of code. Its main problem is that the same product history is exposed through too many names and repository boundaries. A reviewer currently has to infer that `ai-project-workspace-manager`, `ai-workspace-manager`, `claude-switcher-setup`, and the workspace runtime inside `ai-workflow-foundry` are one product lineage. The same issue exists for feedback analysis, meeting media, and nameplate automation.

The recommended portfolio center is the existing `ai-workflow-foundry` repository, evolved into the flagship AI workspace/workflow platform rather than replaced by another empty repository. Its best supporting projects are the meeting-media product, Feedback Analysis System, and Confera Media Skills.

Key findings:

- Local inventory: 14 Git repositories under `~/Projects`.
- GitHub inventory: 14 repositories owned by `ryanshi1103`: 9 public and 5 private.
- GitHub currently has **no pinned repositories**.
- The GitHub bio already supports the intended positioning: local-first AI workflows, human-reviewable automation, and resilient software.
- The public profile README is directionally strong, but its passing-test counts are now stale and the flagship CI is currently red after the workspace source consolidation.
- The current code demonstrates Claude, DeepSeek, Codex launching, permissions, session logs, recovery, workflow contracts, capability manifests, and human approval boundaries.
- It does **not yet** demonstrate a complete MCP runtime, semantic/long-term agent memory, a model evaluation harness, or a production SaaS architecture. Those should be presented as roadmap items, not current features.
- No current repository is a genuine environmental-engineering AI application. This is a strategic portfolio gap. The Hunan presentation, GRUB theme, VPN scripts, and Taobao prototype should not be relabeled as Industry AI.
- Several local workspaces contain real deliverables, operational state, local configuration, or identifiable data. Their reusable code can be preserved, but those workspaces must never be published as-is.

## 2. Evidence and scoring method

The analysis used:

- root README and project-state documentation;
- tracked and relevant untracked source structure;
- package manifests and dependencies;
- test directories and GitHub Actions configuration;
- licenses, Docker files, and contributor documentation;
- recent Git history, remotes, visibility, topics, and latest Actions results;
- file-level comparisons between suspected duplicate lineages.

Each score is 1–10, except where AI value is genuinely zero.

| Dimension | What a high score means |
|---|---|
| AI value | Real agent/model/tool workflow, not merely AI-assisted development |
| Engineering complexity | Non-trivial architecture, persistence, safety, testing, packaging, or platform work |
| Product potential | Clear user, repeatable workflow, extensibility, and a credible path to adoption |
| GitHub showcase value | Public-safe, understandable, runnable, licensed, tested, visually demonstrable |

Grades are strategic rather than a direct conversion of the total:

- **A — Core showcase:** central to the AI Engineer story and suitable for headline treatment.
- **B — Merge or consolidate:** valuable code that should live under a clearer canonical product boundary.
- **C — Archive/de-emphasize:** preserve the code, but remove it from the active AI portfolio narrative. C does not necessarily mean low engineering quality.

## 3. Local and GitHub repository map

| Local project | GitHub repository or public representation | Current role |
|---|---|---|
| `ai-workflow-foundry` | [`ryanshi1103/ai-workflow-foundry`](https://github.com/ryanshi1103/ai-workflow-foundry) | Public integrated monorepo and strongest flagship candidate |
| `ai-project-workspace-manager` | Private `ryanshi1103/ai-project-workspace-manager` | Operational/private predecessor and deployment source |
| No top-level local checkout | [`ryanshi1103/ai-workspace-manager`](https://github.com/ryanshi1103/ai-workspace-manager); bundled under `core/workspace-manager` | Public portable snapshot of workspace runtime |
| `claude-switcher-setup` | No direct GitHub remote | Legacy launcher/configuration and network-repair workspace |
| `meeting-media-auto` | Private `ryanshi1103/huiying-media-workbench` | Linux/web development workbench for Huiying |
| `meeting-media-desktop` | Private `ryanshi1103/huiying-desktop-release` | Windows/Android commercial release variant |
| `social-negative-monitor` | [`ryanshi1103/feedback-analysis-system`](https://github.com/ryanshi1103/feedback-analysis-system); bundled under `applications/feedback-analysis-system` | Local predecessor name and canonical public feedback product |
| `PhotoTransform` | [`ryanshi1103/oppo-photo-archive`](https://github.com/ryanshi1103/oppo-photo-archive) | Private operational workspace plus sanitized public snapshot |
| `phone-control` | [`ryanshi1103/oppo-phone-control`](https://github.com/ryanshi1103/oppo-phone-control) | Small public ADB automation utility |
| `A` | [`ryanshi1103/print-ready-nameplate-generator`](https://github.com/ryanshi1103/print-ready-nameplate-generator); bundled under `workflows/` | Private real-delivery workspace plus sanitized public generator |
| `Hunan-University-Motivation-PPT` | Private `ryanshi1103/hunan-four-universities-presentation` | Presentation deliverable and generation scripts |
| `System` | [`ryanshi1103/grub-minimal-focus-theme`](https://github.com/ryanshi1103/grub-minimal-focus-theme) | Polished Linux/GRUB side project |
| `VPN` | No GitHub remote; no commits | Operational server/network scripts |
| `taobao-auto-shop` | Private `ryanshi1103/taobao-auto-shop` | Backend architecture prototype |
| No separate top-level checkout | [`ryanshi1103/confera-media-skills`](https://github.com/ryanshi1103/confera-media-skills); bundled under `components/` | Public agent-skill contract package |
| `ryanshi1103` | [`ryanshi1103/ryanshi1103`](https://github.com/ryanshi1103/ryanshi1103) | Personal profile repository |

`_trash-review` is not a Git repository and was not treated as a portfolio project. `PROJECTS_INDEX.md` is an inventory artifact, not a project.

## 4. Duplication and lineage analysis

### 4.1 Workspace/AI operating system lineage

Projects:

- `ai-project-workspace-manager`
- public `ai-workspace-manager`
- `claude-switcher-setup`
- `ai-workflow-foundry/core/workspace-manager`
- `ai-workflow-foundry/src/flowfoundry/workspace`

Evidence:

- The private workspace manager has 15 Python module paths that also exist in the unified FlowFoundry workspace package.
- Of those 15 common modules, 9 are byte-identical and 6 have evolved in FlowFoundry.
- FlowFoundry adds two workspace modules and makes the integrated package the current development path.
- The old `claude-switcher-setup` workspace now primarily contains historical session/configuration material and a mobile network repair note; the launcher capability is already represented in the workspace manager.
- The public `ai-workspace-manager` remains a good sanitized snapshot, but it competes with the flagship for the same story.

Recommendation: one canonical implementation in the flagship repository. Preserve the old histories and unique deployment/network documentation before turning predecessor repositories into read-only redirects or archives.

### 4.2 Meeting-media lineage

Projects:

- `meeting-media-auto`
- `meeting-media-desktop`

Evidence:

- The Linux/web project contains 86 source files under `src`; the desktop project contains 94.
- All 86 Linux/web paths exist in the desktop tree.
- 69 common source files are byte-identical and 17 diverge, mainly desktop behavior, provider/runtime integration, export, networking, web assets, and settings.
- The desktop repository additionally contains Windows packaging, pywebview/PyInstaller support, Android/Gradle code, signing/release material, and vendor artifacts.

Recommendation: one canonical Huiying product repository with a shared `mediaflow` core and explicit platform adapters/distribution targets. Keep release secrets, signing material, licensed vendor binaries, and commercial documents private. A sanitized public architecture/demo should represent the product in the portfolio.

### 4.3 Feedback-analysis lineage

Projects:

- local `social-negative-monitor`
- public `feedback-analysis-system`
- FlowFoundry `applications/feedback-analysis-system`

Evidence:

- The local predecessor and bundled FlowFoundry copy share 53 relative files.
- 52 of those files are byte-identical; the single changed file is presentation/integration documentation.
- The local repository already points to the renamed public product lineage.

Recommendation: `feedback-analysis-system` is the only product name and canonical public identity. Preserve Git history, then retire the `social-negative-monitor` name.

### 4.4 Nameplate lineage

Projects:

- local `A`
- public/bundled `print-ready-nameplate-generator`

Evidence:

- `A` is a real delivery workspace with multiple scripts, real participant lists, PDFs, PPTX/DOCX files, and operational notes.
- The public project contains the reusable generalized generator, fictional input, safe filename logic, tests, and an MIT license.
- The public copy is intentionally not a full mirror, which is the correct privacy boundary.

Recommendation: keep the private delivery workspace private. Maintain only the generalized, sanitized generator as public code. Never merge real names or delivery files into the public repository.

### 4.5 Device-automation lineage

Projects:

- `PhotoTransform` / public `oppo-photo-archive`
- `phone-control` / public `oppo-phone-control`

These are related by device domain but not duplicate implementations. Photo archive is a transactional data-integrity workflow with optional local vision classification; phone control is a small plan/apply/restore ADB configuration tool. They can share one portfolio category and documentation style without forcing their code into one executable.

## 5. Project-by-project analysis

### 5.1 Core agent and workspace projects

| Project | Purpose and stack | Value, overlap, and public suitability | Scores (AI / Eng / Product / GitHub) | Grade |
|---|---|---|---:|---|
| `ai-workflow-foundry` | Python 3.11 monorepo; CLI, component catalog, JSON schemas, capability registry, workflow contracts, workspace runtime, Shell/systemd assets, unittest, GitHub Actions | Best architecture narrative and canonical integration point. Contains workspace, feedback, media-skill, and document-workflow lines. Public-safe and MIT, but currently lacks a compelling demo and its workspace CI job is red after source consolidation. | 9 / 8 / 8 / 7 = **32** | **A** |
| `ai-project-workspace-manager` | Python + Shell + systemd; multi-tool launcher, project lifecycle, session logs/redaction, recovery, maintenance, deployment | Substantial engineering, but mostly duplicates the unified workspace package and is private/operational. No `pyproject.toml`; public story would conflict with the flagship. | 8 / 8 / 7 / 4 = **27** | **B → flagship workspace core** |
| public `ai-workspace-manager` | Sanitized Python/Shell snapshot with MIT license, tests, CI, launcher, permission modes, recovery | High-quality public component and green CI, but duplicates the flagship's core product claim. Keep temporarily as a compatibility/release mirror, then redirect or archive after canonical packaging exists. | 8 / 7 / 7 / 8 = **30** | **B → flagship workspace core** |
| `claude-switcher-setup` | Local config, historical launcher/session material, a Clash script, and mobile network repair documentation | Unique operational notes may be worth preserving, but it has no package, tests, license, or remote and is no longer an independent product. It contains local configuration and uncommitted state. | 4 / 2 / 2 / 1 = **9** | **B → extract unique docs, then archive** |
| `confera-media-skills` | Ten agent skills, manifests, schemas, tool/privacy policies, human-review gates, Python contract tests | Strong evidence of agent-boundary design and human-in-the-loop engineering. It is public, MIT, CI-green, focused, and useful as a separately installable skill pack even when cataloged by the flagship. It is a contract package, not a full media runtime. | 8 / 6 / 6 / 8 = **28** | **A** |

### 5.2 AI automation applications

| Project | Purpose and stack | Value, overlap, and public suitability | Scores (AI / Eng / Product / GitHub) | Grade |
|---|---|---|---:|---|
| `meeting-media-auto` | Python, FastAPI, Uvicorn, Jinja, SQLite, FFmpeg, local media pipeline, DeepSeek provider routing, immutable candidates, review/approval gates, systemd; about 130 Python files and 60 test files | Strongest applied product: clear users, real workflow, model/provider boundaries, recovery, local fallback, and extensive testing. Source is private, large, and tied to operational/product material; showcase via a sanitized public demo or case study. | 8 / 9 / 9 / 5 = **31** | **A** |
| `meeting-media-desktop` | Shared media core plus pywebview, PyInstaller, Windows PowerShell/Inno Setup, Android Java/Gradle, signing and release assets; about 151 Python files and 68 test files | High complexity and product value, but 69 of 86 common source files are identical to the workbench. Treat it as platform/release targets inside one canonical product, not a second portfolio product. | 7 / 9 / 8 / 4 = **28** | **B → Huiying canonical product** |
| `feedback-analysis-system` | Streamlit, SQLAlchemy, Pydantic, pandas, Plotly, OpenAI-compatible DeepSeek client, Apify connector, SQLite, pytest, Ruff | Clear AI application with import → model candidate → human review → audit → export. Public and CI-green with mock mode. Missing a detectable license, architecture diagram, hosted/demo media, and a production backend path. | 8 / 7 / 8 / 7 = **30** | **A** |
| local `social-negative-monitor` | Same Python application lineage under the old product name | 52 of 53 shared files match the bundled canonical application. The old name narrows the product and creates confusion. Preserve history, use only `feedback-analysis-system` publicly. | 7 / 7 / 7 / 4 = **25** | **B → Feedback Analysis System** |
| `PhotoTransform` | Python transactional photo archive, SHA-256 verification, atomic promotion, explicit deletion gate, local visual-model classification, state/reports, one helper test file | Excellent local-first safety case, but the operational tree is 1.7 GB and contains real personal archive state, paths, reports, and uncommitted work. Never publish this workspace as-is. | 5 / 8 / 7 / 2 = **22** | **B → sanitized device automation app** |
| public `oppo-photo-archive` | Sanitized Python snapshot of the transactional archive workflow; MIT and CI-green | Good supporting engineering utility, but only moderate AI value and not a headline project. Keep as an unpinned public module or consolidate under an automation-app collection. | 4 / 7 / 7 / 8 = **26** | **B → device automation collection** |
| `phone-control` / `oppo-phone-control` | Shell ADB optimize/restore scripts with device-model checks; early Python scaffold | Useful reversible automation, but small, mostly non-AI, and the public repository has no detected license or meaningful CI workflow. Combine at the portfolio/documentation level with device automation. | 1 / 4 / 4 / 5 = **14** | **B → device automation collection** |
| `A` | Python/LibreOffice/PyUNO document generation plus real CSV lists and PDF/PPTX/DOCX deliverables | Real-world automation value, but the workspace contains identifiable names and client-like deliverables and has extensive uncommitted state. Only generalized code belongs in public. | 1 / 5 / 6 / 1 = **13** | **B → sanitized nameplate workflow** |
| public `print-ready-nameplate-generator` | Generalized CSV-to-editable-PPTX generator, deterministic geometry, safe filenames, unittest, MIT, CI | Clean reusable workflow and strong proof of deterministic automation, but low direct AI value. Keep as a FlowFoundry reference workflow rather than a headline product. | 1 / 5 / 6 / 8 = **20** | **B → flagship reference workflows** |

### 5.3 Backend, systems, content, and legacy projects

| Project | Purpose and stack | Value, overlap, and public suitability | Scores (AI / Eng / Product / GitHub) | Grade |
|---|---|---|---:|---|
| `taobao-auto-shop` | FastAPI, async SQLAlchemy/PostgreSQL, Redis, Celery, AES-GCM inventory encryption, Docker Compose, HTML dashboard | Useful backend architecture practice and aligned with future SaaS learning, but currently a private prototype with no tests, CI, package metadata, or license and no implemented AI value. Extract generic backend patterns into a future AI application backend; do not present unverified commerce claims publicly. | 1 / 7 / 6 / 3 = **17** | **B → future AI backend foundation** |
| `System` / `grub-minimal-focus-theme` | Shell, GRUB2 theme assets, ImageMagick/PF2 generation, safe install/uninstall/rollback, validation, GPL-3.0 | A polished systems-engineering project with strong documentation and public safety. It is nevertheless off-thesis for an AI Engineer portfolio. Preserve publicly if desired, but unpin and move to an archived/side-project tier. | 1 / 8 / 6 / 8 = **23** | **C — side-project archive** |
| `Hunan-University-Motivation-PPT` | Python-pptx, Pillow, image download/source tracking, 28-page presentation, 41 public images | Competent content automation and provenance work, but it is private, media-heavy, has no test suite/license, and does not demonstrate AI application engineering. Preserve the deliverable privately. | 1 / 5 / 4 / 2 = **12** | **C — private archive** |
| `VPN` | Bash deployment/rollback, Xray/Hysteria/Nginx/systemd, Python Mihomo config generation | Operationally complex but security-sensitive. The workspace has no commits, remote, tests, or license and its README contains real infrastructure addresses. Never publish as-is. | 0 / 6 / 4 / 0 = **10** | **C — private operational archive** |
| `ryanshi1103` profile repo | Personal GitHub profile README and portfolio narrative | Required portfolio infrastructure. The bio is aligned, but there are no pinned repos, no demo links, and the README contains stale test-count claims after the latest consolidation. | 5 / 2 / 9 / 7 = **23** | **A-support — keep and rewrite later** |

## 6. Recommended A/B/C portfolio set

### A — core showcase

1. **`ai-workflow-foundry`** — flagship AI workspace/workflow platform.
2. **Huiying / meeting-media product** — strongest applied AI automation product; publish a sanitized demo/case study while keeping protected source private.
3. **`feedback-analysis-system`** — public end-to-end AI application.
4. **`confera-media-skills`** — focused AI Agent/skill-contract showcase.
5. **`ryanshi1103` profile repository** — portfolio navigation layer, not a product pin by itself.

The desired future Industry AI project is not in this list because it does not yet exist.

### B — merge or consolidate

| Source | Destination concept | Preserve before consolidation |
|---|---|---|
| `ai-project-workspace-manager` | Flagship workspace core | Git history, deployment scripts, private operational notes kept private |
| public `ai-workspace-manager` | Flagship workspace core/release mirror | Releases, CI, sanitized docs, compatibility path |
| `claude-switcher-setup` | Flagship networking/deployment documentation where genuinely reusable | Unique repair note and safe configuration logic only |
| `meeting-media-desktop` | Canonical Huiying repository as Windows/Android distribution targets | Platform-specific code, licensing audit, build/signing docs |
| `social-negative-monitor` | `feedback-analysis-system` | Git history and any newer local-only changes |
| `PhotoTransform` + `oppo-photo-archive` | Device/photo automation application | Sanitized transactional engine; never real media/state |
| `phone-control` | Device automation collection | Verified optimize/restore scripts and model checks |
| `A` + `print-ready-nameplate-generator` | FlowFoundry deterministic document workflows | Generalized generator only; never real names/deliverables |
| `taobao-auto-shop` | Future AI application backend foundation | Generic FastAPI/Postgres/Redis/Celery patterns after tests and threat review |

### C — archive or de-emphasize

1. **`Hunan-University-Motivation-PPT`** — preserve privately as a completed deliverable.
2. **`System` / `grub-minimal-focus-theme`** — preserve as a polished systems side project, but remove from AI headline/pins.
3. **`VPN`** — private operational archive only; never publish as-is.

Archive means GitHub's reversible archive state or a clearly labeled private legacy tier. It does not mean deleting local code or history.

## 7. Public-readiness assessment

### Public-safe with targeted fixes

- `ai-workflow-foundry`: fix the stale workspace-runtime CI job and align wrapper/deployment tests with the unified Python package; add an executable demo.
- `feedback-analysis-system`: add an explicit license decision, architecture diagram, demo media, and roadmap.
- `confera-media-skills`: already strong; add a short end-to-end example showing a skill result consumed by trusted code.
- `ai-workspace-manager`: currently public-safe, but strategically redundant.
- `print-ready-nameplate-generator`: public-safe and intentionally sanitized.
- `oppo-photo-archive`: public-safe and intentionally sanitized.
- `oppo-phone-control`: add license, real tests/CI, and remove the unused Python scaffold or label it more clearly.
- `grub-minimal-focus-theme`: public-safe but off the core AI narrative.

### Private or case-study only

- `meeting-media-auto` and `meeting-media-desktop`: source/release repositories can remain private; create a sanitized public demo, architecture case study, screenshots, and synthetic-media walkthrough.
- `ai-project-workspace-manager`: private operational predecessor; expose only portable code through the flagship.
- `taobao-auto-shop`: keep private until tests, licensing, threat modeling, and real integration boundaries exist.
- `Hunan-University-Motivation-PPT`: keep private due to media/licensing and portfolio-fit concerns.

### Never publish as-is

- `A`: real participant names and generated deliverables.
- `PhotoTransform`: personal photo-archive state, paths, reports, and a large operational workspace.
- `VPN`: real server addresses and operational deployment details.
- `claude-switcher-setup`: local configuration/session state and machine-specific repair material.

## 8. Repository quality gaps observed

| Area | Current evidence | Portfolio implication |
|---|---|---|
| Naming | Multiple names for the same lineage (`ai-project-workspace-manager`, `ai-workspace-manager`, FlowFoundry workspace; `social-negative-monitor` vs feedback analysis) | Reviewers cannot quickly identify canonical products |
| README consistency | Strong READMEs exist, but architecture, demo, and roadmap sections are inconsistent | A shared README contract is justified in Phase 3 |
| Packaging | FlowFoundry, feedback, and meeting projects use `pyproject.toml`; workspace predecessor and several prototypes do not | Consolidate package ownership before adding more manifests |
| Licenses | MIT/GPL are clear on several public repos; public feedback and phone-control have no detected license | Public reuse rights are ambiguous |
| Contributing | No inspected project has a complete `CONTRIBUTING.md` | Add first to A-grade public repos only |
| Tests | Strongest in meeting, feedback, workspace, and FlowFoundry; weak/absent in phone, Taobao, Hunan, VPN | Do not apply a blanket pytest badge to projects without meaningful behavior tests |
| CI | Public component snapshots are green; FlowFoundry's latest run fails in the stale workspace shell test; several repos have no Actions | Fix flagship CI before promoting it |
| Docker | Only the Taobao prototype has Docker Compose | Containerize network services/apps where useful; do not force Docker onto local CLI or document-generation tools |
| Demo | No public repository has a strong hosted or recorded product demo/homepage | This is a larger portfolio weakness than adding more repositories |
| GitHub profile | Bio and README are aligned; no repositories are pinned | Pin selection should follow the A-grade architecture after confirmation |

## 9. Capability truth table for the intended flagship

| Intended capability | Current status | Evidence-based interpretation |
|---|---|---|
| Claude / DeepSeek / Codex | Implemented | Unified launcher, provider selection, Codex profiles, and project lifecycle integration exist |
| Permission system | Implemented | Explicit modes and elevated-access confirmations exist |
| Project lifecycle | Implemented | Create/open/select/finalize/maintain/recover paths exist |
| Logs and recovery | Implemented | Session metadata, redaction, transcript handling, interrupted-session recovery |
| Agent workflow contracts | Partial but real | Capability registry, workflow schemas, approval gates, and skill manifests exist; a general workflow runner is not complete |
| MCP | Gap | CLI passthrough/recognition exists, but no first-class MCP server/client registry, lifecycle, policy, or test harness was found |
| Memory | Partial | Session/project records provide operational memory; no semantic long-term memory, retrieval layer, or memory evaluation exists |
| Tool calling | Partial | Confera/FlowFoundry define bounded capabilities and tool policies; a general trusted tool-execution runtime is still roadmap work |
| Evaluation | Gap | Unit/integration/contract tests are strong, but there is no model/agent evaluation dataset, scoring harness, regression threshold, or trace comparison system |
| FastAPI backend | Implemented in Huiying | Not yet part of the flagship platform core |
| PostgreSQL / Redis | Prototype only | Present in Taobao backend prototype, not validated as an AI application architecture |
| Docker / CI/CD | Partial | GitHub Actions and systemd deployment exist; Docker Compose is isolated to the Taobao prototype |
| SaaS architecture | Gap | No validated multi-tenant auth, billing, tenant isolation, hosted deployment, or production observability |
| Environmental Engineering + AI | Gap | No current project supports this portfolio claim |

## 10. GitHub profile-specific finding

For a personal GitHub account, the profile README is rendered from the public repository named exactly after the username: `ryanshi1103/ryanshi1103`, with its root `README.md`. That repository already exists and is the correct target.

`.github/profile/README.md` is the organization-profile mechanism, not the normal personal-profile mechanism. Unless an organization is created later, Phase 3 should improve the existing `ryanshi1103/README.md` instead of adding an unused personal `.github/profile/README.md` path.

## 11. Decisions required before Phase 2

No architectural mutation should begin until these choices are confirmed:

1. **Flagship identity:** retain the established `FlowFoundry AI` name, or rename the existing repository to a clearer `ai-workspace-platform`. Creating another parallel repository is not recommended.
2. **Huiying public strategy:** open-source a sanitized core, or publish only a case-study/demo repository while keeping the product source private.
3. **Component repository policy:** keep `ai-workspace-manager`, `confera-media-skills`, `feedback-analysis-system`, and nameplate as synchronized release mirrors, or redirect/archive selected duplicates after the flagship is stable.
4. **C-grade policy:** confirm whether polished but off-thesis work such as the GRUB theme should be GitHub-archived or simply unpinned and labeled as a side project.
5. **Industry AI direction:** select a real environmental-engineering problem, dataset, and user before creating a repository.

## 12. Phase 1 completion boundary

This report is the only project file created in Phase 1. No destructive operation or GitHub write was performed. The next phase should start only after the A/B/C classification and five decisions above are approved or adjusted.
