# FlowFoundry v0.2.0-alpha.1 launch announcement

Publication status: **Draft**. Publish this announcement only after the release
tag points to the approved candidate, required CI is green, the reviewed wheel
and sdist are attached, and the privacy/security release gate is closed.

## Suggested title

**FlowFoundry v0.2.0-alpha.1: an open, local-first AI coordination layer**

## Announcement copy

AI work is usually bigger than a prompt. A useful result may require choosing a
model, limiting its tools and context, coordinating a builder and reviewer,
validating the output, asking for human approval, and recovering cleanly when a
step fails.

FlowFoundry exists to make that coordination explicit.

Today we are publishing `v0.2.0-alpha.1`, the first public developer preview of
FlowFoundry: an open-source, local-first **AI coordination layer** for bounded AI
workflows. It sits between a human goal and the models, tools, knowledge, and
resources that may help achieve it. The aim is not to replace people or present
one model as universally best. The aim is to choose the smallest sufficient
workflow, expose its permissions and decisions, and leave the human in control.

### What works in this Alpha

- rule-based task profiling and explainable single-agent, agent-plus-reviewer,
  and bounded multi-agent planning;
- deterministic offline execution with fake providers, so planning, scheduling,
  review, retry, resume, cancellation, and reports can be reproduced without a
  network call or model bill;
- explicit opt-in real-provider paths with separate runtime, profile, and
  workspace preflight checks;
- durable run state, human approval gates, conservative recovery, and Git-
  isolated worktrees for write-capable tasks;
- a project launcher with provider profiles, permission controls, and a
  documented line-oriented compatibility path; and
- reusable component manifests, capability declarations, workflow contracts,
  and synthetic reference workflows.

The 90-second Personal AI Manager demo shows the current coordination slice. A
synthetic documentation goal asks for one candidate and an independent review.
FlowFoundry selects a two-step path, scopes the builder to write access and the
reviewer to read access, executes both through deterministic fake adapters, and
preserves a reviewable run report. It does not call a cloud model, modify the
main Git working tree, merge, push, or publish anything.

### What this Alpha does not claim

This is a developer preview, not a production personal assistant. Real-provider
parity remains incomplete. Personal semantic memory, preference learning,
general local-model and plugin ecosystems, learned cost/quality optimization,
and a polished cross-device interface are planned rather than implemented.
FlowFoundry does not automatically merge, push, open pull requests, release, or
deploy. Feedback Intelligence and its Customer Intelligence demo are excluded
from this release because an approved publication license was not available.

### Try the deterministic path

```bash
git clone --branch v0.2.0-alpha.1 --single-branch \
  https://github.com/ryanshi1103/ai-workflow-foundry.git flowfoundry
cd flowfoundry

python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install .

flowfoundry validate
flowfoundry team plan examples/personal-ai/personal-ai-manager.json
```

Requirements are Python 3.11 or newer and Git. The planning command is offline
and does not create run state.

### Developer invitation

FlowFoundry is early enough for contributors to shape its contracts and
operating model. We especially welcome small, test-backed contributions around
provider adapters, orchestration and recovery, permission boundaries, workflow
contracts, privacy, terminal developer experience, documentation, and
deterministic fixtures.

If you try the Alpha, the most useful feedback is concrete: the operating
system and Python version, the exact command, expected and observed behavior,
and sanitized evidence. Please begin large changes with a design discussion and
never place credentials, private transcripts, personal paths, customer data, or
real media in an issue.

- Repository: <https://github.com/ryanshi1103/ai-workflow-foundry>
- Release: <https://github.com/ryanshi1103/ai-workflow-foundry/releases/tag/v0.2.0-alpha.1>
- Demo: [Personal AI Manager](demos/personal-ai-manager-demo.md)
- Current boundaries: [Current Status](CURRENT_STATUS.md)
- Contribution guide: [Contributing](CONTRIBUTING.md)

FlowFoundry's root package is MIT licensed. Included components retain their
documented license boundaries.
