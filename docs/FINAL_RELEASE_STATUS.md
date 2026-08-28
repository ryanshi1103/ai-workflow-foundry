# Final Release Status

Status date: 2026-08-25
Final candidate branch: `release/v0.2.0-alpha.1-final-candidate`
Frozen runtime baseline SHA: `64f1563ba25278c7bceeedf24b7629c6ac463b76`
Final documentation-integrated candidate SHA: **the commit containing this
document; resolve with `git rev-parse HEAD`; not yet owner-approved**
Package version: `0.2.0a1`
Planned release name: `v0.2.0-alpha.1`

## Decision

**BLOCKED for public publication.**

The frozen runtime baseline is clean and its available offline test suites pass.
The consolidated documentation is assembled on a dedicated local candidate
branch for review. Remote CI, independent security/install sign-off, completed
historical remote-containment decision, owner approval, and final-SHA
wheel/source-distribution evidence are absent.

This report is maintained on a separate documentation branch. It does not
change the frozen candidate, `portfolio-migration`, an integration branch, a
protected ref, or a remote ref.

## Implemented

These capabilities exist in code and have local test evidence:

- **AI workspace management:** project selection, lifecycle operations,
  provider launch profiles, session records, finalization, and recovery.
- **Claude / DeepSeek / Codex coordination:** registry identities, provider
  discovery, bounded adapters, workspace preflight, and deterministic offline
  substitutes. Live provider parity remains experimental.
- **Project discovery:** recent-project discovery, managed/archive policy,
  project metadata, and safe path handling.
- **Permission management:** explicit provider permission profiles, task
  permission checks, and a separate minimum-tool policy.
- **Session recovery:** durable run state, retry/resume, partial-result
  preservation, cancellation records, and workspace-session recovery.
- **Multi-agent planning:** rule-based goal profiling, explicit DAGs, single
  agent, agent-plus-reviewer, and bounded Meeting paths.
- **Review workflow:** stable review decisions, dependency blocking, validation,
  and preserved dissent.
- **Git isolation:** immutable-base managed worktrees, exclusive writer leases,
  candidate diffs, validation, conservative retention, and safe cleanup rules.
- **Approval gates:** scoped, persisted human approval before declared hazardous
  actions. The runtime does not automatically merge, push, deploy, or publish.
- **Cost awareness:** reported token/cost/latency accounting and simple
  project-local performance history. Complete price/quality optimization is not
  implemented.
- **Deterministic workflows:** offline fake providers, contract validation,
  reproducible planning, and bundled reference workflows.

## Experimental

- provider routing optimization beyond explainable heuristics;
- quality/cost selection across providers with incomplete price and usage data;
- long-term memory beyond operational run statistics;
- personal intelligence based on user-owned context and confirmed outcomes;
- an external provider and plugin ecosystem;
- live-provider parity, live bounded-Meeting coverage, and provider upgrade
  compatibility; and
- graphical and cross-device operator experiences.

## Planned

- **Personal AI OS:** a portable, local-first coordination substrate for models,
  tools, context, policies, and workflows;
- **mobile control center:** an approval-first PWA followed by native clients;
- **personalized intelligence:** consent-based preferences, provenance-aware
  retrieval, correction, export, expiry, and forgetting; and
- **autonomous resource optimization:** bounded recommendations and workflow
  planning that remain subordinate to privacy, permission, cost, and human
  approval policies.

FlowFoundry does not claim AGI, human replacement, universal intelligence, or
production-ready autonomous operation.

## Runtime-baseline local evidence

All results below were produced locally against
`64f1563ba25278c7bceeedf24b7629c6ac463b76` without enabling real providers.

| Gate | Result | Evidence boundary |
|---|---:|---|
| Candidate working tree | **PASS** | Empty `git status --short` before and after verification |
| Catalog validation | **PASS** | 4 components, 2 workflow contracts, 13 capabilities |
| Foundation Python suite | **PASS** | 228 tests |
| Workspace Python suite | **PASS** | 90 tests |
| Launcher compatibility | **PASS** | 40 passed, 0 failed |
| Deployment profile preservation | **PASS** | 4 checks |
| Confera Media Skills | **PASS** | 3 tests |
| Nameplate workflow | **PASS** | 3 tests |
| Patch whitespace | **PASS** | `git diff --check` |
| Markdown relative links | **PASS** | 0 broken relative links in committed Markdown |
| Forbidden candidate paths | **PASS** | 0 occurrences across the five reachable candidate commits |
| Common credential shapes | **PASS** | 0 matching files across reachable candidate commits |
| Tracked secret-named paths | **PASS** | 0 |
| Runtime-baseline wheel/sdist build | **NOT VERIFIED** | Host lacks both `build` and `setuptools`; no dependency installation was authorized |
| Runtime-baseline clean install | **NOT VERIFIED** | Depends on a wheel or source build for that exact SHA |
| GitHub Actions | **NOT RUN** | Candidate has not been pushed at this SHA |

Absolute `/home/...` examples remain in one launcher-layout test file. The
current tree contains three occurrences, all using synthetic test placeholders
and none using the active maintainer home name. They are not private local-path
disclosures.

## Release gate

| Gate | State | Required closure |
|---|---|---|
| Exact final candidate identity | Local candidate assembled | Owner reviews the resolved SHA and records approval in the Alpha Release Checklist |
| Local code tests | Pass | Preserve command logs for the exact SHA |
| Build and install | Blocked by local environment | Run the matrix in GitHub Actions or an approved clean environment |
| Security/privacy | Pending external review | Complete historical containment and independent candidate/ref review |
| License/asset provenance | Pending sign-off | Confirm owner authority, dependency notices, SBOM, and media provenance |
| Remote CI | Not available | Push only the approved candidate SHA when explicitly authorized |
| Tag and GitHub Release | Prohibited now | Consider only after all gates pass and separate authorization is given |

## Remaining blockers

1. Documentation consolidation has not been committed into an owner-approved
   final candidate SHA.
2. The cached local `origin/release/v0.2.0-alpha.1-candidate` ref points to
   `32b94345ba9166d8b8b5d3171b132ecee4ecffea`, one commit behind. This has not
   been confirmed with a fetch and must not be treated as live remote state.
3. `FINAL_RELEASE_REPORT.md` has been corrected on the documentation branch to
   distinguish current-SHA local tests from historical `8d1929b...` package
   evidence. That correction is not part of the frozen candidate.
4. Final-SHA wheel, sdist, clean-install, and multi-Python evidence is absent.
5. GitHub Actions and required protected-review checks have not run on a final
   candidate SHA.
6. Historical remote containment, independent privacy/security review, SBOM,
   notices, asset provenance, and owner publication authority remain open.
7. Demo media, first-ten user validation, and contributor-response evidence are
   absent.

## Required next release action

First review and approve or reject the assembled local candidate without
changing runtime architecture. Record the decision in
[ALPHA_RELEASE_CHECKLIST.md](ALPHA_RELEASE_CHECKLIST.md). Only after separate
push authority is given may that exact object be published to a candidate ref
and used for CI/build/install/security gates. A failure stops publication and
is classified as code, environment, permission, or infrastructure; it must not
trigger an automatic fix on the frozen runtime baseline.
