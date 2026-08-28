# Mobile Security Model

Status: security design; not implemented

## Security objective

The mobile command center may request and approve bounded actions, but only the
paired local computer may execute them. A compromised relay, notification
service, model response, or unpaired phone must not gain project, credential, or
provider authority.

The default deployment is local-first and exposes no public local-agent port.

## Assets

- local projects, documents, history, preferences, and run artifacts;
- provider credentials and local authentication sessions;
- Git remotes, deployment identities, and financial accounts;
- device and agent private keys;
- capability grants and approval records;
- run state, event history, cost evidence, and review decisions; and
- the integrity and availability of the local computer agent.

Provider API keys, passwords, SSH private keys, cloud credentials, and private
credential files must never be stored on the phone or relay.

## Trust boundaries

```text
Phone secure storage
  | signed + encrypted application envelope
  v
Untrusted network / relay / push notification service
  | ciphertext only
  v
Local connection gateway
  | authenticated typed command
  v
Policy and approval engine
  | permitted local operation
  v
FlowFoundry orchestrator -> providers / projects / tools
```

The model boundary is also untrusted. Model output can propose a plan or action
but cannot create a capability grant, sign an approval, choose its own approval
scope, interpolate an arbitrary command, or access a secret value.

## Threat model

In scope:

- stolen or temporarily unlocked phone;
- malicious or compromised relay;
- intercepted QR invitation;
- replayed, delayed, duplicated, or reordered messages;
- malicious website attempting to invoke PWA capabilities;
- compromised or prompt-injected model output;
- unauthorized scope widening;
- approval confusion between projects, branches, files, remotes, or costs;
- sensitive data in events, notifications, logs, caches, or screenshots;
- local-agent restart during an action;
- revoked device reconnecting after being offline; and
- denial of service and notification spam.

Out of scope for the MVP, but documented as residual risk:

- a fully compromised local operating system with access to the user's session;
- hardware or firmware compromise;
- forensic extraction defeating the phone OS security boundary;
- provider-side compromise; and
- availability when both the computer and relay are offline.

These conditions never justify silently weakening approval or credential rules.

## Authentication and device pairing

Each phone creates a non-exportable device key. The local agent has a stable
identity key protected by restrictive local permissions and, where available,
the OS keychain or secure hardware.

The QR invitation contains only a short-lived pairing capability and public
material. It expires quickly, is single-use, and is invalidated after success or
explicit cancellation. Both devices display the same short authentication
string so the user can detect an intercepted pairing flow.

The durable paired-device record stores:

- device public key and key ID;
- human-readable device name;
- created, last-seen, and revoked timestamps;
- capability and project scopes;
- maximum session duration;
- policy version; and
- optional device-attestation state when native clients support it.

There is no reusable QR bearer token and no password-only fallback.

## Session and token design

Transport sessions use TLS plus application-layer encryption derived from the
paired device and agent keys. Session keys are rotated and have short lifetimes.
Long-lived identity private keys never cross devices.

An encrypted session token is:

- audience-bound to one local agent;
- device-bound to one public key;
- capability- and project-scoped;
- short-lived;
- revocable;
- protected from replay by a monotonic counter and nonce; and
- insufficient by itself to approve a hazardous action.

Browser storage contains only non-exportable key references, encrypted minimal
settings, and non-sensitive UI preferences. The PWA does not cache plaintext
goals, project content, diffs, approval manifests, or event history by default.

## Capability permissions

Capabilities use deny-by-default grants with explicit project and action scope.

| Capability class | Default mobile behavior | Examples |
|---|---|---|
| Observe metadata | Allowed after pairing | Project status, agent readiness, run state |
| Read scoped content | Allowed only within granted scope | Named file summary, reviewed artifact |
| Analyze | Allowed within existing read/provider/budget grants | Plan, compare, classify |
| Generate no-effect output | Allowed | In-app draft, proposed patch, release-note draft |
| Write local files | Exact confirmation required | Apply patch, create document, rename file |
| Execute side-effecting command | Exact confirmation required | Formatter that rewrites files, migration |
| Delete or overwrite | High-risk confirmation | Remove file, discard candidate |
| Remote Git action | High-risk confirmation | Push exact SHA, open PR, merge, tag |
| Deploy/publish/message | High-risk confirmation | Deploy service, create release, post content |
| Financial action | High-risk confirmation and separate policy | Purchase, transfer, trade, paid commitment |
| Permission or privacy widening | High-risk confirmation | New project, provider, data class, network scope |

“Generate” means producing an in-app candidate. Persisting that candidate to a
project is a write and requires confirmation under the default policy.

## Approval security

An approval is a signed, one-time authorization for one canonical action
manifest. It includes:

- action type and schema version;
- project and resource identifiers;
- exact file/path set or remote target;
- immutable input digest, candidate SHA, or artifact digest;
- maximum cost and deadline;
- side-effect summary and rollback boundary;
- policy version;
- nonce, issue time, and short expiry; and
- approving device/key ID.

The local agent recomputes the manifest immediately before execution. Any
change invalidates the approval. Approval cannot be transferred to another
task, project, branch, remote, provider, cost ceiling, or action class.

High-risk confirmation UI must:

- name the effect with a verb, such as “Push” or “Delete”;
- show the exact target and immutable input;
- distinguish local preparation from remote publication;
- show unknown or maximum cost;
- avoid preselected confirmation; and
- require device-local authentication when supported.

Models cannot approve their own proposals. A reviewer decision is not an action
approval, and an action approval is not a quality review.

## Secret and personal-data handling

Provider adapters use existing local credential stores. FlowFoundry may expose
only readiness, credential-source names, and safe setup actions to the mobile
client.

Before any content crosses the computer boundary, policy determines:

1. whether the phone is allowed to receive that data class;
2. whether the specific artifact is required for the current view;
3. whether local redaction or summarization is sufficient;
4. whether the transport session is valid; and
5. whether retention on the phone is permitted.

The default event stream contains status and evidence references, not raw model
transcripts, chain-of-thought, unrestricted command output, or entire files.

Push notifications contain only a non-sensitive event class and opaque wake-up
identifier. Opening the app requires a fresh authenticated fetch.

## Network security

- Bind local control services to loopback or a controlled local socket by
  default.
- Do not enable port forwarding, UPnP, or unauthenticated LAN discovery.
- Use HTTPS/WSS with modern TLS for all network transport.
- Encrypt application payloads end to end between paired devices.
- Pin the paired agent identity at the application layer.
- Rate-limit pairing, commands, approvals, and artifact access separately.
- Apply strict message size, schema depth, and event replay bounds.
- Treat the relay as untrusted and replaceable.

Local direct mode uses an authenticated certificate/fingerprint established by
pairing. A change in agent identity stops the connection and requires explicit
re-pairing; it is never accepted as a routine certificate refresh.

## Local execution safeguards

- Typed commands map to trusted functions; no arbitrary mobile shell exists.
- Paths are resolved beneath an authorized project and checked against symlink
  and traversal escape.
- Write-capable AI tasks use managed Git worktrees where supported.
- Provider and workspace preflight occur after approval and immediately before
  execution when state may have changed.
- The action input is re-hashed before effect.
- Durable idempotency prevents duplicate effects after reconnect or crash.
- Cancellation is verified against process identity before signalling.
- Partial and failed candidates are retained for review according to policy.

## Audit and retention

The computer records device changes, command receipts, policy decisions,
approval manifests/digests, action results, revocations, and security events.
Audit records use restrictive permissions and redact content not required to
prove the decision.

Users can configure retention, export audit evidence, and delete mobile pairing
history subject to any explicit compliance policy. Deleting personal context
does not silently delete release or security evidence; the UI distinguishes
these data classes.

## Revocation and recovery

- Revocation is effective locally immediately and synced to the relay as an
  encrypted routing update when connectivity returns.
- A revoked key cannot create a new session or approve an existing proposal.
- Lost-phone recovery requires local computer access or a separately enrolled
  recovery device; provider credentials are not rotated through the phone.
- Suspected agent-key compromise invalidates all pairings and requires a new
  agent identity.
- Clock anomalies fail closed for approvals and pairing invitations.

## Security test plan

Required automated tests:

- QR invitation expiry, replay, race, and single-use behavior;
- wrong fingerprint and short-authentication-string mismatch;
- signature, audience, key ID, counter, nonce, and expiry failures;
- revoked-device reconnect and pending-approval rejection;
- duplicate command and crash-at-each-commit-boundary idempotency;
- action digest mismatch after file, SHA, ref, target, or cost change;
- project path traversal, symlink escape, and artifact-handle guessing;
- event replay gaps, oversized payloads, and schema fuzzing;
- relay plaintext inspection and metadata inventory;
- service-worker/cache inspection for prohibited content;
- notification-content privacy;
- provider credential-value redaction; and
- disconnect, stale state, cancellation uncertainty, and clock skew.

Required independent review before remote MVP:

- pairing and cryptographic protocol review;
- capability/approval bypass review;
- PWA storage and origin-security review;
- relay and deployment hardening review; and
- privacy threat-model review using synthetic fixtures only.

## Security release gates

The mobile MVP is blocked until:

- there is no public local port in the default installation;
- cryptographic dependencies and protocol choices have an explicit maintenance
  owner and external review;
- all hazardous actions are covered by exact approvals and negative tests;
- the relay can be replaced without changing device identity or losing local
  audit state;
- phone loss and device revocation are tested end to end;
- no secret or prohibited content appears in client storage, relay logs,
  notifications, analytics, screenshots, or crash reports; and
- a fresh local-only mode remains useful with the relay disabled.

## Security decision record

| Decision | Reason | Risk | Verification |
|---|---|---|---|
| No public local port | Reduce internet attack surface | Relay dependency for remote use | Port scan and deployment tests |
| Provider secrets stay local | Limit credential blast radius | Some setup cannot be mobile-only | Storage and traffic inspection |
| Exact one-time approvals | Prevent confused-deputy actions | Approval friction | Bypass tests and usability study |
| Typed commands, no shell | Bound authority | Smaller initial feature set | Schema fuzzing and source review |
| E2EE through relay | Treat relay as untrusted | Protocol complexity | Independent cryptographic review |
