# Open-source Launch Plan

This plan separates product preparation from remote incident remediation. It
does not authorize a push, release, visibility change, ref rewrite, or any
change to the frozen release-candidate evidence.

## Current decision

Use only the new-root sanitized candidate for release review. Do not launch from
the preserved migration history. Feedback Intelligence is excluded and the
launcher EOF/permission suite is green in the candidate.

## Stage 1 — Prepare

### Product surface

- Finalize README, current status, architecture, vision, roadmap, contribution,
  security, demo, and launch documentation.
- Replace demo placeholders with approved reproducible recordings.
- Capture one real launcher screenshot from a clean green build.
- Produce banner, social card, and accessible demo transcripts.
- Prepare issue templates, discussion categories, labels, and maintainer policy.

### Publication safety

- Complete owner-only classification of exposed historical material.
- Apply any required credential rotation and service-log review.
- Authorize and build an isolated sanitized-history candidate while preserving
  the existing incident/RC evidence.
- Resolve the Feedback license or exclude its source from the publication
  candidate with accurate documentation.
- Verify fresh unauthenticated single-branch and mirror clones plus live PR refs.

### Engineering evidence

- Preserve the repaired adaptive-launcher shell contract.
- Run foundation, workspace Python/shell, component, packaging,
  privacy, and offline end-to-end suites in a clean candidate.
- Run remote CI on the exact candidate commit.
- Produce an SBOM/third-party notice set appropriate to shipped artifacts.
- Verify the quick start from a machine/environment not used for development.

Exit condition: one exact candidate SHA is independently reviewed as privacy-
safe, license-clear, test-green, installable, and truthful.

## Stage 2 — Release

### Version decision

The candidate uses PEP 440 version `0.2.0a1`, mapped to release name
`v0.2.0-alpha.1`.

Do not publish `v0.2.0` or `v0.1.0` from this candidate and do not create more
than one “first release” narrative.

### Release checklist

- Tag only the approved sanitized candidate through protected review policy.
- Include implemented/experimental/planned sections in release notes.
- Link test, privacy, license, and packaging evidence without exposing sensitive
  incident identifiers.
- Attach only reproducible, signed/hashed artifacts that passed the documented
  build path.
- Confirm README install URL, badges, screenshots, demo links, and changelog on
  the tag.
- Test installation from the release artifact, not the maintainer checkout.
- Publish a GitHub Release only after all required CI checks pass.

## Stage 3 — Community

- Publish the GitHub release and demo first.
- Announce the engineering problem and offline path on Hacker News.
- Stagger tailored posts for Reddit, X/Twitter, local-first communities, and AI
  research/developer groups.
- Keep a maintainer available for the first forty-eight hours.
- Convert recurring questions into documentation or scoped issues.
- Publish a thirty-day evidence report: install success, failures, contributions,
  and roadmap changes.

Use the message:

> We built a system that helps different AI tools work together under explicit
> permissions, review, budgets, and recovery.

Do not use:

> We built the smartest AI.

## Launch assets

| Asset | Owner decision / evidence needed |
|---|---|
| README and docs | Technical and claim review |
| Banner/social card | Brand and exact-version approval |
| AI Project Manager demo | Offline acceptance and transcript |
| Release artifact | Clean build, SBOM/notices, hashes, install test |
| Release notes | Candidate SHA and all maturity labels |
| Community posts | Links to exact approved release, not working branch |

## Rollback and incident readiness

Before launch, document who can pause releases, change repository visibility,
revoke credentials, contact GitHub Support, and publish a security advisory.
Preserve signed release manifests and the exact source commit. A launch problem
must not trigger an improvised force-push or deletion that destroys evidence.

## Post-launch milestones

1. First ten successful external offline runs.
2. First external documentation or test contribution.
3. Provider adapter contract reviewed by at least two independent implementers.
4. One workflow contributed outside the original portfolio.
5. First patch release produced entirely from the public runbook.
