# Public Website Structure

Status: **launch information architecture only**. This document does not imply
that a public website has been built or deployed.

## Website job

The website should move a visitor through one evidence-backed path:

1. understand the problem in 10 seconds;
2. understand FlowFoundry's role in 30 seconds;
3. see credible evidence in one minute;
4. decide whether to try it, follow it, or contribute.

The primary audience is developers. Students, researchers, automation users,
and prospective contributors are secondary audiences. The primary conversion
is a successful local install and first workflow, not a page view or a star.

## Global content rules

- Lead with the current coordination layer, not the Personal AI OS vision.
- Label every capability **Implemented**, **Experimental**, or **Future**.
- Use only captures made from an identified release candidate.
- Label diagrams and mobile concepts as explanatory or conceptual artwork.
- Put the Developer Preview limitations near the first installation action.
- Never imply that a mobile app, personal memory, unrestricted autonomy, or an
  integration exists when it does not.
- Link security, limitations, source, and reproducible verification as closely
  as possible to the claim they qualify.

## Homepage structure

### Hero

**Message**

> AI is moving from individual models to coordinated systems.

FlowFoundry is a local-first AI coordination layer that helps people manage
models, tools, workflows, permissions, costs, evidence, and human approvals
around a goal.

**Goal:** Make the category and product boundary understandable without
scrolling.

**Target audience:** Every visitor, especially developers arriving from GitHub
or a demo link.

**Required visual:** A small explanatory flow: `Goal -> Plan -> Coordinated
resources -> Evidence -> Human approval`. It must be labeled as a diagram, not
a product screenshot.

**Required evidence:** Link to the flagship demo, current capability matrix,
and exact-version installation instructions. Show the Alpha/Developer Preview
label above the fold.

**Actions:** `Watch the 90-second demo`, `Try the offline workflow`, and `View
source on GitHub`. Do not make `Star` the primary action.

### 1. Problem

**Goal:** Show the human cost of coordinating separate AI tools: repeating
context, manually moving outputs, tracking permissions, and reconstructing
evidence.

**Target audience:** Developers and technical users who already use more than
one assistant or tool.

**Required visual:** A clearly labeled problem diagram showing disconnected
models, terminals, documents, and approval decisions.

**Required evidence:** One real, bounded workflow in which the same project
goal requires planning, execution, review, and approval. Avoid market-size or
productivity claims without independent evidence.

### 2. Why AI workflows become fragmented

**Goal:** Explain that model quality alone does not preserve project state,
control side effects, choose resources, or create an audit trail.

**Target audience:** Users asking why a single chat product is not sufficient.

**Required visual:** A comparison table: `single assistant interaction` versus
`goal-based coordination workflow`.

**Required evidence:** Link each FlowFoundry-side behavior to current docs or a
captured demo step. Describe other product categories accurately; do not claim
they are incapable of coordination.

### 3. How FlowFoundry works

**Goal:** Turn the product idea into a six-step observable workflow: discover,
plan, assign, execute, review, approve.

**Target audience:** Prospective users deciding whether the workflow matches
their needs.

**Required visual:** A workflow diagram with human approval boundaries and
evidence outputs marked explicitly.

**Required evidence:** An actual offline workflow run tied to an exact source
SHA, including the command, sanitized output, and expected result.

### 4. Architecture

**Goal:** Build technical confidence without making architecture the product
story.

**Target audience:** Developers, security reviewers, and contributors.

**Required visual:** A simplified rendering derived from the canonical
[product architecture](FLOWFOUNDRY_PRODUCT_ARCHITECTURE.md): runtime,
coordination, context boundary, and interfaces.

**Required evidence:** Links to the source modules, architecture documentation,
test evidence, and current limitations. Future personal-context and mobile
layers must be visually distinct from shipped layers.

### 5. Real demo

**Goal:** Answer “why do I need FlowFoundry?” through one familiar developer
problem.

**Target audience:** New users, reviewers, and launch-channel visitors.

**Required visual:** The verified 90-second GitHub release-assistant video plus
two actual screenshots and a short terminal GIF.

**Required evidence:** Exact candidate SHA, capture mode, commands, pass/fail
result, sanitization review, and a link to the
[demo script](demos/github-release-assistant.md). Fake-provider mode must be
visible whenever it is used.

### 6. Security model

**Goal:** Explain local-first execution, trust boundaries, permission checks,
approval gates, credential handling, and responsible disclosure.

**Target audience:** Security-conscious users, maintainers, and small teams.

**Required visual:** A trust-boundary diagram showing user, local process,
provider boundary, project workspace, and approval gate.

**Required evidence:** Link to [SECURITY.md](../SECURITY.md), security tests,
known limitations, and the private vulnerability-reporting channel. Do not use
“secure” as an absolute claim.

### 7. Roadmap

**Goal:** Show ambition without presenting designed or future work as shipped.

**Target audience:** Users evaluating project direction and contributors
choosing where to help.

**Required visual:** A three-stage maturity line: current AI Coordination Layer,
future Personal AI Assistant, future Personal AI OS.

**Required evidence:** Acceptance gates for each stage and links to the
[product roadmap](PRODUCT_ROADMAP.md). The Mobile Command Center remains
**Designed**, not implemented.

### 8. Contribute

**Goal:** Give a newcomer a safe, bounded path from checkout to first pull
request.

**Target audience:** Open-source contributors and integrators.

**Required visual:** Day 0 to Day 7 contributor journey.

**Required evidence:** Working contributor commands, labeled good-first issues,
expected maintainer response targets, review policy, license, code of conduct,
and security-reporting path.

### 9. Installation

**Goal:** Let a developer reach a deterministic first result in ten minutes or
identify the exact blocker.

**Target audience:** Users who have decided to try the Alpha.

**Required visual:** A short terminal capture of install, validation, and one
offline workflow.

**Required evidence:** Commands tested from a clean environment against the
published artifact; supported platform and Python matrix; expected output;
artifact hashes; rollback/uninstall steps; and independently recorded timing.
Source-checkout success does not substitute for published-artifact evidence.

## Supporting pages

The minimum supporting routes are:

- `/demo` — video, transcript, exact SHA, commands, and evidence manifest;
- `/install` — clean install, offline first workflow, troubleshooting;
- `/security` — trust model, limitations, disclosure process;
- `/roadmap` — shipped/designed/future boundaries;
- `/contribute` — contributor journey, issues, review expectations;
- `/docs` — canonical documentation index.

These routes may initially be repository-hosted documents. A separate website
is not a launch requirement if the GitHub experience provides the same path.

## Publication gate

The website may be published only when every visible product capture has an
asset manifest, all install commands work from the release artifact, links are
checked, Developer Preview limitations are prominent, and the final candidate
SHA has been independently verified. Until then this structure is **ready for
production work**, while the public site is **not evidenced as ready**.
