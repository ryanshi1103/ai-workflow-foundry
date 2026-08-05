# Human Actions Required

No item in this file was executed by the overnight run. Complete them only after
reviewing the local branches, reports, privacy audit, and final test matrix.

## Git and GitHub

- Review DeepSeek results for every pending checkpoint.
- Push `portfolio-migration` normally and open/merge it through the protected
  repository workflow; do not force-push or squash the preserved migration
  lineage.
- Review and push standalone `migration/feedback-intelligence`, then decide when
  to rename the existing `feedback-analysis-system` repository in place.
- Review and merge the private MediaFlow migration branches into their intended
  private repositories using normal non-squash history.
- Review and push profile branch `portfolio/profile-layer` at commit
  `d50d98d92ef3a238fd91b32115b81dfb00fd8477`.
- Apply repository pins, topics, descriptions, rename, archive, redirect, and
  default-branch changes manually according to the two GitHub plans.
- Make an explicit license decision for the standalone Feedback Intelligence
  product before broad distribution.

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

