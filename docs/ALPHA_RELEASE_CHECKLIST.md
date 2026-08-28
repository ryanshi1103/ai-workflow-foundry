# FlowFoundry Alpha Release Checklist

Version: **`0.2.0a1`**
Planned release name: **`v0.2.0-alpha.1`**
Decision: **NO-GO / BLOCKED**
Checklist updated: **2026-08-25**

This is the canonical operational gate for the first public Alpha. It applies
to one exact owner-approved candidate SHA. Checking a box requires an evidence
location, reviewer, and date for that same SHA.

This checklist does not authorize a push, merge, tag, GitHub Release,
deployment, announcement, or protected-ref change.

## Candidate identity

```text
Frozen runtime baseline: 64f1563ba25278c7bceeedf24b7629c6ac463b76
Final documentation-integrated candidate SHA: the commit containing this file;
  resolve locally with `git rev-parse HEAD`
Expected candidate branch/ref: release/v0.2.0-alpha.1-final-candidate
Candidate tree: _____________________________________________________________
Direct parent(s): ___________________________________________________________
Release owner: ______________________________________________________________
Decision date/time (UTC): ___________________________________________________
```

The baseline SHA is not automatically the final release SHA. Documentation
integration changes the Git object and requires all relevant evidence to be
regenerated or explicitly shown to remain applicable.

- [ ] Owner approved the exact final candidate SHA.
- [ ] `git rev-parse HEAD` equals the approved SHA.
- [ ] `git branch --show-current` shows the expected candidate branch.
- [ ] `git status --short` is empty.
- [ ] Parent commits and changed-file inventory match the reviewed candidate.
- [ ] Frozen RC, `portfolio-migration`, protected refs, integration refs, and
      unrelated dirty worktrees are unchanged.
- [ ] Package metadata says `0.2.0a1`; planned tag/release says
      `v0.2.0-alpha.1` everywhere.

**Current state:** READY FOR OWNER REVIEW — local candidate assembly identifies
one commit; owner approval and every publication gate below remain open.

## Tests

Baseline local evidence at `64f1563...` is recorded in
[Final Release Status](FINAL_RELEASE_STATUS.md). It is a regression baseline,
not final integrated-candidate proof.

- [ ] Catalog validation passes: 4 components, 2 workflow contracts, 13
      capabilities.
- [ ] Foundation Python suite passes with the expected test count.
- [ ] Workspace Python suite passes with the expected test count.
- [ ] Launcher compatibility suite passes with zero failures.
- [ ] Deployment/profile preservation checks pass.
- [ ] Included component and workflow suites pass.
- [ ] Offline team plan/run/status/review/report and approval-stop lifecycle
      pass without real providers.
- [ ] Python compilation and `git diff --check` pass.
- [ ] Required GitHub Actions pass on the exact final SHA.
- [ ] Any failure is classified as code, environment, permission, or
      infrastructure; no automatic candidate fix is applied.

```text
Foundation result / log:
Workspace result / log:
Launcher result / log:
Components result / log:
Offline demo result / log:
CI workflow URLs:
Reviewer / date:
```

**Current state:** PARTIAL — baseline local suites are recorded; final-SHA CI
and complete rerun evidence are absent.

## Artifacts and reproducibility

- [ ] Build exactly one wheel and one sdist from a clean checkout of the final
      approved SHA.
- [ ] Record filenames, sizes, SHA-256 hashes, build environment, and source
      provenance.
- [ ] Inspect archive entries for excluded paths, secrets, private history,
      caches, generated state, and unexpected files.
- [ ] Generate/review required SBOM and third-party notices.
- [ ] Install the wheel with `--no-index` outside the source tree.
- [ ] Run import/version, `pip check`, `flowfoundry validate`, and the offline
      first workflow from the installed package.
- [ ] A second person downloads staged artifacts and independently verifies
      hashes and installation.
- [ ] Historical artifacts or hashes from `8d1929b...` are not reused.

```text
Wheel filename / SHA-256:
Sdist filename / SHA-256:
SBOM / notices:
Build provenance:
Independent verifier / date:
```

**Current state:** BLOCKED — current/final-SHA wheel, sdist, hashes, and clean
artifact install do not exist.

## Security, privacy, and legal

- [ ] Current tree and reachable candidate history pass the approved secret,
      private-path, credential-shape, and prohibited-content scans.
- [ ] Historical remote containment and any required credential response have
      an owner-approved decision.
- [ ] Independent reviewer verifies candidate ancestry, advertised refs, live
      pull refs, artifact contents, and sanitization boundary.
- [ ] Approval, permission, provider opt-in, Git isolation, and destructive
      action boundaries match public documentation.
- [ ] Root/component licenses, publication authority, dependency notices, SBOM,
      fonts, screenshots, demo inputs, and other assets have reviewed
      provenance.
- [ ] Feedback Intelligence and Customer Intelligence remain excluded unless a
      separately authorized license decision and full re-audit exist.
- [ ] The private vulnerability-reporting path is tested.
- [ ] No unresolved release-blocking security, privacy, or legal finding exists.

```text
Security scan evidence:
Privacy/history decision:
License/SBOM evidence:
Independent reviewer / date:
Open findings:
```

**Current state:** BLOCKED — local candidate sanitization evidence exists;
independent review, remote containment decision, and final artifact review do
not.

## Installation

- [ ] [Installation guide](INSTALLATION.md), [Troubleshooting](TROUBLESHOOTING.md),
      [FAQ](FAQ.md), and [Limitations](LIMITATIONS.md) match the final artifact.
- [ ] Python 3.11 clean installation completes using only public instructions.
- [ ] At least one newer supported Python version completes the same path.
- [ ] Validation runs outside the source checkout.
- [ ] At least two independent external users complete clean artifact installs
      before release authorization.
- [ ] At least 8/10 observed first users install within ten minutes before broad
      promotion.
- [ ] Uninstall, retry, repeated run-ID, unavailable-provider, and offline-build
      instructions are verified.
- [ ] No installation step requires a provider credential for the offline first
      success.

```text
Environment matrix:
Install timing:
External install evidence:
Documentation corrections required:
Reviewer / date:
```

**Current state:** BLOCKED — local source-install evidence exists, but no final
public artifact or external installation evidence exists.

## Demo

- [ ] The canonical [GitHub Release Assistant](demos/github-release-assistant.md)
      runs from the final candidate in deterministic fake-provider mode.
- [ ] Four prerequisite tasks complete and `package` stops at
      `skipped_pending_human`.
- [ ] The recording uses actual runtime output; no fake screenshot, invented UI,
      or simulated product output is presented as real.
- [ ] Fake/offline mode is visible on screen, in captions, and in narration.
- [ ] The 90-second video, 30-second clip, screenshots, terminal GIF,
      installation recording, captions, transcript, and asset manifests satisfy
      [Demo Recording Checklist](DEMO_RECORDING_CHECKLIST.md) and
      [Demo Asset Checklist](DEMO_ASSET_CHECKLIST.md).
- [ ] Every asset identifies the exact final SHA and passes privacy,
      accessibility, technical, and claim review.
- [ ] No approval, push, merge, tag, deployment, publication, or real-provider
      call is performed by the public demo.

```text
Demo source SHA:
Video / transcript / captions:
Screenshot and GIF manifests:
Technical reviewer / date:
Privacy reviewer / date:
```

**Current state:** BLOCKED — the executable demo lifecycle passes locally, but
the required media package has not been recorded.

## First external users

- [ ] Consent, minimal-data collection, install observation, and follow-up forms
      are ready.
- [ ] First-ten cohort is told that this is an Alpha and which capabilities are
      synthetic, experimental, designed, or future.
- [ ] At least 8/10 correctly explain FlowFoundry after 30 seconds.
- [ ] At least 7/10 install successfully; launch target is 8/10.
- [ ] At least 6/10 complete the first workflow within 30 minutes.
- [ ] At least 90% of activated users identify the human approval boundary.
- [ ] No unresolved serious security, privacy, credential, or data-loss issue
      appears.
- [ ] Failures and interventions are published in an anonymized,
      denominator-preserving report.
- [ ] At least one external contributor completes a reviewable first issue.

```text
Participants attempted:
Correct 30-second understanding:
Ten-minute installs:
Thirty-minute first successes:
Approval-boundary understanding:
Security/trust incidents:
Contributor result:
Research lead / date:
```

**Current state:** BLOCKED — simulations and protocols exist; no external user
has been counted as activation evidence.

## Documentation and launch surface

- [ ] [Authoritative Document Index](AUTHORITATIVE_DOCUMENT_INDEX.md) has no
      broken or competing canonical links.
- [ ] README passes the 10-second understanding, 10-minute install, and
      30-minute first-success tests with external users.
- [ ] Implemented, Experimental, Designed, and Future labels match code and
      evidence.
- [ ] No AGI, human-replacement, universal capability, shipped mobile, shipped
      memory, or hidden-autonomy claim appears.
- [ ] Release copy contains no `TBD`, stale SHA, old artifact hash, or unpublished
      URL presented as live.
- [ ] Five good-first issues are verified against the final candidate and have
      named reviewers.
- [ ] Maintainer and security response ownership is active for launch week.

**Current state:** PARTIAL — local documentation is consolidated; it is not
integrated into an immutable candidate or externally comprehension-tested.

## Final GO / NO-GO

The current score is maintained in [Launch Scorecard](LAUNCH_SCORECARD.md).
Scoring cannot override a blocked mandatory gate.

Release is **GO** only when:

- the score is at least 85/100;
- every section above is complete for the same final SHA;
- no mandatory security, privacy, legal, artifact, CI, installation, demo, or
  user-validation blocker remains; and
- the owner explicitly authorizes each remote/release action.

```text
Final decision: NO-GO / GO
Final candidate SHA:
Score:
Release owner:
Security/privacy reviewer:
Artifact/install reviewer:
Demo reviewer:
External-validation lead:
Decision date/time (UTC):
Remaining warnings:
```

**Current recommendation: NO-GO.** The safe next action is to integrate and
approve the documentation candidate, then run final-SHA CI/build/security and
external install gates. No remote action is authorized by this checklist.
