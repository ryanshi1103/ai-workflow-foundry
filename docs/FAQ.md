# FlowFoundry Alpha FAQ

## What is FlowFoundry?

FlowFoundry is a Local-first Adaptive AI Team Runtime. Its current Alpha is a
coordination layer that helps a human organize the minimum sufficient path
across supported models, tools, workflows, permissions, costs, evidence, and
approval boundaries around a goal.

## Is it another AI model or chatbot?

No. FlowFoundry does not train or replace a model. It coordinates eligible
resources and preserves workflow state and evidence. Models still provide model
capability; the human still owns the goal and consequential decisions.

## How is it different from ChatGPT, Claude, or Copilot?

Those products provide assistant or coding capability. FlowFoundry's emphasis
is the path around a project goal: planning, routing, permissions, execution,
review, recovery, evidence, and approval. This is a difference in emphasis, not
a claim that other products cannot use tools or coordinate work.

## Does the Alpha call Claude, Codex, or DeepSeek during the demo?

No. The first external-user workflow uses deterministic fake providers. Names
such as `claude-architect`, `codex-builder`, and `deepseek-reviewer` are offline
routing identities. Live provider use requires local configuration and explicit
opt-in and is not equally verified across providers.

## Why use fake providers in the first demo?

They make planning, routing, persistence, review, recovery, cost-state handling,
and approval behavior reproducible without credentials, network variability, or
a model bill. They do not prove live model quality or provider parity.

## Does “completed_with_blockers” mean the demo failed?

Not in the GitHub Release Assistant. The final package task intentionally stops
at `skipped_pending_human`. That shows the human approval boundary is working.

## Will FlowFoundry modify or publish my repository?

The official first-user demo does not. Current public Alpha policy does not
automatically merge, push, tag, deploy, publish, spend money, or widen
permissions. Any future consequential action must remain explicitly scoped and
approved.

## Does FlowFoundry store API keys?

The offline workflow needs none. Do not put credentials into project files,
fixtures, issues, or recordings. Provider runtimes keep their own credential
boundaries; FlowFoundry documentation and status output must never expose
credential values.

## Is the Mobile AI Command Center available?

No. Mobile and PWA documents are designs. There is no shipped mobile client in
this Alpha.

## Does personal memory exist?

No complete personal semantic-memory or preference-learning system is shipped.
Operational run state and limited performance history are not the Personal AI
Assistant or Personal AI OS described in future strategy.

## Can I install without network access?

Runtime use of the official offline demo needs no provider network call. Source
installation may need the declared build backend. A verified offline install
requires the final reviewed wheel and hash; that release evidence is currently
pending.

## Which Python versions are supported?

The package declares Python 3.11 or newer. Public support claims require the
final artifact to pass the published environment matrix. Python 3.11 is the
mandatory Alpha install target.

## Where is run evidence stored?

Team commands use a local runs root and persist plan/task/review/report state.
The exact location is shown by the CLI and demo documentation. Treat run output
as project data; review it before sharing.

## How do I repeat the first workflow?

Use a new run ID. Existing IDs are durable and should be inspected rather than
deleted simply to repeat the tutorial.

## Is FlowFoundry production ready?

No. It is an Alpha developer preview. Final artifact, external-install, demo,
security-review, and first-user evidence remain release gates.

## What feedback is most useful?

Report the exact candidate/artifact identity, sanitized failed command, platform
and Python version, whether the product boundary was clear, and whether the
workflow evidence helped. Never post credentials or private project content.

## How can I contribute?

Start with [CONTRIBUTING.md](CONTRIBUTING.md) and one of the five proposed
[Good First Issues](GOOD_FIRST_ISSUES.md). Security concerns must follow the
private process in [SECURITY.md](../SECURITY.md).
