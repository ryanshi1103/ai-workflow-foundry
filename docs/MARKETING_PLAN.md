# Open-source Marketing Plan

FlowFoundry should grow by demonstrating a clear coordination problem and
publishing reproducible engineering evidence. The message is not “we built the
smartest AI.” It is:

> We built a local-first system that helps different AI tools work together
> under explicit permissions, budgets, review, and recovery.

## Audience

### Primary

- developers already using two or more AI coding/research tools;
- agent-framework developers who care about reliability and observability;
- local-first and privacy-conscious builders;
- researchers studying multi-agent coordination, evaluation, or human oversight;
- maintainers building reusable AI workflow components.

### Secondary

- technical product teams evaluating provider independence;
- automation practitioners who need review and recovery;
- educators and knowledge workers exploring personal AI systems;
- enterprise architects interested in future coordination controls.

## Positioning

Use three consistent messages:

1. **Coordination over model worship.** Different models and deterministic tools
   have different strengths.
2. **Bounded by design.** Minimum-path planning, explicit permissions, isolated
   candidates, review, approval, and recovery are product features.
3. **Personal infrastructure, not human replacement.** The human owns goals,
   context, and consequential decisions.

Avoid:

- AGI, autonomous employee, or “replace your team” language;
- benchmark superiority without reproducible evidence;
- listing planned providers as supported;
- calling fake-provider demos live multi-model results;
- hiding cost, license, security, or publication limitations.

## Launch content package

Prepare these assets before announcement:

- a five-minute README path from problem to offline run;
- ninety-second AI Project Manager demo;
- architecture article: “Why AI systems need a coordination layer”;
- technical article: “Isolating AI writers with Git worktrees”;
- operator article: “Unknown cost should remain unknown”;
- contributor issue set for provider contracts, demo UX, and documentation;
- release notes with implemented/experimental/planned tables;
- reproducible test and privacy evidence for the publication candidate.

## Channel strategy

### GitHub

- Use a concise description: “Local-first coordination for bounded,
  reviewable, and recoverable AI workflows.”
- Suggested topics: `ai-agents`, `multi-agent`, `local-first`, `ai-workflows`,
  `developer-tools`, `human-in-the-loop`, `llm-orchestration`.
- Pin the release, demo issue, roadmap discussion, and good-first-issue board.
- Respond to issues with reproducible evidence and clear maturity language.

### Hacker News

Title pattern: **Show HN: FlowFoundry – a local-first coordination layer for AI
tools**.

Lead with the engineering problem, one offline command, architecture choices,
and known limitations. The author should remain available for technical
questions and avoid promotional cross-posting during the discussion.

### Reddit

Choose communities whose rules permit project posts. Tailor the substance:

- local-first/privacy communities: data and provider boundaries;
- programming/agent communities: scheduler, worktrees, recovery, and contracts;
- self-hosting/local-model communities: honest current absence of a complete
  local-model adapter and an invitation to shape the contract.

Do not paste identical marketing copy across communities.

### X / Twitter

Use a short visual thread:

1. one-model problem;
2. coordination diagram;
3. ninety-second demo;
4. three safety decisions;
5. current limitations;
6. contributor invitation.

### AI and research communities

Share an architecture note and a reproducible offline fixture. Invite critique
of the minimum-path decision, conflict gate, cost evidence, and human approval
model. Do not frame preliminary engineering as a research breakthrough.

## Content cadence

### Four weeks before launch

- close publication and license gates;
- recruit three to five private technical reviewers;
- turn reviewer confusion into README and setup fixes;
- prepare demo and issue backlog.

### Launch week

- publish release notes and demo on GitHub first;
- announce to one primary community, learn from feedback, then stagger other
  channels over several days;
- label issues quickly and publish known problems visibly.

### First month

- weekly engineering note or contributor spotlight;
- one scoped community call for provider-adapter design;
- publish installation and demo success/failure metrics;
- close or refine stale issues rather than optimizing star count.

### Ongoing

- monthly roadmap evidence update;
- release only when acceptance gates close;
- maintain a public compatibility matrix;
- rotate between architecture, workflow examples, and contributor stories.

## Growth loop

```text
Reproducible demo
      ↓
Developer tries offline path
      ↓
Clear issue or workflow proposal
      ↓
Contract + tests + documentation
      ↓
More useful capability
      ↓
New reproducible demo
```

The ecosystem unit should be a reviewed capability or workflow, not an
unverified prompt collection.

## Measures that matter

Track:

- successful fresh-install and offline-demo runs;
- time to first validated run;
- issue response and first-contribution time;
- number of independently maintained adapters/workflows passing conformance;
- repeat contributors and reviewed releases;
- demo-to-install conversion;
- known provider cost/latency/validation evidence coverage.

Treat stars, impressions, and follower count as reach indicators, not product
quality.

## Risks and responses

| Risk | Response |
|---|---|
| “Another agent framework” perception | Lead with local project runtime, minimum-path selection, isolation, review, and recovery evidence |
| Vision overpromises implementation | Put maturity labels beside every demo and capability |
| Provider fan debates | Return to task fit, replaceable adapters, and user constraints |
| Privacy skepticism | Publish sanitized process evidence and current limitations; never expose incident contents |
| Maintainer overload | Narrow issue scopes, templates, labels, and documented architecture decisions |
| Demo works only on maintainer machine | Require fresh-checkout offline acceptance and record exact environment |
