# Contributor Journey

Status: contributor-onboarding plan for the public Alpha

## Goal

A new contributor should move from curiosity to one small, evidence-backed pull
request without needing private project history or maintainer-specific tooling.

The journey assumes the owner-approved public Alpha tag exists. Until then,
contributors must not be directed to migration branches or unpublished refs.

## Day 1 — Run the project

Outcome: install the root package and complete one offline workflow.

```bash
git clone --branch v0.2.0-alpha.1 --single-branch \
  https://github.com/ryanshi1103/ai-workflow-foundry.git flowfoundry
cd flowfoundry

python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e .

flowfoundry validate
flowfoundry team plan examples/personal-ai/personal-ai-manager.json
```

Then follow the README's complete offline workflow. The contributor should be
able to explain why fake providers are the default and where run evidence is
stored before moving on.

Day 1 exit check:

- validation output matches the release documentation;
- no credential or real-provider setup was required;
- one plan or run completed without changing tracked files; and
- the contributor can identify SHIPPED, DESIGNED, and FUTURE product surfaces.

## Day 2 — Understand the architecture

Read in this order:

1. [Current Status](CURRENT_STATUS.md) — maturity and known limitations.
2. [Architecture](ARCHITECTURE.md) — module and trust boundaries.
3. [Operator Guide](../MULTI_AGENT_OPERATOR_GUIDE.md) — lifecycle behavior.
4. [Security Model](../MULTI_AGENT_SECURITY_MODEL.md) — permissions, providers,
   Git isolation, and consequential actions.
5. One focused test file matching the intended contribution.

The goal is not to learn the entire monorepo. The contributor should be able to
trace one path: task input → plan → route → run state → review/report.

Day 2 exit check:

- identify the source module and tests for one behavior;
- state whether the change affects network, permissions, secrets, cost,
  persistence, or Git state; and
- know which architecture changes require a design discussion first.

## Day 3 — Fix the first issue

Choose one issue labeled `good first issue` with:

- one user-visible problem;
- exact files or subsystem boundary;
- acceptance criteria;
- a test or documentation verification command;
- explicit non-goals; and
- no requirement for private credentials or billed provider calls.

Create a focused branch, reproduce the problem, make the smallest change, and
run the relevant checks. Do not combine cleanup, refactoring, and feature work.

Day 3 exit check:

- reproduction or evidence is recorded;
- relevant tests pass;
- `git diff --check` passes;
- documentation claims match actual behavior; and
- no secret, private path, or generated personal data enters the diff.

## Day 7 — Submit a contribution

The pull request should answer:

1. What user problem changes?
2. Why is this the smallest useful scope?
3. What are the permission, privacy, network, cost, and Git-state effects?
4. What evidence was run?
5. What remains unsupported?

Maintainer review should provide one clear status: accepted, changes requested,
design discussion required, or blocked with a specific reason.

## Good first issue ideas

| Area | Starter issue | Acceptance evidence | Boundary |
|---|---|---|---|
| Documentation | Add one missing expected-output block to a verified CLI example | Command rerun plus link/fence check | No capability claim changes |
| Examples | Add a small offline task fixture for one existing capability path | Fixture validates and deterministic route is asserted | No live provider or new schema |
| Provider adapters | Improve readiness/error documentation or add an offline envelope fixture | Credential-free test covers unavailable and malformed states | A new live adapter is not a first issue |
| Tests | Add regression coverage for one documented CLI error or recovery state | Focused failing test before fix, passing after | No broad test rewrite |
| UI improvements | Improve launcher wording, alignment, accessibility text, or verified layout examples | Terminal layout tests and updated real/rendered evidence | Do not imply the PWA exists |

Additional useful documentation issues:

- test Python 3.11 install instructions on a clean environment;
- add sanitized Windows/macOS setup evidence when support is verified;
- improve error-message links to troubleshooting sections; and
- check README diagrams and alt text at mobile width.

## Issues that are not good first issues

- cryptographic pairing or approval protocols;
- automatic merge, push, deployment, publication, or financial actions;
- personal semantic memory;
- provider credential handling;
- persisted schema migrations;
- cross-process cancellation and writer-lease semantics; and
- broad architecture rewrites.

These require design review, threat analysis, compatibility planning, and
specialist maintainers.

## Maintainer preparation before launch

- Publish the issue labels listed in [Contributing](CONTRIBUTING.md).
- Seed at least five real good-first issues using the template above.
- State expected response times and supported communication channels.
- Keep a public known-limitations list.
- Close or relabel stale issues rather than leaving newcomers without context.
- Thank contributors through specific review feedback, not automated praise.

## Journey success measures

Track, with consent:

- time to successful development setup;
- percentage completing one offline fixture;
- time from issue assignment to first pull request;
- review turnaround;
- percentage of first pull requests merged or given actionable feedback; and
- contributors returning for a second issue within 30 days.

Do not add hidden telemetry to measure contributor behavior.
