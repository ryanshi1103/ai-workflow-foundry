# Final Candidate Checklist

Purpose: **local immutable candidate assembly for review; not public release**
Branch: `release/v0.2.0-alpha.1-final-candidate`
Runtime baseline: `64f1563ba25278c7bceeedf24b7629c6ac463b76`
Candidate SHA: **the commit containing this checklist; resolve with
`git rev-parse HEAD`**
Package version: `0.2.0a1`
Planned release name: `v0.2.0-alpha.1`

## Candidate assembly decision

**PASS for local reviewable-candidate assembly.** The resolved commit identity
and clean-tree results are verified in the final handoff.

**NO-GO for public release.** Artifact, remote CI, independent security/install,
demo-media, owner approval, and external-user gates remain open.

This checklist does not authorize push, merge, tag, GitHub Release, deployment,
announcement, provider expansion, runtime architecture changes, mobile
implementation, or memory implementation.

## Source identity

- [x] Candidate branch was created locally from exact baseline `64f1563...`.
- [x] `git merge-base --is-ancestor 64f1563... HEAD` passed before integration.
- [x] The target branch did not exist before assembly.
- [x] Frozen `release/v0.2.0-alpha.1-candidate` remained clean at `64f1563...`.
- [x] `portfolio-migration` remained at `5dbd149...` with its pre-existing dirty
      state untouched.
- [x] No integration ref, protected ref, remote ref, or tag was created or
      modified.
- [x] Post-commit `git status --short` is empty.
- [x] Post-commit `git rev-parse HEAD^` equals `64f1563...`.
- [x] Post-commit changed-file inventory matches the final candidate report: 62
      files.

The last three boxes are verified after creating the containing commit; their
resolved results belong in the reviewer record and final handoff.

## Included changes

- [x] Product landing and 10-second/10-minute/30-minute README journey.
- [x] Canonical architecture and roadmap references.
- [x] Installation, troubleshooting, FAQ, limitations, and first-user guide.
- [x] Contributor journey, community operation, and five good-first issues.
- [x] Security transparency, trust audit, sanitization/license boundaries, and
      public documentation audit.
- [x] Candidate/release checklists, release-day runbook, status/report evidence,
      launch package, and scorecard.
- [x] Canonical GitHub Release Assistant fixture, demo guide, recording
      checklist, and asset provenance requirements.
- [x] Designed/future mobile and Personal AI documents with explicit non-shipped
      labels.
- [x] Duplicate, obsolete, contradictory, or portfolio-only public documents
      removed.

## Excluded changes

- [x] No runtime or orchestration architecture change.
- [x] No provider addition or adapter expansion.
- [x] No mobile/PWA/native implementation.
- [x] No personal memory or learned optimizer implementation.
- [x] No automatic push, merge, tag, deploy, publish, or financial authority.
- [x] No Feedback Intelligence or Customer Intelligence code/demo.
- [x] No private sessions, credentials, user data, incident archives, or
      preserved migration history.
- [x] No public release operation.

## Tests

All commands ran locally without enabling real providers or installing missing
dependencies from the network.

| Check | Result | Evidence |
|---|---:|---|
| Catalog/capability validation | PASS | 4 components, 2 workflow contracts, 13 capabilities |
| Foundation unittest suite | PASS | 228 tests |
| Workspace unittest suite | PASS | 90 tests |
| Launcher EOF/permission/remote suite | PASS | 40 passed, 0 failed |
| Deploy/profile preservation | PASS | 4 checks |
| Confera Media Skills | PASS | 3 tests |
| Nameplate workflow | PASS | 3 tests |
| GitHub Release Assistant lifecycle | PASS | 4 tasks complete; package pending human approval; 0 assertion errors |
| `git diff --check` | PASS | No whitespace errors before candidate commit |
| Markdown structure and relative links | PASS | 91 Markdown files; 0 errors before commit |
| Remote CI | BLOCKED | Candidate has not been pushed; no remote operation authorized |

## Version consistency

- [x] `pyproject.toml` reports `0.2.0a1`.
- [x] Source `flowfoundry.__version__` reports `0.2.0a1` with `PYTHONPATH=src`.
- [x] Workspace module version reports `0.2.0a1`.
- [x] Changelog uses `0.2.0a1` and maps it to `v0.2.0-alpha.1`.
- [x] README, install guide, launch package, and release documents use
      `v0.2.0-alpha.1` for the planned public release.
- [ ] Final wheel `METADATA` reports `0.2.0a1`.

Final wheel metadata is blocked because the wheel has not been built. The local
environment has the `build` module but lacks `setuptools` and `wheel`; no
network installation was attempted.

## Artifacts

- [ ] Wheel built from this exact candidate SHA.
- [ ] Sdist built from this exact candidate SHA.
- [ ] Artifact filenames, sizes, SHA-256 hashes, and build provenance recorded.
- [ ] Archive contents scanned for excluded/private/unexpected files.
- [ ] SBOM and third-party notices reviewed.
- [ ] Independent reviewer downloads and verifies staged artifacts.

**State: BLOCKED BY ENVIRONMENT AND AUTHORIZED RELEASE WORKFLOW.** Historical
artifacts from `8d1929b...` are explicitly excluded from candidate evidence.

## Security and privacy

- [x] Candidate descends from the sanitized new-root runtime baseline.
- [x] Public documentation rejects AGI, autonomous replacement, shipped mobile,
      shipped personal memory, and universal-AI claims.
- [x] Fake/live provider boundaries and human approval authority are explicit.
- [x] Feedback Intelligence and Customer Intelligence remain excluded.
- [x] No runtime, provider, mobile, or memory implementation was added.
- [ ] Independent final-candidate privacy/security review complete.
- [ ] Historical remote containment and any required credential response have
      owner approval.
- [ ] Final artifacts, advertised refs, and live pull refs independently
      reviewed.
- [ ] Private vulnerability-reporting route exercised by an external reviewer.

**State: PARTIAL / PUBLICATION-BLOCKING.** Local documentation and sanitized
baseline evidence pass; independent and remote gates do not.

## Installation

- [x] Canonical installation guide, troubleshooting, FAQ, and limitations exist.
- [x] First workflow requires no provider credential or billed model call.
- [ ] Final candidate wheel installs with `--no-index` outside source tree.
- [ ] `pip check`, import/version, installed validation, and installed demo pass.
- [ ] Python 3.11 and one newer supported version pass the final artifact path.
- [ ] At least two independent clean installs pass before release review.
- [ ] At least 8/10 first users install within ten minutes before broad launch.

**State: BLOCKED.** Local source/runtime evidence does not substitute for final
artifact installation.

## Demo

- [x] Committed fixture forbids real providers, push, tag, deploy, and publish.
- [x] Four prerequisite tasks complete through deterministic fake providers.
- [x] `package` stops at `skipped_pending_human`.
- [x] Report requires human action.
- [x] No real provider or release action ran during validation.
- [ ] Real 90-second video recorded from an approved candidate.
- [ ] Actual screenshots, terminal GIF, installation recording, captions,
      transcript, poster, and manifests reviewed.
- [ ] Independent technical/privacy/accessibility demo review complete.

**State: EXECUTABLE DEMO PASS; MEDIA GATE BLOCKED.** No fake screenshot may
satisfy the missing-media items.

## User validation

- [x] First-ten simulation and first-100 experiment protocol exist.
- [x] Consent/minimal-data and stop conditions are documented.
- [ ] At least 8/10 users correctly explain FlowFoundry after 30 seconds.
- [ ] At least 8/10 install within ten minutes.
- [ ] At least 6/10 complete the workflow within thirty minutes.
- [ ] At least 90% of activated users identify the approval boundary.
- [ ] No unresolved serious security/privacy/data-loss issue appears.
- [ ] One external contributor completes a reviewable good-first issue.

**State: BLOCKED.** Plans and simulated personas are not external evidence.

## Known limitations

The canonical list is [LIMITATIONS.md](LIMITATIONS.md). Mandatory candidate
warnings include:

- Alpha developer preview, not production software;
- real-provider parity and usage/cost completeness are experimental;
- offline routing identities do not prove cloud calls;
- source installation may require build-backend network access;
- no final wheel/sdist, remote CI, independent install, or demo media yet;
- no automatic merge, push, tag, deploy, publish, spend, or permission widening;
- mobile/PWA and Personal AI OS documents are designed/future;
- complete personal semantic memory and preference learning are not shipped;
- historical remote containment and independent review remain open; and
- Feedback Intelligence and Customer Intelligence are excluded.

## Reviewer handoff

```text
Resolved candidate SHA:
Changed files:
Post-commit tree clean: yes / no
Baseline parent verified: yes / no
Owner decision: pending / approved / rejected
Artifact reviewer:
Security/privacy reviewer:
Install reviewer:
Demo reviewer:
External-validation lead:
Review date/time (UTC):
```

The next step is owner review of this local candidate commit. Do not begin any
remote or publication action from this checklist.
