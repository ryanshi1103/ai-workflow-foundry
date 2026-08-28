# Release Day Runbook

Status: **BLOCKED / operator runbook only**. This document grants no authority
to push, merge, tag, publish, deploy, or announce. Every release mutation
requires the release owner's explicit authorization at the relevant gate.

Use [ALPHA_RELEASE_CHECKLIST.md](ALPHA_RELEASE_CHECKLIST.md) for the canonical
gate and [LAUNCH_PACKAGE.md](LAUNCH_PACKAGE.md) for reviewed release copy. Any
stale or blank SHA in a supporting report must be replaced with the exact
approved candidate before use.

## Roles

One person may hold multiple roles for a small Alpha, but each responsibility
must be named in the release record.

| Role | Responsibility | Cannot self-approve |
|---|---|---|
| Release owner | Final go/no-go, explicit authorization, scope and timing | Candidate identity discrepancy or missing mandatory evidence |
| Release operator | Executes authorized GitHub and artifact steps exactly | Their own unexplained command/result mismatch |
| Build verifier | Rebuilds, hashes, installs, and verifies artifacts | Artifact created from an unverified tree |
| Security reviewer | Reviews scans, contents, permissions, known limitations | A high-severity unresolved finding |
| Demo verifier | Confirms every frame and claim against the candidate | Untraceable, private, or simulated media |
| Community lead | Monitors issues, contributor questions, feedback, and incident routing | Public disclosure of a private security report |

## Release record header

Create the release record before any mutation:

```text
Version: 0.2.0-alpha.1
Expected branch/ref:
Approved commit SHA:
Candidate parent(s):
Release owner:
Release operator:
Build verifier:
Security reviewer:
Demo verifier:
Community lead:
Authorization timestamp and channel:
CI run URLs:
Artifact filenames and SHA-256:
External install evidence:
Known limitations reviewed:
Go / no-go decision:
```

Blank identity, role, artifact, or authorization fields keep the release
blocked.

## T-24 hours: before release

The first mandatory gate is **final SHA verification**. Every later CI,
artifact, security, demo, and installation record must resolve to that same
approved object.

### 1. Freeze and identify the candidate

Run read-only checks in the exact release worktree:

```bash
git rev-parse HEAD
git branch --show-current
git status --short
git log -1 --decorate --oneline
git diff --check
```

Confirm the approved SHA, expected branch, clean status, parent commit(s), and
changed-file inventory. Independently verify that protected, integration,
frozen, and unrelated dirty worktrees are untouched.

**STOP:** Any unexpected output, dirty state, branch mismatch, or SHA mismatch.

### 2. Verify CI and focused evidence

- Run the required foundation, workspace, launcher/component, deployment,
  security, and installation checks at the exact SHA.
- Record workflow URL, run ID, job, step, tool versions, and result.
- Classify any failure as code, environment, permission, or infrastructure.
- Do not automatically fix a failed release candidate. Return to review and
  create a new candidate through the normal authorized process.

**STOP:** Missing checks, failed required checks, or results from another SHA.

### 3. Build and verify artifacts

- Build from the clean approved candidate in a documented environment.
- Inventory archive contents and check for credentials, private paths,
  excluded history, caches, or unexpected files.
- Record SHA-256 hashes and provenance for every artifact.
- Install into a fresh environment from the built artifact, not from the source
  tree.
- Obtain at least two external clean-environment successes using only public
  instructions.

**STOP:** Artifact/source mismatch, unexpected content, an undocumented
dependency, or unresolved installation failure.

### 4. Security and legal review

- Run current required security checks and secret scanning.
- Verify approval/permission boundaries and known limitations in public copy.
- Test the private vulnerability-reporting route.
- Confirm license files, notices, dependency obligations, and release contents
  have owner/legal approval appropriate to the project.

**STOP:** Credential exposure, high-severity unresolved finding, unclear
license authority, or unapproved included content.

### 5. Verify launch media and copy

- Complete [DEMO_ASSET_CHECKLIST.md](DEMO_ASSET_CHECKLIST.md).
- Verify captions, alt text, privacy review, fake/live mode labels, and exact
  source SHA.
- Check README, release notes, website, limitations, roadmap, security, and
  install links in a logged-out view or equivalent preview.
- Confirm no material claim depends on future mobile, memory, or autonomy.

**STOP:** Mock screenshots presented as real, media from a different SHA,
private information, broken critical link, or an unevidenced claim.

## T-0: release sequence

Proceed only after the release owner records an explicit **GO** and authorizes
the exact next mutation. The operator should announce each completed gate to the
release channel and stop if observed state differs from the record.

1. Re-run candidate identity and cleanliness checks.
2. Verify the remote candidate ref matches the approved local SHA if a remote
   candidate was authorized and pushed.
3. Under separate explicit authorization, create the approved version tag from
   that exact SHA without rewriting history.
4. Prepare the GitHub Release as a draft using the reviewed launch package.
5. Attach only verified artifacts and publish their hashes/provenance.
6. Verify the draft from a logged-out or independent account: download each
   artifact, check its hash, install it, and run the first workflow.
7. Under explicit publication authorization, publish the GitHub Release.
8. Verify the public release page, tag, artifacts, links, version, limitations,
   and install command.
9. Publish the verified demo and announcement through only the authorized
   channels.

Do not combine authorization for pushing a candidate with authorization for a
tag, GitHub Release, deployment, or announcement. Do not force-push, delete
evidence, rewrite the candidate, or silently substitute an artifact.

## Immediate post-release checks

### First two hours

- Monitor release downloads, installation reports, broken links, security
  reports, and issue volume.
- Reproduce the first reported installation failure from the public artifact.
- Answer with facts and a next update time; do not improvise an unreviewed fix.
- Pin the known-limitations and support route where users can see them.

### First 24 hours

- Classify every report as code, environment, permission, infrastructure,
  documentation, trust, or product fit.
- Confirm all platforms claimed as supported have observed evidence.
- Check that announcements and third-party summaries do not repeat an incorrect
  mobile, memory, autonomy, or provider claim.
- Publish corrections visibly when public copy was wrong.

### First 72 hours

- Summarize install/activation counts from consented reports.
- Rank blockers by severity and affected users.
- Triage first contributions using
  [COMMUNITY_OPERATING_MODEL.md](COMMUNITY_OPERATING_MODEL.md).
- Decide whether to continue promotion, narrow the cohort, or pause.

### First seven days

- Publish an anonymized limitations-first validation update.
- Review maintainer response capacity and security intake.
- Select documentation or packaging fixes with the highest activation impact.
- Keep architecture expansion, providers, mobile, and memory outside the launch
  stabilization scope.

## Pause and incident protocol

Pause promotion immediately for a compromised artifact, hash mismatch,
credential/private-data exposure, unintended destructive behavior, high-severity
security issue, material license problem, or public claim that changes the
product boundary.

Preserve logs and artifacts, move sensitive discussion to the private security
channel, identify affected versions, and let the release owner choose the
documented response. Prefer a clear advisory or superseding release over
history rewriting or silent replacement. Tell users what is known, what remains
unknown, and the next update time.

## Release completion

Release day is complete only when the public tag and release resolve to the
approved SHA, artifacts and hashes verify, public installation succeeds,
critical links and demo media work, monitoring ownership is active, and the
release record contains the final evidence. Publication itself is not the
completion criterion.
