# Current Status

Last audited: 2026-08-27
Candidate ref: `release/v0.2.0-alpha.1-reconciled-candidate`
Protected productization ancestor: `e9692132c20285b348b261d3483c9ae04cfd362e`
Decision Inheritance integration base: `10991edd9c8c38c9c13020e5fc1cc99f0bb7cdd9`
Reconciled candidate SHA: **the commit containing this document; resolve with
`git rev-parse HEAD`; not yet owner-approved or published**
Package version: `0.2.0a1`

FlowFoundry is an **Alpha developer preview** of a local-first coordination
runtime for bounded AI workflows. It is not a production personal AI manager.

## Implemented and test-backed

- rule-based task profiling and explainable `single_agent`,
  `single_agent_reviewer`, and bounded `multi_agent` planning;
- bounded Meetings with one Context Pack, independent Round 1 views,
  deterministic conflict detection, targeted Round 2, early stop, and
  preserved unresolved dissent;
- read-only Decision Inheritance that validates a 36-entry ledger, selects
  applicable `BINDING`/`ADOPTED` decisions by exact domain/surface/scope,
  injects exact authoritative wording before task or Meeting reasoning, and
  warns on occupied semantic slots without automatic write-back;
- deterministic offline fake providers, dependency scheduling, review,
  approvals, retry, resume, cancellation, durable state, and reporting;
- explicit real-provider opt-in with runtime/profile/workspace preflight;
- Git-isolated writer candidates with immutable bases and conservative cleanup;
- workspace selection, explicit permission profiles, session recovery, and an
  adaptive terminal launcher with a preserved line-oriented compatibility path;
- four public component manifests, two workflow contracts, and thirteen
  registered capabilities;
- media-skill contracts, a sanitized private-MediaFlow boundary, and a
  deterministic nameplate workflow; and
- deterministic Personal AI Manager and GitHub Release Assistant fixtures; the
  release-assistant path stops at a synthetic `release` approval gate.

## Experimental

- real-provider parity, broad live-provider Meeting coverage, and
  provider-version stability;
- provider-reported token/cost aggregation and simple performance history;
- operator experience outside the terminal; and
- universal integration across components with separate dependency surfaces.

## Planned, not claimed

- personal semantic memory, preference learning, and cross-session retrieval;
- general local-model and external-plugin ecosystems;
- learned quality/price/latency optimization;
- automatic merge, push, pull-request, release, or deployment actions;
- automatic decision promotion, Human approval, supersession, or ledger
  write-back; and
- a polished cross-device Personal AI Manager interface.

## Candidate boundaries

- The candidate is a new-root allowlist snapshot and does not descend from the
  preserved incident-bearing migration history.
- Feedback Intelligence and its Customer Intelligence demo are excluded because
  no approved publication license was provided.
- Offline demo agent names are routing identities. They are not evidence of a
  cloud call; official demos do not enable a real provider.
- No push, merge, tag, release, protected-branch change, frozen-candidate change,
  or remote incident action was performed.

## Release evidence

The reconciled source tree passes 22 focused Decision Inheritance tests, 250
foundation tests, 90 workspace tests, 26 launcher unit checks, 40 launcher
EOF/permission checks, 4 deploy checks, and 3 tests each for Confera and
Nameplate. Exact committed-SHA artifact/install results are recorded outside
the source tree in the candidate-specific local release-evidence directory.
Remote CI, independent review, and release recording remain open. Older
package artifacts and hashes must not be reused for this candidate.

See:

- [Sanitization Report](SANITIZATION_REPORT.md)
- [License Decision](LICENSE_DECISION.md)
- [Launcher EOF Compatibility](launcher-eof-compatibility.md)
- [90-second GitHub Release Assistant demo](demos/github-release-assistant.md)
- [Alpha Release Checklist](ALPHA_RELEASE_CHECKLIST.md)
- [Limitations](LIMITATIONS.md)
- [Final Release Report](../FINAL_RELEASE_REPORT.md)

The Alpha Release Checklist is authoritative for GO/NO-GO. The final report
provides detailed baseline test, package, clean-clone, and external-gate
evidence.
