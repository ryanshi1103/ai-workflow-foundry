# FlowFoundry Final Release Report

Date: 2026-08-23

## Decision

**BLOCKED for public Alpha publication.**

**PASS for the local release-candidate engineering gate.** The candidate is
sanitized, clean, license-bounded, version-aligned, test-green, installable,
and demo-ready. Publication remains blocked only by owner/external gates that
cannot be completed under the explicit no-push, no-merge, no-protected-ref
rules.

## Candidate identity

- Branch: `release/v0.2.0-alpha.1-candidate`
- Tested source commit: `8d1929b85f4cc572813cbf503c22d2b55cb78ebb`
- Tested source tree: `3cd811083a199ffa2a675f9b8ad730b052918307`
- History shape: two commits, with new root
  `0c793a859b4f7d2631c3ea33d1ca8a5566b5a8b4`
- Package version: `0.2.0a1`
- Planned release name: `v0.2.0-alpha.1`
- Candidate status during gate: clean

The commit containing this report is documentation-only and follows the tested
source commit. No source, test, package metadata, catalog, workflow, fixture,
or artifact input changes are introduced by the report commit.

## Blocker closure

| Original blocker | Result | Evidence |
|---|---|---|
| Historical privacy exposure | **PASS for candidate history** | New-root allowlist history; forbidden paths and concrete user-home paths absent from every reachable candidate commit; old remote exposure remains an external gate |
| No sanitized release candidate | **PASS** | Candidate branch created without changing frozen/protected/evidence refs; `docs/SANITIZATION_REPORT.md` |
| Feedback Intelligence licensing | **PASS by exclusion** | Source, catalog manifest, four capabilities, executable contract, CI path, tests, and Customer Intelligence demo excluded; `docs/LICENSE_DECISION.md` |
| Launcher EOF compatibility | **PASS** | Wrapper probe changed from side-effecting import to module-spec lookup; `test-cc-eof-fix.sh`: **40 passed, 0 failed** |
| Missing Feedback test evidence | **PASS by release boundary** | Feedback is not shipped or claimed, so its absent test evidence is not candidate evidence |
| Version mismatch | **PASS** | Package/module metadata and artifacts report `0.2.0a1`; release name remains `v0.2.0-alpha.1` |
| Missing real demo assets | **PASS for demo preparation** | Deterministic input, exact expected plan, normalized verified output, and 90-second walkthrough are committed |

## Sanitization and history evidence

- Allowlist-only candidate assembly admitted 243 files at the root commit.
- `.ai/`, `.ai-session/`, `.flowfoundry/`, `docs/sessions/`, incident/migration
  archives, Feedback source, credentials, databases, logs, and unlisted reports
  were excluded.
- Reachable-object scan found zero forbidden candidate paths.
- Reachable-text scan found zero concrete maintainer-home paths, private-key
  blocks, or common AWS/GitHub/OpenAI token shapes.
- A `--no-local --single-branch --no-tags` clean clone contained two candidate
  commits, one candidate local branch, one matching remote-tracking branch, no
  tags, no forbidden path ancestry, and no unreachable objects.
- The original migration checkout, frozen candidate/evidence, protected refs,
  remotes, and tags were not modified.

These checks prove the candidate boundary. They do not retract old remote PR
refs, caches, forks, or clones.

## Tests

| Gate | Result |
|---|---:|
| Catalog/contract validation | 4 components, 2 workflow contracts, 13 capabilities |
| Foundation Python | 228 passed |
| Workspace Python | 90 passed |
| Launcher EOF/permission/remote compatibility | 40 passed, 0 failed |
| Deploy/profile preservation | 4 passed |
| Confera Media Skills | 3 passed |
| Nameplate workflow | 3 passed |
| Shell syntax and `git diff --check` | passed |
| Deterministic Personal AI Manager plan fixture | exact match |
| Clean-clone foundation suite | 228 passed |
| Clean-clone launcher compatibility | 40 passed, 0 failed |
| Clean-clone offline demo | build and review completed; no commit produced |

Workspace tests generated ignored `.ai-session` state during one local run. The
state was detected, removed, and absent from the committed tree, reachable
history, packages, and final candidate checkout.

## Packages and install

Built with Python 3.14.6 using `build 1.5.0` and isolated setuptools build
environments:

| Artifact | Size | SHA-256 | Scan |
|---|---:|---|---|
| `flowfoundry_ai-0.2.0a1-py3-none-any.whl` | 209501 bytes | `3b75137605efdfe2517af7b510e0bd18f09a65bfa7ff336b7de93d16497d7b40` | 86 files; 0 blocked paths/content |
| `flowfoundry_ai-0.2.0a1.tar.gz` | 213653 bytes | `e37cccfe7345ce8c5bb05fa7c5fe10e5bb98f5a0af852f8180315e618b069364` | 105 files; 0 blocked paths/content |

A fresh venv installed the wheel with `--no-index`; import reported `0.2.0a1`,
`pip check` found no broken requirements, installed validation returned 4/2/13,
and the installed CLI plan exactly matched the deterministic demo fixture from
outside the source directory.

A separate clean clone completed `pip install .`, import/version, validation,
`pip check`, foundation tests, launcher tests, and the offline demo.

The build emitted a non-blocking setuptools warning that the legacy TOML table
form of package-license metadata becomes unsupported in 2027. This is a future
metadata maintenance item, not a `0.2.0a1` failure.

## Demo

The official 90-second script is
`docs/demos/personal-ai-manager-demo.md`. It uses only:

- `examples/personal-ai/personal-ai-manager.json`;
- `docs/assets/demos/personal-ai-manager-plan.json`; and
- `docs/assets/demos/personal-ai-manager-demo-output.txt`.

The demo truthfully shows deterministic planning and fake-adapter execution.
It does not claim personal memory, real-provider quality, automatic edits,
merge, push, publication, or a finished consumer UI.

## Remaining blockers

1. **Historical remote containment and privacy response.** The candidate is
   clean, but previously exposed remote refs/caches are not retracted by a new
   local branch. Owner-only content classification and any required credential
   response must be completed.
2. **Remote and independent evidence.** GitHub Actions has not run on this local
   branch, and no independent privacy/security/install reviewer has signed the
   exact candidate.
3. **Publication authority and host state.** No push, pull request, protected
   review, tag, GitHub Release, anonymous hosted clone, live pull-ref audit, or
   hosting-provider cleanup was authorized or performed.
4. **Release media recording.** The deterministic 90-second walkthrough is
   ready, but a recording from the exact approved hosted candidate is still
   needed if the public launch requires video evidence.

## Exact next actions

1. The owner completes controlled classification of the historical exposure,
   documents whether credential rotation/service-log review is required, and
   completes any required response without placing sensitive details here.
2. An authorized owner publishes only
   `release/v0.2.0-alpha.1-candidate` through the protected review process; do
   not merge or republish the preserved migration history.
3. Run required CI on the published candidate and require green foundation,
   workspace, launcher, component, package-install, privacy-path, and demo gates.
4. An independent security/privacy reviewer verifies candidate ancestry,
   advertised refs, live pull refs, secret-scan results, and the Feedback
   exclusion; an independent installer repeats the clean install and demo.
5. Retire or restrict exposed legacy refs under the approved incident runbook,
   verify an unauthenticated mirror clone and live pull refs, and request
   hosting-provider cache/object cleanup if required.
6. Record the final approved candidate SHA, artifact hashes, reviewers, and
   decision; then create `v0.2.0-alpha.1` and the GitHub Release from that SHA.
7. Record the 90-second demo from the exact approved hosted SHA and publish only
   the deterministic synthetic fixtures and truthful limitation statement.

No push, merge, tag, release, frozen-candidate change, evidence-archive change,
or protected-branch mutation occurred during this hardening run.
