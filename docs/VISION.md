# Vision

## Models are tools. Intelligence comes from coordination.

The AI ecosystem is moving from one general model toward many specialized
models, tools, data sources, and execution environments. This creates more
capability, but it also creates a management problem: users must decide what to
trust, what context to share, what a task may cost, which tool may act, how to
review the result, and what to do when a workflow fails.

FlowFoundry's thesis is that the next useful layer is not another chat window.
It is a coordination layer that translates a human goal into a bounded,
reviewable workflow across the capabilities already available.

## Why coordination matters

No model is best for every task. A coding model, a long-context model, a local
private model, and a deterministic program make different tradeoffs. Sending
every problem to one provider can waste money, expose unnecessary context, and
produce results that are difficult to validate.

A coordination layer can make those tradeoffs explicit:

- use the minimum number of model calls needed for the goal;
- select capabilities by task fit, availability, privacy, latency, and cost;
- expose only the tools and permissions a step requires;
- pass bounded, traceable context between stages;
- keep AI proposals separate from trusted side effects;
- insert human judgment where consequences or ambiguity justify it;
- preserve enough state to review, resume, retry, or stop safely.

Coordination does not make models infallible. It creates an engineering system
around probabilistic tools.

## Why personal AI systems matter

An isolated model knows only what a prompt contains and what its training makes
available. A valuable personal AI system can instead work with user-controlled
context:

- current goals and active projects;
- preferences and working patterns;
- approved knowledge and historical decisions;
- available models, tools, compute, time, and budget;
- privacy rules and retention choices;
- feedback about what helped and what failed.

The value is not that the system becomes a digital human replacement. The
value is that it reduces repeated coordination work while keeping the person in
control.

## Product principles

### Human authority

The human defines the goal, controls sensitive context, and retains authority
over consequential actions. Review and execution approval are separate when
the risk requires it.

### Minimum sufficient path

A simple task should remain simple. FlowFoundry should use one agent when one
agent is enough, add review when risk or uncertainty warrants it, and use a
team only when independent expertise materially improves the outcome.

### Local-first, not local-only

State, policy, and workflow ownership should remain local by default. Remote
models can be valuable, but their use must be declared and bounded. Local
models should be first-class where hardware and quality permit.

### Honest evidence

Unknown cost is unknown. An installed provider is not necessarily ready. A
model-produced answer is not a verified artifact. Maturity labels and release
claims must be supported by code, tests, and operational evidence.

### Replaceable providers

Provider-specific advantages should be usable without making user workflows
hostage to one model vendor. Capabilities and contracts are the durable layer;
adapters are replaceable.

### Recoverable operation

Useful AI workflows will fail. Durable state, immutable inputs, candidate
isolation, idempotency, partial outputs, and clear operator actions matter as
much as successful generation.

## Long-term outcome

The long-term direction is a **Personal Intelligence Infrastructure** in which
models, tools, knowledge, workflows, and resources are coordinated around the
person's goals:

```text
Human goals and authority
          │
          ▼
Personal AI Manager
          │
          ├── Models: cloud, specialized, and local
          ├── Tools: code, documents, data, automation, communication
          ├── Context: projects, knowledge, preferences, decisions
          ├── Resources: money, time, compute, quota, privacy
          └── Controls: policy, review, approval, audit, recovery
```

Intelligence in this system is not claimed to live inside one orchestration
algorithm. Useful behavior emerges from **coordination + context + experience +
feedback**, bounded by human intent and engineering controls.

## What this vision does not claim

FlowFoundry is not an AGI project, a benchmark claim, or a plan to eliminate
human responsibility. It does not assume autonomous execution is always
desirable. The current implementation is an Alpha coordination foundation; the
personal context and adaptive-manager layers remain roadmap work.

See [Current Status](CURRENT_STATUS.md) for the implemented boundary and
[Roadmap](ROADMAP.md) for staged acceptance criteria.
