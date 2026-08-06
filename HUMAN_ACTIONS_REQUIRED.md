# Human Actions Required

No item in this file was executed by the overnight run. Complete them only after
reviewing the local branches, reports, privacy audit, and final test matrix.

## Git and GitHub

- **Do not push the current `portfolio-migration` branch.** It contains tracked
  session material in reachable history. Authorize and review a separate
  sanitized publication branch, or explicitly choose another compliant history
  treatment. The current run did not rewrite history.
- Make the Feedback license and monorepo-boundary decision before any public
  FlowFoundry or standalone Feedback push. Apply the choice consistently to the
  application `LICENSE`/`NOTICE`, package metadata, README, catalog, and root
  license boundary.
- After the sanitized FlowFoundry candidate exists, repeat full tests, privacy
  and secret scans, tree/lineage verification, and DeepSeek review.
- Fetch remote refs read-only, confirm fast-forward/PR bases, then push only the
  reviewed sanitized feature branch through the protected repository workflow;
  do not force-push or squash lineage commits.
- Review and push standalone `migration/feedback-intelligence` only after the
  license decision, then decide when to rename the existing
  `feedback-analysis-system` repository in place.
- Review and merge the private MediaFlow migration branches into their intended
  private repositories using normal non-squash history.
- Review and push profile branch `portfolio/profile-layer` at commit
  `d50d98d92ef3a238fd91b32115b81dfb00fd8477`.
- Apply repository pins, topics, descriptions, rename, archive, redirect, and
  default-branch changes manually according to the two GitHub plans.
- Verify old Feedback URLs redirect after any in-place rename; update profile
  links and pins only after the new canonical URL is stable.

## Huiying / MediaFlow release operations

- Provision and verify Android SDK 36 in a clean authorized build environment;
  accept any SDK licenses interactively and run real-device validation.
- Generate a real Windows dependency/hash lock from the approved release
  environment. Do not replace it with a fabricated hash.
- Perform Windows installer build, signing, installation, upgrade/rollback, and
  release validation with protected signing material.
- Review the role of `huiying-desktop-release` as a private release mirror.
- Run authorized provider-enabled and real-media acceptance tests using private
  fixtures; keep all resulting media, logs, and configuration outside public
  version control.

## Releases and deployment

- Create GitHub releases only after branch review, CI verification, versioning,
  artifact provenance, and license checks.
- Perform any real deployment with production credentials in the approved
  operator environment. The migration did not access credentials or deploy.
