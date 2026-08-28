# Release Blockers

Status: **BLOCKED_BEFORE_PUSH**

## RC-PRIVACY-001 — reachable session material

- Severity: P0
- Branch: `portfolio-migration`
- Introducing commit: `e3f42ecc8ced2d6621878f070f69d9399a0d7bb8`
- Parent: `d747bd786d10b7d96c2bf6e13f64699a1c409963`
- Evidence: five tracked paths under
  `docs/sessions/20260805-150012-claude-27eec5/`, including
  `conversation.md`, are present in the current tree and reachable history.
- Safety: the primary Codex audit used filename/object evidence and did not
  inspect or reproduce the conversation contents.
- Why a normal fix commit is insufficient: deleting at the tip does not remove
  the ancestor blobs transferred by a push.
- Why automatic remediation stopped: rebase/filter/history rewriting is not
  authorized and would conflict with the preserved merge/lineage constraints.
- Required authority: approve a separate sanitized publication branch or other
  compliant history treatment, preserving the current branch and bundle.
- Required validation after remediation: exact tree comparison excluding only
  approved paths, eight-merge topology audit, complete tests, privacy/secret
  scan, bundle verification and independent review.

External backup before any treatment:

- `~/Projects/.flowfoundry-backups/flowfoundry-pre-rc-sanitization-fd62992.bundle`
- SHA-256:
  `6bd330e2f8ac772accae4d35d1c1a3d05e85b90b27eebc7e697e7606516b46a6`
- `git bundle verify`: complete history for `portfolio-migration` and `main`

## RC-LICENSE-002 — Feedback publication boundary

- Severity: P1/publication gate requiring a human legal/owner decision
- Evidence: standalone has no license; bundled README/catalog say internal use;
  FlowFoundry root is MIT without a subtree exception.
- Required fix: select and consistently apply one model from
  `FEEDBACK_LICENSE_DECISION.md` before public push.
- This run did not select a license or alter copyright notices.

## Non-blocking packaging notes

Checkpoint `3471894` is `APPROVED_WITH_NOTES`. Standard prefix/venv wheel and
editable installations pass; `pip --target`/`--user` layouts are not part of the
current resource-locator contract, and installed-wheel regression coverage
should be added to CI before a package release.
