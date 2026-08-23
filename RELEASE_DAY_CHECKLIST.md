# FlowFoundry v0.2.0-alpha.1 release-day checklist

Launch-preparation base SHA: `755ec5223dffedd83cbef5efd9edc9821b61deb3`

Approved release SHA: `________________________________________`

Decision owner: `____________________`  Date/time (UTC): `____________________`

This checklist prepares authorized maintainers for publication. It does not
authorize release engineering automation to push, merge, tag, upload, or post.
Stop immediately if the approved SHA changes; rebuild and re-verify every
artifact from the new SHA.

## Stop/go gate

- [ ] Historical privacy exposure has an owner-approved containment decision,
      any required credential response is complete, and no sensitive details are
      copied into public evidence.
- [ ] An independent privacy/security reviewer signed the exact candidate.
- [ ] Feedback Intelligence and Customer Intelligence remain excluded unless a
      separately approved publication license and full re-audit exist.
- [ ] The candidate is clean, allowlist-only, and contains no personal paths,
      credentials, private sessions, or prohibited ancestry.
- [ ] Required CI is green on the exact approved release SHA.
- [ ] Anonymous clone, Python 3.11 install, validation, tests, and the offline
      Personal AI Manager demo pass from the hosted candidate.
- [ ] A named release owner, incident owner, and launch-week support owner are
      available.

If any item above is unchecked, the decision is **BLOCKED**.

## Candidate identity and version

- [ ] Record `git rev-parse HEAD` as the approved release SHA above.
- [ ] Confirm the approved commit is on the reviewed publication branch and not
      on a frozen, evidence, or protected ref.
- [ ] Confirm `git status --short` is empty.
- [ ] Confirm `pyproject.toml` and installed metadata report `0.2.0a1`.
- [ ] Confirm the public tag/release name will be `v0.2.0-alpha.1`.
- [ ] Confirm README, installation, changelog, launch announcement, and demo use
      the same version and canonical repository URL.
- [ ] Replace any remaining publication URL or tag placeholders; record the
      zero-result search in sanitized release evidence.

## CI verification

- [ ] Required GitHub Actions ran on the approved release SHA, not only a local
      branch or previous commit.
- [ ] Foundation validation and Python tests passed.
- [ ] Workspace Python and shell suites passed.
- [ ] Launcher compatibility passed all current checks (40/40 in this
      candidate), including the EOF, permission, and remote-session cases.
- [ ] Included component/workflow suites passed.
- [ ] Wheel-install matrix passed on Python 3.11, 3.12, and 3.13.
- [ ] CI logs were reviewed for accidental secrets, personal paths, or private
      session output before being linked publicly.

Record workflow URLs:

```text
tests:
release-readiness:
privacy/security review:
```

## Artifact build and verification

- [ ] Build one wheel and one sdist from a clean checkout of the approved SHA.
- [ ] Install the wheel with `--no-index` in a new environment outside the
      source tree.
- [ ] Run `pip check`, import/version verification, `flowfoundry validate`, and
      the deterministic plan through the installed CLI.
- [ ] Inspect wheel and sdist entries for excluded/private paths and unexpected
      files.
- [ ] Generate SHA-256 hashes after the final build; do not reuse hashes from an
      earlier documentation commit or candidate.
- [ ] Verify the license, notices, SBOM, and asset provenance required for every
      distributed file.
- [ ] Have a second person download the staged files and independently confirm
      filenames, hashes, version, install, and validation.

Record final artifacts:

```text
flowfoundry_ai-0.2.0a1-py3-none-any.whl  sha256:
flowfoundry_ai-0.2.0a1.tar.gz            sha256:
SBOM/notices:
independent verifier:
```

## Tag creation

- [ ] Confirm the tag does not already exist locally or remotely.
- [ ] Obtain explicit publication approval for the exact SHA.
- [ ] Create an annotated `v0.2.0-alpha.1` tag pointing directly to that SHA.
- [ ] Independently verify the tag target and annotation before any push.
- [ ] Push only the approved tag through the authorized release procedure.
- [ ] Verify the remote tag resolves to the approved SHA from a fresh anonymous
      fetch.

Record:

```text
tag target:
tagger:
verification command/result:
```

## GitHub Release and artifact upload

- [ ] Create a draft GitHub Release from the verified tag.
- [ ] Mark it as a **pre-release**.
- [ ] Use [LAUNCH_ANNOUNCEMENT.md](docs/LAUNCH_ANNOUNCEMENT.md) as the reviewed
      release notes, with the draft warning removed.
- [ ] Upload the final wheel, sdist, hash manifest, required notices/SBOM, demo
      transcript, caption file, and approved poster/recording links.
- [ ] Verify the GitHub-generated source archives resolve from the expected tag.
- [ ] Download every uploaded artifact and recheck its hash before publication.
- [ ] Publish the release only after the artifact and CI checks above are signed.
- [ ] Verify the public release page, install commands, relative documentation
      links, and security-report link while logged out.

Release URL: `____________________________________________________________`

## Demo publication

- [ ] Record [the 90-second script](docs/DEMO_SCRIPT.md) from the exact approved
      tag in a disposable clean checkout.
- [ ] Confirm the plan fixture, fake-provider execution, report, and normalized
      evidence all match.
- [ ] Confirm the video makes no real-provider, personal-memory, autonomous edit,
      merge, push, or polished-UI claim.
- [ ] Run visual privacy review for terminal title, paths, notifications, history,
      metadata, and background content.
- [ ] Publish captions, an accessible transcript, and a legible poster image.
- [ ] Verify the recording URL in a logged-out browser.

Demo URL: `_______________________________________________________________`

## Community announcement

- [ ] Publish the GitHub Release first; use it as the canonical destination.
- [ ] Post the first GitHub announcement and open a focused feedback discussion.
- [ ] Confirm maintainers are available before submitting a Show HN post.
- [ ] Re-read current Hacker News and subreddit rules on launch day.
- [ ] Post to at most one external community at a time and tailor the request for
      that community.
- [ ] Publish the captioned X/Twitter thread only after release and demo URLs are
      stable.
- [ ] Do not request votes, stars, mass reposts, or coordinated engagement.
- [ ] Monitor install failures, security/privacy reports, and misleading claim
      interpretations; pause promotion if a release-integrity issue appears.

Use [GITHUB_GROWTH_PLAN.md](docs/GITHUB_GROWTH_PLAN.md) for approved copy,
channel order, community safeguards, and response metrics.

## Final release record

```text
Decision: PASS / BLOCKED
Approved release SHA:
Tag target:
GitHub Release URL:
Artifact hashes verified:
CI verified:
Privacy/security reviewer:
License/owner approval:
Independent install reviewer:
Demo reviewer:
Release engineer:
Publication time (UTC):
Remaining warnings:
Rollback/incident owner:
```
