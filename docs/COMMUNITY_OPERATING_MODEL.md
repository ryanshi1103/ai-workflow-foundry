# Community Operating Model

Status: **proposed Alpha operating model**. Response times below are targets for
a limited launch, not contractual service levels. Maintainers should reduce or
pause intake if they cannot meet them responsibly.

## Community objective

Build a small, technically credible community in which a newcomer can install
FlowFoundry, understand its boundaries, report a reproducible problem, and make
a bounded contribution without depending on private maintainer knowledge.

The system optimizes for trusted participants and useful feedback, not maximum
issue volume, stars, or pull-request count.

## First contributor journey

### Day 0 — Discover

The contributor should be able to identify the problem, current Alpha scope,
limitations, license, security-reporting path, and one real demo from the
README.

**Maintainer responsibility:** Keep shipped, designed, and future work visibly
separated. Route potential vulnerabilities to the private process in
[SECURITY.md](../SECURITY.md), never to a public good-first issue.

**Exit condition:** The person can describe FlowFoundry as a local-first AI
coordination layer and can choose whether they want to use, evaluate, or
contribute.

### Day 1 — Install

The contributor follows the public installation path, runs validation, and
completes the deterministic offline workflow before configuring a live
provider.

**Maintainer responsibility:** Publish supported environments, expected output,
common failures, uninstall steps, and a structured installation-report form.

**Exit condition:** The install succeeds, or the failure report contains OS,
Python, artifact/source SHA, command, sanitized output, and the failed step.

### Day 2 — Understand the architecture

The contributor reads the product boundary, canonical architecture, repository
map, trust model, and test organization. They trace one workflow from goal to
evidence and approval.

**Maintainer responsibility:** Identify canonical documents and source entry
points so parallel vision documents do not look like independent architectures.

**Exit condition:** The contributor can locate the relevant module, tests, and
documentation for one issue without a private walkthrough.

### Day 3 — Fix one issue

The contributor selects a labeled, unassigned issue with a bounded acceptance
test. Documentation and example fixes are first-class contributions.

**Maintainer responsibility:** Confirm scope before substantial work, identify
security or compatibility constraints, and avoid silently expanding a
good-first issue.

**Exit condition:** The local change passes the issue-specific command and the
contributor records the result.

### Day 7 — Submit a pull request

The pull request links the issue, explains reason/risk/value, lists test
evidence, and contains no unrelated changes or secrets.

**Maintainer responsibility:** Review against documented acceptance criteria,
distinguish required changes from optional suggestions, and explain the final
decision.

**Exit condition:** The PR is reviewable and receives a clear next action. A
merge is not the only successful outcome; a well-explained close or rescope can
also preserve trust.

See [CONTRIBUTOR_JOURNEY.md](CONTRIBUTOR_JOURNEY.md) for the detailed learning
path and [GOOD_FIRST_ISSUES.md](GOOD_FIRST_ISSUES.md) for the curated backlog.

## Maintainer response targets

| Event | Initial response target | Expected response |
|---|---:|---|
| Private security report | 2 business days | Acknowledge receipt, establish a private contact, and state the next update time |
| New bug or install issue | 3 business days | Triage, request only missing reproduction data, label status |
| New feature request | 5 business days | Confirm product-boundary fit or explain why it is deferred/out of scope |
| First-time pull request | 5 business days | Confirm CI/scope state and give one consolidated review direction |
| Follow-up on active PR | 5 business days | Review changes or communicate a revised time target |
| Community question | 5 business days | Answer, route to canonical docs, or mark that evidence is still missing |

These are public operating targets only after a maintainer roster and coverage
schedule exist. If capacity is exceeded, post a visible notice, label items as
waiting, and narrow the launch cohort instead of leaving contributors uncertain.

## Issue labels

Use a small, orthogonal taxonomy.

### Type

- `type:bug`
- `type:documentation`
- `type:test`
- `type:feature`
- `type:question`
- `type:security` — routing label only; vulnerability details stay private

### Area

- `area:install`
- `area:cli`
- `area:workspace`
- `area:provider-adapter`
- `area:workflow`
- `area:security`
- `area:docs`
- `area:community`

### Difficulty

- `difficulty:first-issue`
- `difficulty:small`
- `difficulty:medium`
- `difficulty:advanced`

### State

- `status:needs-reproduction`
- `status:ready`
- `status:claimed`
- `status:needs-review`
- `status:blocked`
- `status:waiting-for-reporter`

### Trust and release

- `trust:security-sensitive`
- `trust:breaking-change`
- `release:blocker`

Do not encode people, urgency, and architecture into dozens of overlapping
labels. Every `difficulty:first-issue` item must also be `status:ready`, contain
acceptance criteria, and name a test command.

## Contribution review process

1. **Triage:** Confirm the issue is public-safe, reproducible, in scope, and not
   already solved.
2. **Claim:** Assign or acknowledge the contributor; state when the claim
   expires if no update arrives.
3. **Scope check:** Agree on the smallest acceptable change and affected trust
   boundaries.
4. **Implementation:** Preserve unrelated work, include docs where behavior
   changes, and add proportionate tests.
5. **Automated checks:** Run formatting, focused tests, full required CI, secret
   scanning, and packaging checks.
6. **Human review:** Check correctness, safety, user experience, compatibility,
   claims, and evidence.
7. **Decision:** An authorized maintainer merges, requests changes, or closes
   with a documented reason. Protected-branch and release rules still apply.
8. **Follow-through:** Credit the contributor, update the issue, and add release
   notes only if the change is actually included in a release.

No bot or workflow should autonomously merge security-sensitive, release, or
permission-related changes.

## Security reporting

- Put the private reporting mechanism from [SECURITY.md](../SECURITY.md) in the
  README, issue chooser, and contribution guide.
- Public issues should contain no exploit details, tokens, private paths, or
  user data.
- A maintainer moves an accidentally public report to the private channel and
  asks the reporter to remove sensitive material; do not copy it into another
  public thread.
- Acknowledgement is not confirmation of a vulnerability or a promise of a fix
  date.
- Coordinate disclosure, remediation, advisories, and credit with the reporter
  and release owner.

## Community health controls

- Adopt and visibly link a code of conduct before broad promotion.
- Publish who can triage, review, merge, and release.
- Require reason, risk, and test evidence for material changes.
- Keep contributor data minimal and do not add hidden analytics.
- Summarize recurring install and usability problems monthly.
- Close stale claims kindly, while leaving reproducible issues open when the
  problem still exists.
- Mark future/mobile/personal-memory discussions as design work, not requests
  for contributors to implement unapproved architecture.

## Operating readiness gate

The community system is ready for a limited cohort when issue templates and
labels exist, at least ten curated issues are verified, a maintainer rota can
meet the published targets, security reports have a tested private route, and
one outside contributor completes the journey. Until those conditions are
observed, the model is **designed**, not proven.
