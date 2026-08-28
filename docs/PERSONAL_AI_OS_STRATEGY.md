# Personal AI OS Strategy

Status: product strategy; later phases are planned, not implemented

## Thesis

The future is not one model becoming smart enough for every task. The useful
system is a coordination layer that understands a person's goals and
constraints, then selects the best available action across models, tools,
context, time, cost, privacy, and human attention.

The optimization target is **best action**, not **best model**.

## Phase 1 — AI Workflow Manager

Status: **Current Alpha**

FlowFoundry currently provides the coordination foundation:

- project and workspace discovery;
- Claude, DeepSeek-compatible, Codex, and deterministic runtime identities;
- minimum-path planning and bounded task DAGs;
- capability, permission, workspace, and readiness routing;
- review, validation, approval, retry, resume, cancellation, and reporting;
- Git-isolated writer candidates; and
- measured operational cost/latency evidence when providers report it.

The current system is strongest as developer infrastructure. It is not yet a
complete personal assistant, memory engine, mobile product, or learned resource
optimizer.

Phase gate:

- public Alpha installs reproducibly;
- external users complete offline workflows;
- release/security processes work outside the maintainer environment; and
- current limitations remain visible.

## Phase 2 — Personal AI Coordinator

Status: **Planned**

Add user-owned context while preserving the coordination and safety substrate.

### Memory

Store facts, decisions, outcomes, and temporary context with provenance,
freshness, project scope, retention, and deletion controls. Do not treat an
unstructured chat archive as trustworthy memory.

### Preferences

Separate explicit preferences from system inferences. Promote an inference to a
durable preference only after user confirmation. Make every preference
inspectable, correctable, exportable, and reversible.

### History

Record validated outcomes, review decisions, user corrections, costs, latency,
and discarded results. Use this evidence to recommend workflows without hiding
why a recommendation changed.

### Mobile command center

Deliver an iPhone-first PWA as the human approval and intelligence interface.
The phone submits goals, reviews plans, sees AI team status and costs, signs
exact approvals, and receives results. The local computer retains projects,
credentials, tools, and execution authority.

Phase gate:

- users can inspect, export, delete, and disable all personal context;
- retrieval receipts explain every context item;
- provider disclosure never bypasses privacy policy;
- mobile pairing, revocation, replay protection, and exact approvals pass
  independent security review; and
- recommendations remain useful in local-only mode.

## Phase 3 — Personal Intelligence System

Status: **Planned**

Combine explicit goals, constraints, resources, context, and confirmed outcomes
to create personalized decision support.

The system understands:

- what the user is trying to achieve;
- time, money, privacy, attention, and compute limits;
- available models, tools, documents, and collaborators;
- current project and knowledge state;
- confirmed preferences and prior mistakes; and
- the evidence required before a result can be trusted.

It can recommend a strategy, workflow, budget, model/tool combination, and
review depth. It cannot silently redefine goals, spend money, disclose sensitive
context, or approve its own effects.

Phase gate:

- recommendations cite supporting evidence and uncertainty;
- repeatable personal workflows improve validated outcome, cost, or time over a
  fixed workflow baseline;
- users can reset or override every learned policy; and
- personalization does not require hidden telemetry or mandatory cloud storage.

## Phase 4 — AI Resource Optimization Network

Status: **Long-term direction**

Coordinate local and remote intelligence resources across devices and approved
services. Automatically recommend the best eligible:

- model for the required capability;
- deterministic tool or workflow;
- cost and quota allocation;
- privacy-preserving context path;
- execution time and deadline tradeoff;
- validation and reviewer path; and
- point for human attention.

“Automatic” remains bounded by hard policy. The optimizer cannot override
permission, privacy, budget, legal, or approval constraints. Unknown price,
quality, availability, or state remains unknown.

Phase gate:

- provider/workflow contracts are portable and independently conformant;
- recommendations show complete reason receipts;
- optimization improves real validated user outcomes;
- cross-device data placement is visible and controllable; and
- the system remains useful without a central service or single provider.

## Scenario: student

Goal: “I need an exam preparation and career plan.”

Future FlowFoundry analyzes only user-approved inputs:

- available time and fixed commitments;
- course materials and current knowledge;
- diagnosed knowledge gaps;
- learning preferences confirmed by the student;
- prior mistakes and reviewed outcomes; and
- career interests and deadlines.

It coordinates research, planning, learning, and review capabilities to produce
a personal execution roadmap with sources, milestones, tradeoffs, and revision
points. This scenario depends on the planned personal-context layer and must not
be presented as a current live Alpha capability.

## Scenario: developer

Goal: “Prepare my GitHub release.”

Current FlowFoundry can already contribute meaningful pieces:

- inspect the project/candidate boundary;
- plan a bounded test and review workflow;
- route implementation, review, and deterministic validation capabilities;
- preserve evidence and costs;
- isolate write-capable candidates; and
- stop at approval boundaries.

A future command center adds mobile plan review and exact approval cards. The
system may recommend Codex for code verification, Claude for architecture or
claim review, DeepSeek-compatible analysis where eligible, and deterministic
tests for evidence. It must not claim success, push, tag, or publish without the
required proof and authority.

## Strategy constraints

- Trust before autonomy.
- Usability before new agent count.
- External feedback before learned optimization.
- Provenance before personal memory.
- Stable contracts before provider ecosystem expansion.
- Real outcome evidence before model-ranking claims.
- Human authority before convenience.

## Relationship to the canonical roadmap

This document explains the long-term strategy; it does not define current
release status or roadmap priority. Product stages and acceptance gates live in
[Product Roadmap](PRODUCT_ROADMAP.md). Mobile delivery details remain in
[Mobile PWA MVP](MOBILE_PWA_MVP.md). The canonical layer model
is [FlowFoundry Product Architecture](FLOWFOUNDRY_PRODUCT_ARCHITECTURE.md).

## 90-day strategic sequence

### Days 1–14 — trustworthy public Alpha

- close exact-SHA package, CI, security, legal, and publication gates;
- publish one reproducible developer release-preparation demo;
- make installation and limitations obvious; and
- prepare a small, test-backed contributor issue set.

### Days 15–45 — PWA control-plane prototype

- implement typed local control schemas and event replay;
- build dashboard, task creation, approval cards, timeline, and notifications;
- prove QR pairing, revocation, no-public-port operation, and no phone secrets;
- keep all provider execution on the computer.

### Days 46–70 — personal context foundation

- design provenance, scope, retention, export, correction, and deletion first;
- implement a local-only, memory-disabled-by-default evaluation slice;
- use synthetic fixtures and explicit user-confirmed preferences; and
- do not introduce learned routing yet.

### Days 71–90 — external contributor loop

- onboard the first external users and document activation failures;
- publish adapter/workflow conformance discussions and good-first issues;
- measure successful install and offline-demo completion; and
- choose the next milestone from evidence, not feature volume.
