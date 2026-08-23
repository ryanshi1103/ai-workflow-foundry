# Current Status

Last audited: 2026-08-23
Candidate: `release/v0.2.0-alpha.1-candidate`
Package version: `0.2.0a1`

FlowFoundry is an **Alpha developer preview** of a local-first coordination
runtime for bounded AI workflows. It is not a production personal AI manager.

## Implemented and test-backed

- rule-based task profiling and explainable `single_agent`,
  `single_agent_reviewer`, and bounded `multi_agent` planning;
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
- a deterministic Personal AI Manager builder/reviewer demo.

## Experimental

- real-provider parity, live Meeting coverage, and provider-version stability;
- provider-reported token/cost aggregation and simple performance history;
- operator experience outside the terminal; and
- universal integration across components with separate dependency surfaces.

## Planned, not claimed

- personal semantic memory, preference learning, and cross-session retrieval;
- general local-model and external-plugin ecosystems;
- learned quality/price/latency optimization;
- automatic merge, push, pull-request, release, or deployment actions; and
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

See:

- [Sanitization Report](SANITIZATION_REPORT.md)
- [License Decision](LICENSE_DECISION.md)
- [Launcher EOF Compatibility](launcher-eof-compatibility.md)
- [90-second Personal AI Manager demo](demos/personal-ai-manager-demo.md)
- [Final Release Report](../FINAL_RELEASE_REPORT.md)

The final report is authoritative for exact test, package, clean-clone, and
remaining external-gate results.
