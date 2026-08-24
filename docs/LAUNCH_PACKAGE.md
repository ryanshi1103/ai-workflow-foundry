# FlowFoundry Alpha Launch Package

Status: **DRAFT — DO NOT PUBLISH**
Target: GitHub Release for `v0.2.0-alpha.1`
Authority: this document does not authorize a push, tag, merge, release, or
protected-ref change

Use this copy only after every required gate in the
[Alpha Release Checklist](ALPHA_RELEASE_CHECKLIST.md) is complete for the same
exact candidate SHA.

## GitHub Release title

**FlowFoundry v0.2.0-alpha.1 — local-first AI coordination**

## Developer Preview disclaimer

> **Developer Preview / Alpha.** FlowFoundry's deterministic offline
> coordination path is runnable and tested, but this release is not production
> ready. Real-provider parity is incomplete. The mobile command center and
> personal-memory layers are not implemented. Review permissions, evidence, and
> limitations before using FlowFoundry with a real project or provider.

## Release description

### Problem

AI work is becoming fragmented across models, coding tools, local runtimes,
projects, permissions, costs, and interfaces. A user still has to move context,
choose the right tool, combine outputs, verify evidence, and decide which action
is safe.

More models do not remove that coordination burden.

### Solution

FlowFoundry is a local-first AI coordination layer. It turns a bounded goal into
an inspectable workflow across eligible models and deterministic tools, with
explicit planning, routing, review, approval, recovery, cost evidence, and Git
isolation.

FlowFoundry does not replace ChatGPT, Claude, Copilot, Codex, DeepSeek, or local
models. It coordinates eligible intelligence resources around the user's goal
and preserves human authority over consequential actions.

### What works in this Alpha

- rule-based goal profiling and minimum-sufficient-path planning;
- explicit DAG and bounded multi-agent execution;
- deterministic offline fake-provider workflows;
- Claude, Codex, DeepSeek-compatible, and local routing identities;
- structured review and human approval gates;
- durable status, reports, retry, resume, cancellation, and recovery;
- provider and workspace preflight;
- Git-isolated writer candidates; and
- reusable component, capability, and workflow contracts.

Routing identities in offline demos do not mean the named cloud provider was
called.

### Demo

The 90-second **GitHub Release Assistant** asks:

> Prepare a reviewable GitHub release evidence package. Do not push, tag,
> deploy, publish, or enable a real provider.

FlowFoundry validates the explicit plan, routes planning and code-oriented
stages, records a synthetic security review and test-stage result, preserves
evidence, and stops at `skipped_pending_human` before the scoped `release`
approval.

The demo proves coordination, persistence, review, and the approval lifecycle.
It does not inspect the repository, run the project's real tests, build release
artifacts, write release notes, push, tag, deploy, or publish.

Demo guide: [GitHub Release Assistant](demos/github-release-assistant.md)

### Installation

Requirements: Python 3.11 or newer and Git.

Run these commands only after the immutable tag is published and independently
verified:

```bash
git clone --branch v0.2.0-alpha.1 --single-branch \
  https://github.com/ryanshi1103/ai-workflow-foundry.git flowfoundry
cd flowfoundry

python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install .

flowfoundry validate
flowfoundry team plan examples/personal-ai/github-release-assistant.json
flowfoundry team run examples/personal-ai/github-release-assistant.json \
  --run-id first-workflow
flowfoundry team report first-workflow
```

Expected validation summary:

```text
validated 4 FlowFoundry components
validated 2 workflow contracts
validated 13 registered capabilities
```

This path uses deterministic fake providers and needs no provider credentials or
billed model calls.

### Limitations

The canonical list is [Alpha Limitations](LIMITATIONS.md). In summary:

- This is an Alpha developer preview, not a production personal assistant.
- Real-provider setup, versions, usage reporting, and parity are incomplete.
- The official offline demos produce synthetic task outputs, not model-quality
  evidence.
- FlowFoundry does not automatically merge, push, open a pull request, release,
  deploy, publish, spend money, or widen permissions.
- General local-model and external-plugin ecosystems are not implemented.
- The Mobile AI Command Center and iPhone PWA are designs, not shipped software.
- Personal semantic memory, preference learning, and Personal AI OS capabilities
  are future work.
- Feedback Intelligence and its Customer Intelligence demo are excluded from
  this release because approved publication licensing was not available.

### Roadmap

1. **Current — AI Coordination Layer:** stabilize installation, contracts,
   evidence, and first external workflows.
2. **Future — Personal AI Assistant:** add consent-based personal context and a
   securely reviewed control interface.
3. **Long-term future — Personal AI OS:** coordinate portable tools, context,
   policies, and resources while retaining human authority.

Future stages are evidence gates, not release promises.

### Feedback requested

The most useful Alpha feedback is:

- exact sanitized install failure;
- whether routing and permissions were understandable;
- whether status/review/report evidence helped;
- whether fake and live provider modes were clear;
- which existing workflow would create repeat usage; and
- one small documentation, fixture, test, or CLI improvement.

Do not include credentials, private repository content, personal paths, raw
provider output, or customer data in public issues.

## Release links to populate after GO

- Source tag: `TBD`
- Candidate commit: `TBD`
- Wheel and sdist: `TBD`
- SHA-256 manifest: `TBD`
- CI evidence: `TBD`
- Security and license evidence: `TBD`
- Demo video and transcript: `TBD`
- Known issues: `TBD`
- Contribution guide: [Contributing](CONTRIBUTING.md)
- Current status: [Current Status](CURRENT_STATUS.md)

Never publish the draft with a `TBD` release-evidence field.

## Asset checklist

- [ ] Exact candidate SHA is approved and clean.
- [ ] GitHub Actions pass on that SHA.
- [ ] Wheel/sdist names and hashes match that SHA.
- [ ] Artifact install succeeds outside the source tree.
- [ ] Security, history-containment, and license gates are closed.
- [ ] At least five external clean installs succeed.
- [ ] Demo video, captions, transcript, and poster are reviewed.
- [ ] Known issues and maintainer response ownership are published.
- [ ] Every link above resolves anonymously.
- [ ] Owner explicitly authorizes tag and release publication.
