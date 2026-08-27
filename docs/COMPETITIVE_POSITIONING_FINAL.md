# Competitive Positioning — Final Public Frame

Status: **category positioning for the Alpha launch**. This comparison explains
where FlowFoundry fits; it is not a benchmark, feature-completeness claim, or
assertion that every named product integrates with the current release.

## Positioning statement

> FlowFoundry is a Local-first Adaptive AI Team Runtime. Its current Alpha is a
> coordination layer that helps people manage models, tools, workflows,
> permissions, costs, evidence, and human approvals around a goal.

AI is moving from individual model interactions toward systems that coordinate
multiple intelligence resources. FlowFoundry does not attempt to replace those
resources. It gives the human a project-centered control and evidence layer
around them.

## Category comparison

| Category | Primary job | What it does well | Where FlowFoundry fits | What FlowFoundry does not claim |
|---|---|---|---|---|
| AI assistants | Help a user converse, research, write, analyze, or complete tasks through an assistant experience | Strong general interaction and model capabilities | Coordinates bounded roles, local project context, permissions, evidence, and approval around a goal that may use assistant/provider resources | That assistants cannot coordinate tools, or that FlowFoundry is a smarter model or replacement assistant |
| Agent frameworks | Let developers construct agent graphs, conversations, routing, tools, and application-specific orchestration | Flexible primitives for building multi-agent applications | Provides an opinionated user-facing workflow emphasizing project discovery, conservative authority, review, recovery, cost state, and Git isolation | That FlowFoundry is the first or only coordination framework, or that it replaces framework-level extensibility |
| Developer copilots | Help developers understand, write, review, and modify code inside development workflows | Deep code assistance and IDE/terminal integration | Can assign development and review responsibilities within a broader goal, then collect evidence and preserve the human approval boundary | That it replaces code assistants, produces better code by default, or currently integrates every copilot product |
| Workflow automation | Connect triggers, applications, data, and repeatable actions | Deterministic integration and business-process automation | Adds goal interpretation, AI-resource selection, review evidence, approval gates, and recovery to bounded local workflows | That conventional automation lacks approvals, or that FlowFoundry is a general replacement for integration platforms |

## The difference in one question

Many AI products begin with:

> Which model or assistant should handle this interaction?

FlowFoundry begins with:

> What is the goal, what capabilities and resources are available, what may
> they do, what will it cost, and what evidence must a human review?

This is a difference in product emphasis, not a claim that other categories
cannot implement planning, tools, routing, memory, or human approval.

## Relationship, not replacement

FlowFoundry can conceptually treat models, local tools, and project workflows
as coordinated resources. That statement does not mean the current Alpha has
an adapter for every assistant, framework, copilot, or automation service.
Named integration support must always be demonstrated by the current source,
tests, and documentation.

The product relationship is:

```text
Human goal and constraints
          |
FlowFoundry coordination, permission, evidence, approval
          |
Supported models, tools, project workflows, and local data boundaries
```

The human remains responsible for goals and material side effects.

## Public messages by context

### One sentence

FlowFoundry is a Local-first Adaptive AI Team Runtime for the smallest
sufficient path across models, tools, workflows, permissions, costs, evidence,
and human approvals around a goal.

### Thirty seconds

Using more AI tools creates a coordination problem: context is fragmented,
side-effect authority is unclear, and evidence has to be assembled manually.
FlowFoundry adds a local project-centered layer that plans bounded work,
coordinates supported resources, collects review evidence, preserves recovery
state, and asks the human before sensitive actions.

### Developer frame

Use FlowFoundry when the hard part is no longer generating one answer but
coordinating a repeatable project workflow with explicit permissions, evidence,
and recovery. Continue using the models, code assistants, frameworks, and tools
that fit the job; FlowFoundry's role is to manage the path around the goal.

## Safe competitive language

Use:

- “different product emphasis”;
- “local-first coordination and evidence layer”;
- “works around supported resources”;
- “human-controlled side effects”;
- “Alpha capability with documented limits.”

Avoid:

- “the only coordinator” or “the first agent system”;
- “safer than” without a comparable security evaluation;
- “cheaper” or “better quality” without reproducible measurements;
- “replaces ChatGPT, Claude, Copilot, LangGraph, AutoGen, or CrewAI”;
- “supports everything” or language implying unimplemented adapters;
- “autonomous employee,” AGI, or replacement of people.

## Current Alpha boundary

The current product is the **AI Coordination Layer**. The Mobile Command Center
is **designed, not shipped**. Personal memory, personalized intelligence, and a
Personal AI OS are **future**. Competitive copy must lead with the current
layer and may discuss later stages only after this boundary is explicit.

For product-level comparisons with ChatGPT, Claude, GitHub Copilot, LangGraph,
AutoGen, and CrewAI, including official-source links checked during the launch
review, use [POSITIONING.md](POSITIONING.md) as the canonical detailed
reference. Re-check those external descriptions immediately before publication
because competing products change over time.
