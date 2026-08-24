# Visual Product Story

Status: launch-asset specification; no new product architecture
Rule: explanatory diagrams and clearly labeled concepts are allowed; fake
screenshots are not.

## Narrative

The visual story should make one transition obvious:

```text
Disconnected AI tools
        ↓
One bounded coordination layer
        ↓
Human-reviewed evidence and approval
```

The future mobile concept may follow this current-product story, but it must not
be presented as a shipped screen.

## Image 1 — The problem

Purpose: show the coordination burden before showing FlowFoundry.

Content:

- Claude;
- ChatGPT;
- Codex;
- local models;
- separate tools, project context, permissions, costs, and result windows; and
- a developer manually carrying context and checking outcomes.

Suggested composition:

```text
Claude       ChatGPT       Codex       Local model
   \            |            |             /
    \---- manual context, decisions, and checks ----/
                         |
                     Developer
```

Caption: **More AI tools create more coordination work.**

This is an explanatory diagram, not a product screenshot. Do not use provider
logos without checking their current trademark and brand-use requirements.

## Image 2 — FlowFoundry today

Maturity label: **SHIPPED — ALPHA COORDINATION LAYER**

Purpose: show the current product outcome, using the existing architecture and
workflow semantics rather than introducing a new system design.

Content:

```text
Human goal and constraints
           ↓
FlowFoundry coordination
  plan → route → execute → review
           ↓
Evidence → approval boundary → human decision
```

Surround the coordinator with replaceable model/tool labels, not a claim that
all providers are live or equally verified. The final node is a reviewable
candidate or report, not “autonomous completion.”

Caption: **Define the goal. Coordinate the resources. Keep the evidence and
authority visible.**

## Image 3 — Future Personal AI Command Center

Maturity label on the image itself: **DESIGNED CONCEPT — NOT IMPLEMENTED**

Purpose: show the future phone as a human approval and intelligence interface,
not remote desktop.

Allowed concept surfaces:

- project and agent status;
- bounded task creation;
- approval cards;
- execution timeline;
- privacy-safe notifications; and
- clear offline, stale, blocked, and unknown-cost states.

Required relationship:

```text
iPhone PWA concept
        ↓ signed bounded command / approval
Local FlowFoundry agent
        ↓
Projects, tools, and provider runtimes on the computer
```

Do not show credentials, an unrestricted terminal, arbitrary filesystem access,
background hidden work, or a functioning native application.

Caption: **Future concept: approve and understand AI work from the phone while
execution authority remains on the computer.**

## README image requirements

| Asset | Evidence source | Required label | Acceptance criteria |
|---|---|---|---|
| Architecture diagram | Current runtime and canonical architecture docs | Current Alpha | Renders on GitHub; goal, coordination, review, approval, and evidence are legible on mobile |
| Workflow diagram | Verified GitHub Release Assistant event sequence | Synthetic Alpha demo | Matches actual task order and stops at `skipped_pending_human` |
| Mobile future concept | Mobile Command Center and security specifications | Designed concept; not implemented | Visually distinct from screenshots; no fake connectivity or completed task claims |
| Demo screenshots | Exact approved candidate running in a clean terminal | Candidate SHA and fake-provider mode | Actual captured output only; sanitized paths; no credentials; readable at README width |

## Screenshot policy

A screenshot is acceptable only when it was captured from an executable product
surface at the approved candidate SHA. Every screenshot must record:

- source SHA;
- command or UI path;
- fake or real provider mode;
- operating system/terminal context when relevant;
- sanitization review; and
- alt text describing the user outcome.

Illustrations, Mermaid diagrams, wireframes, and storyboards must be labeled by
type. Never crop away a failure, synthetic marker, stale state, or approval
boundary to make the product appear more complete.

The existing launcher preview is a rendered preview derived from a tested TUI
contract; it is already described that way in the README and must not be called
a screenshot.

## Recommended README sequence

1. One-sentence product definition.
2. Image 1: fragmented tools and human coordination burden.
3. Image 2: current FlowFoundry coordination and approval outcome.
4. Actual release-assistant terminal capture or short GIF after recording.
5. Quick Start.
6. Image 3 only within the clearly labeled future-vision section.

## Asset release gate

No visual enters the public README until its source, maturity label, alt text,
and claim boundary have been reviewed. A concept may explain direction; only an
actual capture may prove current behavior.
