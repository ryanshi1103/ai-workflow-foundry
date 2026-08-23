# FlowFoundry v0.2.0-alpha.1 Release Checklist

This checklist applies to one exact, owner-approved sanitized candidate SHA.
Nothing may be checked based only on the current dirty `portfolio-migration`
working tree, an older RC report, or a clean wheel built from affected history.

Release decision starts as **BLOCKED**. The release engineer records the SHA,
date, reviewer, command, and evidence link for every completed gate.

## Candidate identity

- [ ] Owner authorized the sanitized publication strategy and candidate branch.
- [ ] Candidate SHA is recorded: `________________________________________`.
- [ ] Candidate branch is not the frozen RC and does not alter preserved evidence.
- [ ] `git status --short` is empty.
- [ ] Candidate diff matches the approved allow-manifest.
- [ ] Python package version is PEP 440 `0.2.0a1`; Git tag and public release
      name are `v0.2.0-alpha.1`; changelog, docs, wheel, and release notes agree.
- [ ] No protected branch, tag, PR ref, or remote was changed outside the
      separately approved publication runbook.

## Privacy and credentials

- [ ] Owner-only classification of prohibited historical session content is complete.
- [ ] Required credential revocation/rotation and service-log review are complete.
- [ ] Approved secret scanner reports zero unreviewed findings in current tree and history.
- [ ] Absolute local path, email/PII, private-media, database, log, and generated-
      artifact scans pass against the exact candidate.
- [ ] No `.ai-session`, `.flowfoundry`, `.ai/preserve`, `.env`, auth, key,
      certificate, customer export, or real user content is present.
- [ ] Candidate wheel/sdist entry lists contain no prohibited paths.
- [ ] Security reviewer signs the sanitized privacy report.

## License and notices

- [ ] Root MIT license and package metadata agree.
- [ ] Workspace Manager, Confera, and Nameplate license boundaries are preserved.
- [ ] Feedback Intelligence license is explicitly selected and applied, or its
      source is excluded with all catalog/README/package claims updated.
- [ ] Copyright holder and publication authority are confirmed.
- [ ] Direct and transitive dependency inventory is reviewed.
- [ ] SBOM and third-party notices are generated for distributed artifacts.
- [ ] No asset, screenshot, dataset, font, or demo input lacks provenance/license.

## Tests

- [ ] `PYTHONPATH=src python3 -m flowfoundry validate` passes.
- [ ] Foundation Python suite passes.
- [ ] Workspace Python suite passes.
- [ ] `core/workspace-manager/tests/test-cc.sh` passes.
- [ ] `core/workspace-manager/tests/test-cc-eof-fix.sh` passes with zero failures.
- [ ] Deployment profile preservation suite passes.
- [ ] Confera and Nameplate suites pass.
- [ ] Feedback Ruff and pytest suites pass when the subtree is included.
- [ ] Offline team run, status, review, report, retry/resume, and cancellation
      smoke tests pass.
- [ ] `git diff --check` and Python compilation pass.
- [ ] Required GitHub Actions pass on the exact candidate SHA.

Record totals:

```text
Foundation:
Workspace Python:
Workspace shell:
Feedback:
Components:
CI URL:
```

## Installation and packages

- [ ] Source install succeeds in a fresh Python 3.11 venv.
- [ ] Source install succeeds in at least one newer supported Python version.
- [ ] One wheel and one sdist are built from the exact candidate.
- [ ] Wheel installs with `--no-index` into a clean venv.
- [ ] Installed `flowfoundry validate` succeeds outside the source tree.
- [ ] `pip check` passes.
- [ ] Package entry scan, hashes, sizes, and build environment are recorded.
- [ ] README and [installation guide](docs/INSTALLATION.md) match observed commands.
- [ ] No package is uploaded to PyPI or GitHub before final owner approval.

## Documentation and positioning

- [ ] README first screen answers what FlowFoundry is, why it exists, and why it
      differs from a one-model chatbot.
- [ ] “AI coordination layer” is the primary positioning.
- [ ] No AGI, autonomous human replacement, unsupported provider, or production-
      readiness claim appears.
- [ ] Implemented, experimental, and planned capabilities match code/tests.
- [ ] Current status, release audit, architecture, roadmap, security, contribution,
      installation, and release-plan links resolve.
- [ ] Temporary sanitized-clone URL placeholder is replaced with the final URL.
- [ ] All Markdown links, Mermaid diagrams, YAML files, and SVG assets validate.

## GitHub community surface

- [ ] Bug and feature templates render correctly.
- [ ] Security template and private vulnerability-reporting link work.
- [ ] Pull request template renders correctly.
- [ ] Code of Conduct and Security Policy are linked from the repository UI.
- [ ] Required checks and branch protection are configured by an authorized owner.
- [ ] Repository description, topics, discussions, and issue labels are reviewed.
- [ ] Maintainer and response ownership are explicit for launch week.

## Demo verification

### Personal AI Manager

- [ ] Plan and offline run complete from a fresh approved checkout.
- [ ] Two-task reviewed path and fake-provider status are visible.
- [ ] Main worktree remains unchanged.

### AI Project Manager

- [ ] Builder → reviewer → tester dependency path completes once.
- [ ] Status, review, and report reopen persisted state.
- [ ] Recording does not imply fake output is production application quality.

### Customer Intelligence

- [ ] License gate is closed or this demo is omitted.
- [ ] Fresh application install and mock workflow succeed without credentials.
- [ ] Only synthetic data appears in DB, export, screenshots, and recording.
- [ ] Original AI candidate and human correction remain distinct.

For every published demo:

- [ ] Poster, recording, transcript, exact commands, expected output, and
      limitations are present.
- [ ] Recording was made from the exact candidate SHA.

## Clean-clone and history verification

- [ ] Fresh unauthenticated single-branch clone checks out only approved history.
- [ ] Fresh mirror clone and advertised refs contain no prohibited ancestry.
- [ ] Live PR/pull-ref metadata does not reach the incident history.
- [ ] Clone install, validation, tests, and demos pass without maintainer-local state.
- [ ] A collaborator verifies the same result independently.
- [ ] Hosting-provider cleanup/support response is complete when required.

## Release artifacts and announcement

- [ ] Release notes list implemented, experimental, planned, known issues, and
      upgrade/rollback guidance.
- [ ] Wheel/sdist hashes and SBOM/notices match reviewed artifacts.
- [ ] Tag points to the approved candidate SHA.
- [ ] GitHub Release is created only after protected review and required CI.
- [ ] Announcement links to the exact tag, not a working branch.
- [ ] Rollback, advisory, visibility, credential, and GitHub Support owners are named.

## Final sign-off

```text
Release decision: BLOCKED / APPROVED
Candidate SHA:
Release tag:
Release engineer:
Privacy/security reviewer:
License/owner approval:
Independent install reviewer:
Decision date:
```
