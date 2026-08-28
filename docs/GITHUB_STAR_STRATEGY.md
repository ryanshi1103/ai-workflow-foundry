# GitHub Trusted-user Conversion Strategy

Status: **launch strategy**. Stars are a secondary signal; successful installs,
useful workflows, repeat use, and contributions are the intended outcomes.

## Conversion principle

The repository should not ask a stranger to endorse FlowFoundry before giving
them a reason to trust it. The preferred journey is:

`understand -> verify -> try -> obtain value -> return or contribute -> star`

A star is useful when it means “I want to follow or return to this project.” It
is not proof of installation, usefulness, security, or product-market fit.

## Why someone would star

- The coordination problem matches their experience with fragmented AI tools.
- The local-first, evidence-oriented approach is a direction worth following.
- The architecture or security model is useful even before they install.
- The roadmap is credible because shipped, designed, and future work are
  separated.
- They want to revisit a real demo, tutorial, or contribution opportunity.

The repository should earn this response with a concise story, real artifacts,
and transparent limitations rather than a prominent “please star” banner.

## Why someone would install

- They can identify a concrete first workflow, such as preparing a release.
- The quick start has few prerequisites and a deterministic offline path.
- They know what will read or write files and where approval is required.
- Expected output, timing, supported platforms, and uninstall steps are clear.
- The package, source SHA, hashes, and test evidence are verifiable.

The current source-checkout documentation supports internal evaluation. Public
install conversion remains blocked until a published artifact is tested by
people who did not prepare it.

## Why someone would contribute

- The product boundary and canonical architecture are understandable.
- A small issue has a reproducible problem, acceptance criteria, and test
  command.
- Maintainers state when and how an issue or pull request will be reviewed.
- Security-sensitive reports have a private route.
- Contributors can see that documentation, examples, tests, and usability work
  are valued alongside runtime code.

## README conversion review

### First screen

**Current strength:** The README names the coordination shift, defines the
local-first product, compares goal-first coordination with model selection, and
labels the Alpha boundary.

**Needed before launch:** Add one real product capture or terminal GIF, the
verified 90-second demo link, and a single exact-version try command. Keep the
Developer Preview limitation beside that command.

### Screenshots

Use two or three images only:

1. actual goal and plan output;
2. actual evidence/review result;
3. actual approval boundary.

Every image needs alt text and an asset manifest containing its source SHA,
mode, capture command, and sanitization review. Explanatory diagrams are not
screenshots, and rendered UI previews must not be presented as runtime output.

### Examples

Lead with one complete developer example instead of a gallery of possible
futures. The release-assistant example should show input, plan, agent roles,
evidence, approval boundary, result, and the exact command to reproduce it.
Additional student and research scenarios may be described as use cases only
when their shown behaviors are supported by the current runtime.

### Badges

Recommended badges after their targets exist:

- current CI status for the default supported branch;
- license;
- published package/version;
- supported Python versions;
- security policy link.

Do not add star counters, download counters, synthetic “quality” scores,
coverage claims without a maintained report, or release badges before a
release exists. Every badge must link to the evidence behind it.

### Quick start

The first quick start should have three small steps:

1. install an exact Alpha artifact or checked-out candidate;
2. run `flowfoundry validate`;
3. run one deterministic offline example.

Show expected output and elapsed-time target. Provider setup belongs after the
offline success path so credentials are not required to understand the core
workflow.

## Recommended README order

1. Hero, one-sentence product definition, Developer Preview label
2. Why FlowFoundry and the traditional-versus-coordinated comparison
3. Verified 90-second demo
4. Ten-minute quick start
5. Shipped capability list and limitations
6. Simplified architecture diagram
7. Security and approval model
8. Shipped / designed / future roadmap
9. Contribution path and documentation links

This preserves the existing first-screen strength while moving proof and first
use ahead of deep architecture.

## Trusted-user metrics

Measure a small funnel with explicit participant consent:

| Stage | Measure | Why it matters |
|---|---|---|
| Understand | Correct one-sentence explanation after 30 seconds | Positioning clarity |
| Try | Clean install completed or a precise blocker recorded | Distribution quality |
| Activate | Offline workflow completed | First product value |
| Retain | A second workflow within 14 days | Repeated usefulness |
| Contribute | Actionable issue, documentation change, or PR | Community accessibility |

Do not infer activation from stars or page views. FlowFoundry should not add
hidden product telemetry for launch measurement; use consented interviews,
issue forms, and an optional survey.

## Highest-return repository improvements

1. Record and publish the verified flagship demo.
2. Test the release artifact with external clean environments.
3. Add actual screenshots and the terminal GIF with provenance.
4. Make the offline quick start the shortest route to value.
5. Publish maintainer response targets and a curated first-issue queue.

Success is not a particular star count. Success is a growing group of users who
can explain the product, install it, finish a workflow, understand its limits,
and decide that returning or contributing is worthwhile.
