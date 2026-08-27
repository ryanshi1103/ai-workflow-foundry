<p align="center">
  <img src="branding/logo.svg" width="112" alt="FlowFoundry Council Mark: one principal star above three council stars">
</p>

<h1 align="center">FlowFoundry</h1>

<p align="center"><strong>One goal. The smallest sufficient AI team.</strong></p>

<p align="center">
  <strong>Local-first Adaptive AI Team Runtime.</strong><br>
  <strong>Current Alpha: AI Coordination Layer.</strong>
</p>

<p align="center"><strong>你定目标，AI组队实现</strong></p>

<p align="center">
  Give FlowFoundry a goal. It profiles the work, chooses the smallest sufficient
  execution path, coordinates the required AI and tools within bounded permissions,
  validates the result, and preserves evidence.
</p>

<p align="center"><code>Goal → Decision Context → Profile → Minimum Sufficient Path → Execute → Validate → Human Gate → Evidence / Recovery</code></p>

<p align="center">
  <sub>local-first · adaptive team sizing · bounded AI Meetings · decision continuity · human authority</sub>
</p>

<p align="center">
  <a href="#quick-start">Try the offline workflow</a> ·
  <a href="#flagship-demo">See the flagship demo</a> ·
  <a href="#bounded-ai-meetings">Understand AI Meetings</a> ·
  <a href="docs/CURRENT_STATUS.md">Check current status</a>
</p>

<p align="center">
  <img src="docs/assets/architecture-overview.svg" width="920" alt="FlowFoundry coordinates a human goal through planning, routing, execution, review, evidence, and human approval">
</p>

> **Alpha / developer preview.** The deterministic offline coordination path
> and Decision Inheritance read path are runnable and tested. Real-provider
> execution remains explicit opt-in, provider parity is incomplete, and remote
> CI, independent review, and final demo media remain publication gates. Read the
> [current status](docs/CURRENT_STATUS.md) and
> [limitations](docs/LIMITATIONS.md) before relying on FlowFoundry.

## Why now?

**AI is moving from individual models to coordinated systems.**

AI tools are multiplying. A useful project may involve a coding model, a
reviewer, local tools, project files, security checks, and a human decision.
Each tool can be capable while the overall workflow remains fragmented.

The problem is no longer only intelligence. It is coordination:

- context gets copied between tools;
- permissions and side effects are easy to lose track of;
- cost and usage evidence is incomplete;
- review happens separately from execution;
- failures leave partial work that is hard to recover; and
- the human approval boundary is often implicit.

<p align="center">
  <img src="docs/assets/product-evolution.svg" width="920" alt="Disconnected AI tools become a bounded FlowFoundry workflow with evidence and human control">
</p>

FlowFoundry does not compete with AI models. It coordinates eligible models,
tools, workflows, permissions, costs, evidence, approvals, and recovery around
a goal. **Use the minimum sufficient path—not the largest possible AI team.**

## What works today

| Maturity | Product surface | Honest boundary |
|---|---|---|
| **SHIPPED — Alpha** | Goal profiling, Minimum Sufficient Path selection, deterministic offline execution, bounded Meetings, decision inheritance, review, approval gates, cancellation, recovery, evidence/reporting, provider preflight, workspace isolation, and Git-isolated writer candidates | CLI/terminal product; real-provider compatibility, cost completeness, and broad live-provider Meeting coverage remain experimental |
| **DESIGNED — not implemented** | Personal AI Command Center | Approval-first mobile/PWA specifications only; no shipped mobile application |
| **FUTURE** | Personal AI OS direction | Personal context/memory, learning management, product/project management, and adaptive AI-resource management are not shipped |

The current source also validates four component manifests, two workflow
contracts, thirteen registered capabilities, and a 36-entry project Decision
Ledger. There is no autonomous publishing authority, automatic decision
write-back, complete personal-memory layer, or universal intelligence claim in
the Alpha.

## Minimum Sufficient Path

```mermaid
flowchart LR
    G[Human goal] --> D[Applicable project decisions]
    D --> P[Task profile]
    P --> M{Smallest sufficient path}
    M -->|simple| S[One Agent]
    M -->|review needed| R[Agent + reviewer]
    M -->|materially different views| T[Bounded team / Meeting]
    S --> V[Execute + validate]
    R --> V
    T --> V
    V --> A{Approval required?}
    A -->|yes| H[Human decision]
    A -->|no| E[Evidence and result]
    H --> E
    E -. failure or interruption .-> C[Recovery]
    C --> P
```

The core principle is the smallest sufficient Agent or Team: if one Agent is
sufficient, do not use two; if two suffice, do not use five. The deterministic
profile chooses `single_agent`, `single_agent_reviewer`, or a bounded
`multi_agent` path and records why.

Routing then filters by capability, readiness, permission, workspace
compatibility, and policy. Outputs remain candidates until review and
validation complete. Consequential actions stop at a scoped human approval
gate, while durable run state preserves evidence and recovery.

## Bounded AI Meetings

A FlowFoundry Meeting is not “ask every model the same question.” It is a
bounded coordination protocol:

```text
Applicable project decisions
  → one Context Pack before Round 1
  → independent views
  → deterministic conflict detection
  → targeted cross-review / Round 2 only for actual disagreement
  → early consensus, convergence, or preserved dissent
  → decision and evidence output
```

Simple work avoids a Meeting. Where complementary perspectives have material
value, participants reason independently before seeing one another's views.
The Meeting can stop early on consensus, focus Round 2 on detected conflicts,
and preserve unresolved dissent rather than manufacturing agreement.

## Decision continuity

Projects should not forget binding decisions just because the next Agent starts
a new session. Before relevant task or Meeting reasoning begins, FlowFoundry
validates the project Decision Ledger, selects exact domain/surface matches, and
injects the authoritative wording into a bounded `ACTIVE PROJECT DECISIONS`
section:

```text
Decision Ledger → validate → select applicable decisions → Context Pack → task / Meeting
```

Implemented now: **read, validate, select, inject, and warn**. Superseded and
non-binding records cannot masquerade as current authority, and a proposed
value that occupies an active binding semantic slot generates a conflict
warning. Not implemented: automatic promotion, automatic `BINDING`, automatic
Human approval, automatic supersession, or automatic ledger write-back.

Read the [product architecture](docs/FLOWFOUNDRY_PRODUCT_ARCHITECTURE.md) or
the [Decision / Meeting model](docs/MEETING_DECISION_ADOPTION_MODEL.md).

## Why is it different?

The comparison is about operating style, not a claim that other assistants or
agent frameworks cannot coordinate work.

| Concern | Traditional assistant interaction | FlowFoundry coordination workflow |
|---|---|---|
| Starting point | Choose a model and prompt it | Define a goal, constraints, and authority |
| Coordination | The user carries context between interactions | A bounded plan records roles, dependencies, and state |
| Permissions | Often managed outside the conversation | Declared tool and workspace permissions are part of execution |
| Evidence | The answer or transcript is the main record | Tasks, reviews, usage, approvals, and reports remain inspectable |
| Recovery | The user reconstructs interrupted work | Retry, resume, cancellation, and partial results are durable states |
| Cost awareness | Checked separately or after the call | Provider-reported usage/cost is recorded; unknown remains unknown |
| Human control | Depends on the surrounding product/workflow | Review and approval are separate, explicit decisions |

ChatGPT, Claude, Copilot, Codex, DeepSeek, and local models can be intelligence
resources. FlowFoundry is the local coordination and project-control boundary
around eligible resources; it does not replace them.

## Flagship demo

> **Goal:** “Prepare my GitHub release.”

<p align="center">
  <img src="docs/assets/github-release-flow.svg" width="920" alt="GitHub Release Assistant moves from a bounded goal through planning, assigned roles, review, evidence, and a human approval stop">
</p>

The [GitHub Release Assistant](docs/demos/github-release-assistant.md) turns an
explicit five-task fixture into a visible coordination lifecycle:

1. resolve applicable release decisions before execution;
2. validate the declared task profile and dependency plan;
3. assign only the roles declared necessary by this fixture;
4. execute through deterministic fake providers and preserve evidence; and
5. stop the release-package task at `skipped_pending_human`.

Those five fixture tasks do not imply that every FlowFoundry run needs a
Planner, Builder, Reviewer, and Tester. The runtime's ordinary policy is still
the Minimum Sufficient Path.

The current demo makes no cloud-provider call, does not inspect the repository,
does not run the project's real tests, and does not write, push, tag, deploy, or
publish. Its value is showing coordination and the human boundary—not pretending
that a synthetic run created a real release.

## Quick start

**Target:** reach the first deterministic result in under 10 minutes from an
approved source checkout. The external artifact-install target remains
unverified until the release build and clean-install gates pass.

Requirements: Python 3.11+ and Git.

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install .

# Verify the bundled catalog, contracts, and capabilities.
flowfoundry validate

# Preview and run the offline flagship workflow.
flowfoundry team plan examples/personal-ai/github-release-assistant.json
flowfoundry team run \
  examples/personal-ai/github-release-assistant.json \
  --run-id first-flowfoundry-run

# Inspect the evidence and approval boundary.
flowfoundry team report first-flowfoundry-run
```

Expected validation checkpoint:

```text
validated 4 FlowFoundry components
validated 36 project decisions
validated 2 workflow contracts
validated 13 registered capabilities
```

Expected workflow state: `completed_with_blockers`, with four tasks complete
and `package` stopped at `skipped_pending_human`. That is a successful safety
outcome. Do not approve it during the first walkthrough.

If installation or output differs, use the
[installation guide](docs/INSTALLATION.md),
[troubleshooting guide](docs/TROUBLESHOOTING.md), and
[Alpha user guide](docs/ALPHA_USER_GUIDE.md). Do not add provider credentials
to evaluate the offline path.

## Architecture

FlowFoundry keeps models replaceable and separates four concerns:

- **Runtime:** provider identities and deterministic/local capabilities;
- **Coordination:** planning, routing, bounded execution, review, approval, and recovery;
- **Personal context:** a future, consent-based layer—not a shipped memory system; and
- **Interfaces:** CLI/terminal today, with an approval-first mobile concept designed for later.

Security, privacy, cost, provenance, evidence, and human authority remain
cross-cutting controls. See the
[authoritative document map](docs/AUTHORITATIVE_DOCUMENT_MAP.md) for the
official product, architecture, roadmap, security, and release sources.

## Roadmap

<p align="center">
  <img src="docs/assets/roadmap.svg" width="920" alt="FlowFoundry roadmap from the current Alpha coordination layer to a designed Personal AI Command Center and future Personal AI OS">
</p>

1. **Current — AI Coordination Layer:** make planning, routing, review,
   Meetings, decision continuity, approval, recovery, and evidence trustworthy
   for external Alpha users.
2. **Next — Personal AI Command Center:** validate an approval-first mobile PWA
   boundary without storing credentials or exposing an unrestricted shell.
3. **Future — Personal AI OS:** explore user-owned context, provenance,
   preferences, and resource optimization with privacy and human authority.

Stages are evidence gates, not calendar promises. Read the canonical
[product roadmap](docs/PRODUCT_ROADMAP.md).

## Contributing

FlowFoundry is especially useful for contributors interested in local-first AI
infrastructure, orchestration, safety boundaries, developer experience, testing,
and technical communication.

- **Developers:** improve CLI clarity, workflow fixtures, isolation, and tests.
- **Students:** improve tutorials, examples, and first-install feedback.
- **Researchers:** help define evaluation, provenance, and reproducible evidence.
- **AI builders:** strengthen provider diagnostics without widening authority.

Start with [CONTRIBUTING.md](CONTRIBUTING.md), follow the
[Day 1 → Day 7 journey](docs/CONTRIBUTOR_JOURNEY.md), or review the
[five scoped starter issues](docs/GOOD_FIRST_ISSUES.md). Small, evidenced
changes are preferred over broad capability claims.

## Trust and project status

- [Current capabilities and evidence](docs/CURRENT_STATUS.md)
- [Decision and Meeting model](docs/MEETING_DECISION_ADOPTION_MODEL.md)
- [Known Alpha limitations](docs/LIMITATIONS.md)
- [Historical decision ledger](docs/DECISION_LEDGER.md)
- [Security policy](SECURITY.md)
- [Documentation map](DOCUMENTATION_MAP.md)
- [Final candidate and release gates](docs/FINAL_CANDIDATE_CHECKLIST.md)
- [Community operating model](docs/COMMUNITY_OPERATING_MODEL.md)

FlowFoundry is MIT licensed. No push, tag, release, mobile product, personal
memory system, or automatic publication capability is implied by this
documentation branch.
