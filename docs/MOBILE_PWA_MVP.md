# Mobile PWA MVP

Status: product boundary only; not implemented
Platform: iPhone Safari first
Native apps: out of scope

## Purpose

The PWA is a **human approval and intelligence interface** for the FlowFoundry
agent running on the user's computer. It is not remote desktop, screen
streaming, a raw terminal, or a place to configure provider credentials.

This document defines the smallest useful prototype surface. Detailed pairing,
transport, event, and threat decisions remain in
[Remote Agent Architecture](REMOTE_AGENT_ARCHITECTURE.md) and
[Mobile Security Model](MOBILE_SECURITY_MODEL.md). This MVP does not introduce a
second architecture.

## Prototype question

Can a user understand project and AI-team state, submit one bounded goal, watch
evidence-backed progress, and make an exact approval decision from an iPhone
without moving credentials or execution authority off the computer?

## Included surfaces

### Dashboard

Show:

- paired computer reachability and last verified timestamp;
- projects and READY/BUSY/WAITING/BLOCKED/OFFLINE/STALE state;
- AI routing identities and readiness;
- active and recent tasks;
- reported cost, budget, and unknown usage separately; and
- warnings and pending approvals.

The dashboard is a redacted status view. It does not browse the full filesystem
or expose unrestricted model transcripts.

### Task creation

Collect:

- human goal;
- selected project;
- allowed data scope;
- privacy constraint;
- budget ceiling or ask-before-paid-call policy;
- deadline; and
- optional provider exclusions.

The response is a structured plan showing understood context, required
capabilities, routed identities, permissions, cost state, review stages, and
approval points. The user can accept, revise, or cancel the plan.

The prototype supports one demonstrated goal:

> “Prepare my GitHub release.”

It must preserve the same evidence boundary as the CLI demo: release analysis
and package quality are not claimed unless real tests and artifacts exist.

### Approval cards

Each card shows:

- action verb and exact target;
- project and immutable input/candidate digest;
- file, remote, or artifact scope;
- effect and rollback boundary;
- maximum or unknown cost;
- expiry and one-time status; and
- approve/reject controls.

Read, analyze, and prepare-in-app actions may proceed within an existing grant.
Write, delete, push, deploy, publish, financial, and permission-widening actions
require exact confirmation.

The first prototype may display the existing synthetic `release`-class approval
used by the offline demo. It must not imply that approval performs a push, tag,
deploy, publication, or real package build, and it must not expose such effects
until the corresponding local execution contract and negative tests exist.

### Execution timeline

Render committed events for:

- goal received;
- plan created/accepted;
- task queued/running/completed/blocked;
- routed identity and execution kind;
- review and validation decision;
- usage/cost receipt;
- approval requested/allowed/rejected/expired;
- cancellation requested/verified/uncertain; and
- final report available.

Reconnect replays events after the last acknowledged sequence. The UI never
guesses success, completion percentage, cancellation, or cost.

### Notifications

Notify only for:

- approval required;
- task blocked;
- run completed;
- cost threshold reached;
- paired device revoked; or
- security warning.

A notification contains an opaque wake-up identifier and non-sensitive event
class. It contains no goal, filename, prompt, diff, credential, approval bearer
token, or provider output.

## Explicitly excluded

- native iOS or Android application;
- remote desktop or screen streaming;
- unrestricted shell/terminal;
- arbitrary file browser;
- provider credential entry or storage;
- raw chain-of-thought or full transcript streaming;
- background autonomous execution expansion;
- push, deploy, publish, or financial effects without separately implemented
  exact action contracts;
- personal semantic memory; and
- teams, organizations, billing, or enterprise policy administration.

## Security invariants

1. No provider credentials, passwords, SSH keys, or private credential files on
   the phone or relay.
2. No unrestricted command string accepted from the PWA.
3. No hidden action: every effect is present in the plan and durable event log.
4. Local service has no public port by default.
5. Pairing is short-lived, device-bound, revocable, and replay-resistant.
6. Approval is exact, signed, scoped, expiring, and one-time.
7. The computer revalidates policy and action digest immediately before effect.
8. Relay or notification compromise cannot forge an approval.
9. Stale or uncertain local state is displayed as stale or uncertain.
10. Local-only operation remains useful when remote connectivity is disabled.

## Prototype milestones

### M1 — Static interaction prototype

- mobile layout for all five surfaces;
- synthetic, non-sensitive state fixtures;
- accessibility and approval comprehension test; and
- no connection to real projects or providers.

### M2 — Loopback deterministic slice

- typed status/goal/plan/event/approval schemas;
- FastAPI bound to loopback;
- deterministic fake-provider run only;
- durable event replay and idempotency; and
- no network relay.

### M3 — Paired LAN PWA

- short-lived QR invitation;
- device identity and revocation;
- authenticated HTTPS;
- no sensitive service-worker cache; and
- iPhone Safari install/reconnect evidence.

### M4 — Outbound remote prototype

- outbound-only connection;
- application-layer encrypted command/event envelopes;
- privacy-safe notifications;
- relay outage/stale-state behavior; and
- independent pairing/approval security review.

## MVP acceptance criteria

- A new user can identify project state, active AI identity, next action, and
  pending approval without reading the CLI.
- The GitHub release-assistant synthetic run is visible end to end.
- Reconnect does not duplicate a command or completed effect.
- A changed action digest invalidates approval.
- Revoked phones cannot submit commands or approvals.
- Browser storage, service-worker cache, relay logs, notifications, and traffic
  inspection contain no prohibited plaintext or credentials.
- No public local port, unrestricted shell, hidden execution, native app, or
  real-provider requirement is introduced.

## Evidence required before calling it an MVP

- supported iOS/Safari matrix;
- accessibility and approval-comprehension results;
- pairing/replay/revocation/idempotency tests;
- storage and network privacy inspection;
- security review of cryptographic protocol and capabilities;
- five external users completing the release-assistant prototype; and
- documented failures and limitations.
