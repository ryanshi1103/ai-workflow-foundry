# Public Release Plan

Target: **FlowFoundry v0.2.0-alpha.1**  
Current state: **local candidate hardening in progress**  
Authority: this plan does not authorize push, merge, tag, visibility change,
history rewrite, protected-branch change, credential action, or GitHub Release.

The Git tag/release name `v0.2.0-alpha.1` maps to Python package version
`0.2.0a1`. Candidate package metadata is aligned and must be rebuilt and tested
from the exact committed source.

## Phase 1 — Private review

### Goal

Produce one clean, trustworthy, immutable candidate that external developers can
review without receiving the known incident history or ambiguous-license source.

### Work

1. Complete controlled owner-only classification of the historical session
   material and any required credential response.
2. Authorize a sanitation method, exact ref scope, backup, allow-manifest, and
   rollback procedure without changing the frozen RC evidence.
3. Keep the unlicensed Feedback Intelligence implementation excluded unless a
   later owner-approved license decision creates a new candidate.
4. Reconcile the adaptive Launcher behavior with the EOF/permission regression
   suite.
5. Assemble productization docs, GitHub templates, demos, and package changes on
   a separate authorized publication candidate.
6. Run the complete [release checklist](../RELEASE_CHECKLIST.md).
7. Invite three to five private reviewers covering installation, security/privacy,
   provider architecture, documentation, and one first-time-user workflow.

### Exit criteria

- exact candidate SHA and clean working tree;
- zero unreviewed privacy/secret/license findings;
- all mandatory local and remote tests green;
- fresh anonymous clone and mirror verification green;
- private reviewers can install, validate, and run two offline demos;
- owner approves public visibility and release tag.

## Phase 2 — v0.2.0-alpha.1

### Goal

Publish a truthful developer preview that proves coordination and invites scoped
contributions without claiming a complete personal AI operating system.

### Release contents

- root source package and validated contracts;
- wheel and sdist with hashes, SBOM, and third-party notices;
- README, current status, release audit, installation guide, architecture,
  security, contribution, roadmap, and release notes;
- Personal AI Manager and AI Project Manager offline demos;
- no Customer Intelligence demo in this candidate;
- known limitations and compatibility matrix.

### Release message

> FlowFoundry is a local-first AI coordination layer for planning, routing,
> reviewing, and recovering bounded workflows across AI and deterministic tools.
> The first Alpha focuses on coordination evidence—not on building the smartest
> model or replacing human judgment.

### Operations

- tag only the approved SHA through protected review policy;
- publish GitHub Release before community posts;
- verify the release URL, install commands, artifacts, and demo links from a new
  environment;
- keep an owner available to pause the release or publish an advisory;
- do not upload experimental real-provider logs or private demo inputs.

### Exit criteria

- release assets install and validate;
- no P0/P1 security, privacy, or license finding;
- release notes and repository UI render correctly;
- first external install issue can be triaged from documented evidence.

## Phase 3 — Community feedback

### Goal

Learn whether external developers understand, install, and extend FlowFoundry;
do not optimize primarily for stars or agent-count demos.

### Sequence

1. Publish the first announcement with one architecture diagram, one offline
   demo, exact install command, limitations, and contributor invitation.
2. Share to Hacker News first, then stagger tailored posts for relevant Reddit,
   X/Twitter, local-first, agent-framework, and research communities.
3. Label and respond to issues within a stated maintainer window.
4. Convert repeated confusion into docs/tests before expanding scope.
5. Hold a public design discussion for the provider adapter contract.

### Measures

- ten successful external fresh installs;
- median time to first `flowfoundry validate`;
- offline demo completion rate;
- number and quality of reproducible bug reports;
- first external documentation/test contribution;
- repeat contributors;
- provider/workflow conformance proposals;
- privacy or trust-boundary misunderstandings.

### Exit criteria

- at least ten independently reported successful installs;
- all release-blocking Alpha bugs fixed in patch releases;
- no unresolved critical disclosure;
- roadmap updated from evidence rather than launch speculation.

## Phase 4 — Stable release

### Goal

Promote only a narrow, documented contract to stable use. Stability does not
mean every personal-AI roadmap feature is implemented.

### Required evidence

- supported Python/platform matrix with repeatable CI;
- versioned provider/workflow contracts and migration policy;
- public conformance fixtures for at least three independently useful adapters or
  deterministic capabilities;
- reliable cancel/resume/recovery and writer-isolation evidence;
- stable persisted formats or documented migrations;
- security response, release, rollback, and deprecation policies exercised at
  least once;
- complete license/SBOM/notice process;
- two releases produced entirely from the public checklist;
- external workflows beyond the original portfolio.

### Stable positioning

FlowFoundry stable should promise a dependable coordination substrate: explicit
capabilities, minimum-path planning, bounded execution, human authority,
evidence, and recovery. Personal semantic memory, adaptive optimization, and a
cross-device Intelligence OS may remain separate experimental layers.

## First public announcement draft

**Title**

> FlowFoundry v0.2.0-alpha.1 — a local-first coordination layer for AI tools

**Body**

> Most AI workflows start by choosing one model. FlowFoundry starts with the
> goal, required capabilities, permissions, privacy, and review needs, then
> chooses a bounded path across AI or deterministic tools. The first Alpha ships
> an offline-safe planner/team runtime, recoverable state, human approval gates,
> and Git-isolated writer candidates. It does not claim AGI, autonomous human
> replacement, or universal provider support.
>
> Try the first command: `flowfoundry validate`. Then run the Personal AI Manager
> plan or the synthetic AI Project Manager lifecycle without a provider account.
> We are looking for contributors interested in provider contracts, local-first
> context, workflow conformance, safety, documentation, and reproducible demos.

Add the approved release URL, ninety-second demo, exact test totals, and known
limitations only after Phase 1 exit criteria are complete.
