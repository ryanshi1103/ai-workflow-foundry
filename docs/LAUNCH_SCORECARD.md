# Alpha Launch Scorecard

Status: **68/100 — NOT READY FOR PUBLIC ALPHA LAUNCH**
Required score: **85/100 plus zero mandatory BLOCKED gates**
Last scored: **2026-08-25**

The score supports prioritization. It cannot override a missing security,
license, candidate-identity, CI, artifact, external-install, or publication-
authority gate.

## Score summary

| Category | Maximum | Current | Required for launch | Status |
|---|---:|---:|---:|---|
| Product clarity | 20 | 18 | 17 | **READY** |
| Installation | 15 | 10 | 13 | **BLOCKED** |
| Demo | 15 | 8 | 12 | **BLOCKED** |
| Security and trust | 15 | 11 | 13 | **BLOCKED** |
| Documentation | 15 | 14 | 13 | **READY locally** |
| Community readiness | 10 | 5 | 7 | **BLOCKED** |
| Release evidence | 10 | 2 | 10 | **BLOCKED** |
| **Total** | **100** | **68** | **85** | **NO-GO** |

## Product clarity — 18/20

Strong:

- one-sentence local-first coordination-layer definition;
- problem/solution and traditional-assistant comparison;
- current flagship developer use case;
- SHIPPED / DESIGNED / FUTURE boundary; and
- no AGI, replacement, mobile, or memory overclaim.

Missing:

- external 10-second comprehension evidence; and
- one actual coordination-result screenshot above the fold.

## Installation — 10/15

Strong:

- local isolated source install succeeds quickly;
- Python/Git requirements are documented;
- root runtime dependencies are small;
- expected validation output exists; and
- first offline workflow needs no credentials.

Blocked:

- immutable public tag and artifacts do not exist;
- anonymous install is unverified;
- external platform matrix is incomplete; and
- no observed newcomer installation data exists.

## Demo — 8/15

Strong:

- executable five-task fixture;
- verified routing, review, report, and approval stop;
- synthetic limitations are explicit; and
- public story and recording plan are complete.

Blocked:

- no actual 90-second recording, poster, captions, or transcript;
- no actual terminal screenshots in README; and
- no external viewer comprehension test.

## Security and trust — 11/15

Strong:

- fake/offline default;
- explicit real-provider opt-in;
- permission, approval, recovery, and Git isolation documentation;
- secret/credential handling boundaries; and
- honest unknown-cost and incomplete-evidence states.

Blocked:

- current final-candidate remote CI/security evidence is missing;
- independent release security review is missing;
- artifact hashes and clean download/install checks are missing; and
- owner-controlled historical-containment gates remain open.

## Documentation — 14/15

Strong:

- coherent README, architecture, status, installation, security, roadmap,
  mobile, demo, contributor, positioning, and release materials;
- implemented/experimental/planned separation;
- authoritative document index and consolidated Alpha user package;
- trust audit; and
- link/fence validation.

Missing:

- the local immutable candidate is not owner-approved or remotely verified; and
- the external 10-second/10-minute/30-minute journey is not observed.

## Community readiness — 5/10

Strong:

- first-10 simulation and first-100 validation protocol;
- contributor journey;
- five scoped proposed starter issues;
- proposed maintainer response targets; and
- privacy-conscious feedback metrics.

Blocked:

- issues are not published;
- no maintainer response ownership has been exercised;
- no external user or contributor has activated; and
- no community feedback loop has been exercised.

## Release evidence — 2/10

Available:

- local candidate identity and clean frozen worktree;
- previously recorded local test evidence; and
- locally verified documentation and offline-demo lifecycle.

Blocked:

- final integrated candidate SHA;
- current-SHA GitHub Actions;
- reviewed wheel/sdist and hashes;
- clean artifact install;
- external installs;
- demo recording; and
- explicit publication approval.

## Required movement to 85

| Action | Expected score gain | Gate effect |
|---|---:|---|
| Owner reviews and approves the local candidate | +1 documentation | Establishes the approved source for later evidence |
| Run exact-SHA CI, security, build, hash, and artifact-install checks | +9 to +12 | Closes major security/release gates |
| Complete five to ten external installs and workflows | +4 to +6 | Validates installation and first value |
| Record and review the 90-second demo package | +4 | Closes media proof gate |
| Publish scoped issues and maintainer response ownership | +2 | Opens contributor path |

Documentation consolidation and new checklists do not close an evidence gate,
so the score remains 68. Score gains are estimates; re-score from observed
evidence rather than adding points mechanically.

## First external users decision

**READY for a controlled, observed first-ten validation cohort** if each user is
given the owner-approved sanitized candidate and is told that the public tag is
not yet available.

**NOT READY for open, self-service GitHub launch.** A stranger cannot currently
complete the advertised immutable public path or verify remote artifacts.

## GO rule

Set status to GO only when:

- score is at least 85;
- every mandatory gate in the
  [Alpha Release Checklist](ALPHA_RELEASE_CHECKLIST.md) is complete for the same
  SHA;
- no P0/P1 security, privacy, license, or release-integrity issue is open;
- at least 8/10 observed users install and understand the synthetic boundary;
- the demo is recorded and independently reviewed; and
- the owner explicitly authorizes publication.
