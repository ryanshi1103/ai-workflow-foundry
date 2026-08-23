# Sanitization Report

Date: 2026-08-23
Candidate: `release/v0.2.0-alpha.1-candidate`
Method: allowlist-only snapshot on a new root commit

## Decision

The public candidate uses a new-root snapshot history. It does not descend from
the preserved migration branch or its incident commit, so the historical
session paths and blobs are not reachable from the candidate ref. No existing
branch, tag, remote, frozen release candidate, or evidence archive was changed.

This is candidate construction, not remote incident remediation. Previously
advertised remote refs, pull refs, caches, forks, or clones must still be
handled by the owner-controlled containment process before the old history can
be described as retracted.

## Public allowlist

Only these top-level surfaces were admitted:

- `.github/` community templates and release-readiness workflow;
- `.gitignore`, `LICENSE`, `README.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`,
  `CONTRIBUTING.md`, `SECURITY.md`, and `RELEASE_CHECKLIST.md`;
- `MULTI_AGENT_OPERATOR_GUIDE.md` and `MULTI_AGENT_SECURITY_MODEL.md`;
- `applications/mediaflow/` public contract only;
- `branding/`, `catalog/`, `components/`, `core/`, `schemas/`, `src/`, `tests/`,
  and `workflows/` after the exclusions below;
- curated public files under `docs/`, including the release, license,
  launcher-compatibility, and demo documents;
- deterministic fixtures under `examples/` and `docs/assets/demos/`.

Files not matching this allowlist were never copied into the candidate.

## Explicit exclusions

- all `.ai/`, `.ai-session/`, `.flowfoundry/`, cache, venv, build, and run state;
- all `docs/sessions/` content and all migration/incident evidence reports;
- all unlisted root audit, handoff, post-push, and private-response documents;
- `applications/feedback-intelligence-system/` and its executable catalog,
  capability, workflow, test, and Customer Intelligence demo surfaces;
- credentials, credential stores, `.env` files, keys, certificates, databases,
  logs, exports, real user inputs, and real media.

## Verification gates

The release gate must verify the committed candidate and every reachable
candidate commit for:

1. absence of forbidden prefixes and concrete user-home paths;
2. absence of credential-shaped filenames and private-key markers;
3. a single new-root history with no incident ancestry;
4. clean wheel and sdist entry lists;
5. clean-clone install, tests, validation, and deterministic demo execution.

Command results and the tested source commit are recorded in
`FINAL_RELEASE_REPORT.md`.

## Result

Candidate construction: **PASS**. Historical remote containment remains a
separate owner-controlled gate and is not claimed complete by this report.
