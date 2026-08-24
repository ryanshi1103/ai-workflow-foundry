# Product Roadmap

Status: product-stage roadmap; future stages are not shipped

## Product direction

FlowFoundry progresses from a tested AI coordination layer toward a user-owned
Personal AI Operating System. Stages are evidence gates, not calendar promises.

## Stage 1 — AI Coordination Layer

Status: **Current Alpha**

### Shipped in the candidate

- workspace/project discovery and provider launch profiles;
- explicit permissions and minimum-tool policy;
- goal profiling and minimum-path planning;
- explicit DAG and bounded multi-agent execution;
- Claude, DeepSeek-compatible, Codex, and local routing identities;
- deterministic fake-provider execution;
- review, approval, retry, resume, cancellation, and reports;
- Git-isolated writer candidates and conservative recovery;
- component/capability/workflow contracts; and
- provider-reported usage/cost evidence when available.

### Experimental in Stage 1

- live-provider parity and version compatibility;
- provider-reported cost completeness;
- live Meeting and cancellation coverage;
- routing based on limited project-local outcome history; and
- operator experience beyond CLI/terminal.

### Not shipped in Stage 1

- complete personal semantic memory;
- preference learning;
- mobile or web product;
- automatic push, merge, deployment, or publication;
- general local-model/plugin ecosystem; and
- learned best-cost/best-quality optimization.

### Exit gate

- trustworthy public Alpha artifacts and CI;
- 100 activated external users;
- repeatable clean installation and first workflow;
- no critical security/privacy/license blocker; and
- evidence-based priorities from external feedback.

## Stage 2 — Personal AI Command Center

Status: **Designed next; not implemented**

Add a narrow, approval-first interface around the existing local coordination
runtime. The phone is a command and human-decision surface, not remote desktop
and not an execution host.

Planned capabilities:

- iPhone-first PWA dashboard, task creation, approvals, timeline, and
  notifications; and
- local-agent pairing, explicit permission/cost/evidence views, and bounded
  commands with no unrestricted terminal.

Provider credentials remain on the computer. Stage 2 does not implement
personal semantic memory or authorize autonomous financial, publishing,
deployment, or permission-widening actions.

### Exit gate

- PWA pairing/approval security passes independent review;
- task, timeline, evidence, and stale/offline states pass external usability
  validation;
- no credential is stored on the phone and no unrestricted shell is exposed;
  and
- every approved action is exact, attributable, expiring, and auditable.

## Stage 3 — Personal AI Operating System

Status: **Long-term future**

Provide an open coordination substrate across personal tools, devices, context,
workflows, and approved intelligence resources.

Planned direction:

- explicit and confirmed preferences;
- provenance-aware personal knowledge and outcome history;
- inspect, correct, export, expire, forget, and memory-disabled controls;
- explainable retrieval and provider-disclosure receipts;
- personalized workflow recommendations;
- portable capability/provider/workflow contracts;
- cross-device control with explicit data placement;
- local and remote model/resource scheduling;
- unified privacy, budget, permission, approval, audit, and recovery views;
- user-owned context and policy portability;
- best-action recommendations across model, tool, cost, timing, and human
  attention; and
- third-party conformance, signing, provenance, and lifecycle evidence.

The system optimizes the best eligible action, not a universally best model.
Automation cannot override human authority or hard policy.

### Exit gate

- state and policy are portable without provider lock-in;
- third-party capabilities pass public conformance/security contracts;
- optimization improves validated real-world outcomes;
- local-only use remains supported; and
- consequential operation stays explainable, reversible, and auditable.

## What does not change across stages

- Humans own goals and consequential decisions.
- Models are replaceable capabilities, not the product authority.
- Use the minimum sufficient path.
- Personal data is local by default and disclosed by policy.
- Unknown cost or state remains unknown.
- Review is separate from approval.
- Side effects belong to trusted code and exact grants.
- FlowFoundry does not claim AGI, universal intelligence, or human replacement.

## Immediate roadmap decision

Do not begin Stage 2 by ingesting personal data. First close the public Alpha,
validate the first 100 users, and build only the narrow PWA control surface.
Personal context belongs to the later Personal AI OS stage and follows privacy,
provenance, user ownership, correction, export, deletion, and disclosure
controls.
