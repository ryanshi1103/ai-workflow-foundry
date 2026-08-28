# Mobile AI Command Center

Status: product and interaction design; not implemented
Primary MVP: installable iPhone Safari PWA
Product promise: control a personal AI system from anywhere without turning the
phone into a remote desktop.

Product role: **the human approval and intelligence interface**.

## Product definition

The designed FlowFoundry Mobile concept is a management interface for the
coordination layer running on the user's computer. In that future design, the
phone expresses goals, inspects plans and evidence, sets constraints, grants
narrow approvals, and receives results. The computer owns projects, tools,
credentials, provider runtimes, and side effects.

The phone is not the computer. It provides five iPhone-first MVP surfaces:

- a dashboard for projects, AI team status, tasks, costs, and warnings;
- task creation from a human goal;
- approval cards for exact actions;
- an evidence-backed execution timeline; and
- privacy-safe notifications for meaningful state changes.

It stores no provider credentials, exposes no unrestricted terminal, and
permits no hidden action. Designed capability is not shipped capability: the
current repository has the terminal/CLI runtime, while the PWA remains an
implementation phase.

The core decision path remains visible:

```text
Goal
  -> required capability
  -> available resources
  -> cost and privacy constraints
  -> permission decision
  -> execution
  -> review and evidence
```

This is deliberately not screen streaming, mouse emulation, shell exposure, or
a mobile clone of the desktop terminal.

## Product principles

1. **Intent over pixels.** Users send goals and structured decisions, not remote
   clicks.
2. **Plan before effects.** Analysis produces a reviewable plan before any
   write, push, deploy, deletion, or financial action.
3. **Local execution authority.** The computer agent executes; the phone never
   receives provider secrets or direct filesystem authority.
4. **Minimum sufficient path.** Use one suitable agent when possible and add
   reviewers or a bounded team only when risk or scope justifies it.
5. **Evidence over animation.** Progress is backed by durable events, test
   counts, diffs, costs, and review decisions.
6. **Honest degraded states.** Offline, stale, waiting, blocked, and unknown-cost
   states are visible and never presented as success.
7. **No hidden actions.** Every effect appears in the plan and event history;
   approval-required effects stop until an exact human decision is recorded.

## Information architecture

```text
Command Center
├── Dashboard
│   ├── Projects
│   ├── Active tasks
│   ├── Agents
│   ├── Costs
│   └── Warnings
├── New task
│   ├── Goal
│   ├── Context scope
│   ├── Budget and deadline
│   └── Proposed plan
├── Execution
│   ├── Timeline
│   ├── Agent activity
│   ├── Artifacts and diffs
│   └── Reviews
├── Approvals
│   ├── Pending
│   ├── Granted
│   └── Expired or revoked
└── Settings
    ├── Paired computers
    ├── Capability policy
    ├── Privacy
    └── Notifications
```

## 1. Mobile dashboard

The first screen answers six questions: what projects exist, whether the local
agent is reachable, what is running, which agents are usable, how much has been
spent, and what needs attention.

```text
FlowFoundry                         Connected

FlowFoundry                         READY
Release audit                       80%
Documentation                       DONE

Agents
Claude        READY
DeepSeek      READY
Codex         READY

Today
Reported cost                 $1.24
Unreported usage              1 run

Warnings
1 approval waiting
Candidate branch differs from remote
```

Dashboard status must be derived from evidence:

- `READY`: local agent reachable and project preflight passed;
- `BUSY`: at least one bounded execution is active;
- `WAITING_APPROVAL`: execution is stopped at a durable approval gate;
- `BLOCKED`: a review, policy, provider, or validation gate failed;
- `OFFLINE`: no authenticated heartbeat is available;
- `STALE`: cached data is shown with its last verified timestamp.

Cost cards distinguish reported cost, configured budget, and unknown usage.
Unknown cost is never converted into zero.

## 2. AI task interface

The task composer collects a goal first. Advanced constraints remain available
without forcing users to understand agent internals.

Required inputs:

- goal;
- target project or explicit “no project” mode;
- data scope the task may inspect;
- deadline or “no deadline”; and
- budget ceiling or “cost unavailable; ask before paid calls.”

Optional inputs:

- preferred privacy level;
- allowed providers;
- expected artifact;
- required reviewer; and
- actions the user already knows must remain plan-only.

Example:

> Prepare my GitHub release.

The AI Manager responds with a structured proposal:

```text
Understood context
Project: FlowFoundry
Branch: release/v0.2.0-alpha.1-final-candidate
Risk: high (remote publication)
Budget: $2 maximum; ask if usage cannot be measured

Recommended path
1. Local Tester — run deterministic tests
2. Codex — verify code and package evidence
3. Claude — review architecture and release claims
4. DeepSeek — perform cost-efficient documentation cross-check

No-effect actions
Read, analyze, plan, produce an in-app draft

Approval gates
Write files, push the exact candidate, create a tag, publish a release
```

The user may edit the plan, lower the budget, exclude a provider, demand a
reviewer, or save it without execution.

## 3. Approval system

The interface separates permission to reason from permission to cause an
effect.

Default no-effect capabilities:

- read explicitly scoped files;
- analyze project metadata;
- generate an in-app plan or draft;
- run pre-approved deterministic read-only checks; and
- summarize existing evidence.

Confirmation-required capabilities:

- write or rename project files;
- run a command with side effects;
- delete or overwrite data;
- push, open a pull request, merge, tag, or publish;
- deploy or change infrastructure;
- send a message or publish content;
- purchase, transfer, trade, or make another financial commitment; and
- widen context, provider, network, or permission scope.

An approval card shows the exact action, target, diff or payload summary,
provider, maximum cost, expiry, and rollback boundary. “Approve” signs only
that action digest. Editing any material field invalidates the approval.

## 4. Live execution

Live execution is an append-only event timeline, not a guessed progress bar.

```text
Agent       Codex
Task        Running foundation tests
Progress    228 / 228
Result      PASS
Evidence    Test log · 15.0 s

Next        Package build
State       BLOCKED
Reason      Build backend unavailable in verified environment
```

The client may reconnect and replay from its last acknowledged event sequence.
Each event has a run ID, task ID, monotonic sequence, timestamp, state, safe
summary, and optional evidence reference. Provider chain-of-thought, secrets,
raw credentials, and unrestricted terminal output are never streamed.

Required controls:

- pause future scheduling;
- request cancellation;
- resume after a resolved gate;
- open a redacted artifact or diff;
- approve or reject a pending action; and
- export a signed run report.

Cancellation is reported as requested, terminating, cancelled, completed-before-
cancel, or unable-to-verify. The UI must not claim cancellation until the local
agent verifies the process outcome.

## 5. Personal data intelligence

Personalization is a future local-first context system, not model training on
the user's private life.

Eligible sources include user-selected projects, documents, explicit
preferences, reviewed history, confirmed outcomes, and goals. Each retrieved
item needs provenance, scope, freshness, a reason for use, and a disclosure
decision before it can leave the computer.

The user must be able to inspect, correct, export, expire, forget, and disable
personal context. Recommendations should answer: “What evidence caused this
suggestion?”

The product goal is the best personal decision system for the user—not a claim
to train a larger or universally intelligent model.

## Core user flows

### Pair a computer

1. The computer displays a short-lived QR pairing invitation.
2. The phone scans it and verifies the computer fingerprint.
3. Both devices confirm the same short authentication string.
4. The user names the phone and grants initial capabilities.
5. The computer records a revocable device identity; no provider credential is
   copied to the phone.

### Start a task

1. Select project and enter goal.
2. Review understood context, resource availability, and constraints.
3. Review the minimum sufficient plan.
4. Start only the no-effect portion.
5. Receive approvals when an exact side effect becomes ready.
6. Inspect validation and review before accepting the outcome.

### Approve a push

1. See local branch, local SHA, intended remote/ref, commits, checks, and diff
   summary.
2. Confirm the branch is clean and approval is for one immutable SHA.
3. Approve once with a short expiry.
4. Computer agent performs the push and independently reads back the remote SHA.
5. Phone displays verified match or a classified failure.

## Notifications

Notify only for meaningful state transitions: approval required, blocked,
completed, budget threshold, pairing/revocation, or security warning. A push
notification contains no file content, prompt content, branch secrets, or
approval bearer token; it only asks the authenticated app to reconnect.

## MVP scope

Included:

- one user and one or more paired computers;
- project and agent status;
- goal submission and plan review;
- run timeline with reconnect/replay;
- scoped approvals and cancellation requests;
- reported/unknown cost display;
- local audit export; and
- iPhone Safari installation as a PWA.

Excluded:

- remote desktop, arbitrary shell, and raw terminal streaming;
- background autonomous publication;
- provider credential entry or storage on the phone;
- collaborative teams, organization tenancy, and billing;
- personal semantic memory; and
- native mobile-only features.

## MVP acceptance criteria

- A paired phone can submit a goal and receive a deterministic plan without a
  publicly exposed local-agent port.
- Reconnect resumes the event stream without duplicating a completed action.
- A write/push/deploy/delete/financial action cannot execute without a valid,
  exact, unexpired approval.
- Revoking a phone prevents all new commands and approvals from that device.
- The phone never receives provider API keys, passwords, or private credential
  files.
- Offline, stale, blocked, unknown-cost, and cancellation states are accurate.
- Security tests cover replay, scope widening, expired approval, stolen relay
  token, and local-agent disconnect.

## Design change record

| Change | Reason | Primary risk | Required evidence |
|---|---|---|---|
| Mobile management interface | Control AI work anywhere without remote desktop | UI implies authority the agent does not have | State-contract and end-to-end tests |
| Plan-before-effects flow | Preserve human authority | Approval fatigue | Usability test plus hazardous-action coverage |
| Event timeline | Make progress auditable and recoverable | Sensitive output leakage | Redaction and replay tests |
| Personal context direction | Improve recommendations from user-owned evidence | Privacy boundary erosion | Provenance, disclosure, export, and deletion tests |
