# Marketing Launch Plan

Status: preparation only; no publication or announcement is authorized

## Objective

Earn the first group of trusted users who can explain FlowFoundry, complete the
offline workflow, understand the human approval boundary, and offer useful
feedback. Stars and impressions are secondary signals.

## Message

> One goal. The smallest sufficient AI team.

> AI is moving from individual models to coordinated systems.

> Do not chase every new model. Build a system that coordinates them.

FlowFoundry is a Local-first Adaptive AI Team Runtime. Its current Alpha is a
coordination layer for goals, models, tools, permissions, costs, evidence,
human decisions, and recovery. It does not replace models or people; it makes
a bounded minimum-sufficient workflow visible and reviewable.

## Audience and reason to care

| Audience | Existing problem | First proof | Invitation |
|---|---|---|---|
| Developers and AI builders | Coding, review, tests, and release authority live in separate tools | GitHub Release Assistant reaches a visible human stop | Reproduce the workflow and improve CLI/tests/docs |
| Students | Too many AI tools and repeated setup make learning workflows hard to reason about | Deterministic offline path shows goal→plan→evidence | Improve tutorials and first-install guidance |
| Researchers | Agent claims often lack provenance, controls, and reproducibility | Exact fixture, durable state, and explicit limitations | Improve evaluation, evidence, and trust methods |
| Automation users | Side effects, permissions, and recovery are hard to audit | Approval/recovery state and no-auto-publish boundary | Report a real bounded workflow need |

## Channel sequence

### 1. GitHub

Publish only after release gates close: concise README, exact artifact/source
identity, 90-second demo, installation evidence, limitations, security route,
and curated issues. The main conversion is a successful offline workflow.

### 2. Hacker News

Lead with the technical insight and architecture tradeoff. Title direction:
“FlowFoundry: a local-first coordination layer for AI tools.” Be present for
questions about overlap with agent frameworks, current limitations, and why
review differs from approval.

### 3. Reddit

Choose communities where local AI, developer tooling, automation, or agent
orchestration is on-topic. Share the reproducible demo and ask a concrete
question about fragmented workflows. Do not cross-post identical promotional
copy or hide the Alpha boundary.

### 4. X

Use the 30-second flow: fragmented tools → one bounded goal → coordinated roles
→ evidence → human approval. Link to the demo or repository, not a star request.

### Student and learning communities

Lead with transparent workflow design and offline experimentation, not a claim
that the future personal learning assistant exists. Offer a tutorial task and a
feedback form that collects no private study content.

## Content sequence

1. **Problem post:** why more models create more coordination work.
2. **Demo video:** one developer release goal, visible roles, evidence, stop.
3. **Technical deep dive:** minimum sufficient path, review vs approval,
   recovery, and Git isolation.
4. **Trust post:** fake-provider evidence, limitations, and what remains
   unverified.
5. **Contributor story:** a first issue from problem to tested pull request.
6. **Validation update:** what the first ten users could and could not do.

## Asset requirements

- exact-SHA 90-second recording, transcript, poster, and manifest;
- 30-second clip derived from the same recording;
- real terminal captures for goal/plan, evidence/review, and approval stop;
- architecture and roadmap diagrams labeled by maturity;
- independently verified installation recording; and
- approved GitHub description and channel copy.

No placeholder, concept, or rendered preview may be presented as a live product
capture.

## Launch gates

Marketing waits until the Alpha Release Checklist authorizes publication and:

- CI passes for the exact candidate;
- wheel/sdist hashes and provenance are verified;
- external clean installs succeed;
- artifact security/SBOM/notice review closes;
- the flagship recording is real, sanitized, and accessible;
- private security reporting and maintainer response ownership are active; and
- a separately authorized announcement window exists.

## First 30 days

| Time | Focus | Evidence |
|---|---|---|
| Days 1–3 | Limited developer cohort | comprehension, install blocker, first workflow |
| Days 4–10 | Fix documentation and distribution friction | time-to-first-result and categorized failures |
| Days 11–20 | Technical content and contributor onboarding | repeat use and one reviewable first contribution |
| Days 21–30 | Broader developer/research outreach if gates stay green | retention, workflow requests, safety feedback |

Stop promotion for any critical security/privacy/data-loss issue, misleading
claim, widespread install failure, or maintainer-capacity gap. Fix the evidence
before expanding the audience.
