# First 10 Users Validation Simulation

Status: persona-based risk simulation; **not external-user evidence**
Purpose: predict activation failures before recruiting the first ten people

## Method

Each persona starts at the current README, has no maintainer context, and tries
to answer three questions:

1. Is this relevant to my work?
2. Can I install it safely?
3. Can I reach one useful result without credentials?

The findings are hypotheses to test in observed sessions. A simulated persona
does not count toward the first-100-user activation metric.

## 1. AI developer

- **Why use FlowFoundry?** Evaluate bounded routing, review, approval, recovery,
  and provider-independent workflow contracts without paying for every test.
- **Likely confusion:** “Is this another agent framework, or an operator-facing
  product built on its own runtime?”
- **Installation blocker:** The public tag and artifacts referenced by Quick
  Start are not available yet.
- **First value:** Deterministic plan/run/status/review/report lifecycle with
  fake providers.
- **Documentation needed:** A concise “FlowFoundry versus agent frameworks” page,
  one extension boundary, and one complete offline run with expected output.

## 2. Open-source contributor

- **Why use FlowFoundry?** Contribute to a local-first coordination system with
  explicit security and testing expectations.
- **Likely confusion:** Which issue is genuinely small, and which areas require
  architecture or threat review?
- **Installation blocker:** No public immutable contributor baseline and no
  published good-first-issue inventory.
- **First value:** Running the test-backed CLI and tracing one task through its
  persisted evidence.
- **Documentation needed:** The Day 1–Day 7 contributor journey, scoped issues,
  acceptance criteria, and maintainer response expectations.

## 3. University student

- **Why use FlowFoundry?** Learn reproducible AI workflow design, independent
  review, privacy boundaries, and human-in-the-loop operation.
- **Likely confusion:** The Personal AI Manager and learning examples may sound
  like a shipped study assistant or personal-memory system.
- **Installation blocker:** Python virtual environments, Git, and terminal usage
  may be unfamiliar.
- **First value:** A credential-free plan showing why a task receives a builder
  plus reviewer instead of one unreviewed answer.
- **Documentation needed:** A beginner glossary, copy/paste setup explanation,
  and a clearly synthetic learning-oriented tutorial.

## 4. Researcher

- **Why use FlowFoundry?** Inspect deterministic multi-agent state, review,
  conflict, usage, and recovery behavior.
- **Likely confusion:** Which evidence evaluates the coordination runtime and
  which evidence says nothing about model quality?
- **Installation blocker:** Lack of a compact experiment/reproducibility manifest
  and supported-platform matrix.
- **First value:** Re-running fixtures without network calls and comparing
  persisted reports.
- **Documentation needed:** Schema references, experiment provenance, deterministic
  limits, and a citation/reproducibility guide.

## 5. Automation engineer

- **Why use FlowFoundry?** Add explicit permissions, approvals, evidence, and
  recovery around multi-step AI-assisted automation.
- **Likely confusion:** Whether FlowFoundry can already trigger arbitrary tools,
  deployments, or scheduled production workflows.
- **Installation blocker:** No stable public integration contract or end-to-end
  production adapter example.
- **First value:** Approval-gated task execution and durable retry/resume state.
- **Documentation needed:** Side-effect boundaries, idempotency expectations,
  failure-state examples, and the distinction between current CLI and future PWA.

## 6. Small-company developer

- **Why use FlowFoundry?** Coordinate coding and review while retaining local
  project ownership and avoiding one-provider lock-in.
- **Likely confusion:** Whether the Alpha reduces work today or mainly provides
  infrastructure that still needs significant integration.
- **Installation blocker:** Missing public artifacts, support expectations, and
  a clearly bounded production-readiness statement.
- **First value:** Git-isolated writer candidates, reviewable evidence, and
  explicit approval boundaries.
- **Documentation needed:** One realistic “adopt versus wait” checklist, known
  operational limits, and migration/removal guidance.

## 7. AI beginner

- **Why use FlowFoundry?** Avoid choosing among many AI tools and learn a safer,
  goal-first workflow.
- **Likely confusion:** Terms such as provider, capability, DAG, candidate,
  immutable SHA, and synthetic fixture.
- **Installation blocker:** Command-line setup and interpreting JSON output.
- **First value:** Seeing one goal become an understandable plan with a visible
  human decision point.
- **Documentation needed:** A five-minute guided tutorial, annotated terminal
  output, glossary, and “what did not happen” explanation.

## 8. Security-conscious user

- **Why use FlowFoundry?** Keep default execution offline, inspect permissions,
  separate review from approval, and preserve audit evidence.
- **Likely confusion:** Whether provider discovery reads credentials, whether
  fake-provider runs touch project files, and what historical publication risks
  remain.
- **Installation blocker:** Missing current-SHA remote CI, artifact hashes,
  independent security review, and anonymous-clone evidence.
- **First value:** Fail-closed provider preflight, read-only roles, explicit
  approval gates, and Git worktree isolation.
- **Documentation needed:** A one-page threat summary, data-flow diagram,
  credential non-access statement, and signed/hashed artifact evidence.

## 9. Claude/Codex user

- **Why use FlowFoundry?** Coordinate familiar coding/review tools around one
  project goal with shared evidence and permissions.
- **Likely confusion:** Agent names in the offline demo look like real Claude or
  Codex calls even when they are routing identities backed by fake providers.
- **Installation blocker:** Real-provider setup is intentionally separate and
  provider parity is incomplete.
- **First value:** Inspecting why Claude Architect, Codex Builder, and DeepSeek
  Reviewer receive different bounded roles.
- **Documentation needed:** A fake-versus-live matrix, readiness states, explicit
  opt-in steps, costs/unknown-cost semantics, and verified-provider limits.

## 10. Local AI enthusiast

- **Why use FlowFoundry?** Own coordination state locally and eventually route
  eligible work to private local models.
- **Likely confusion:** “Local-first” may be read as “a complete local-model
  runtime is already bundled.”
- **Installation blocker:** General local-model adapters and hardware-aware
  selection are future work.
- **First value:** Fully offline deterministic workflows and local durable run
  state without a provider account.
- **Documentation needed:** A precise local-first definition, current local
  capability matrix, and a future adapter contract clearly labeled unshipped.

## Activation problems ranked by importance

| Rank | Activation problem | Personas affected | Impact | Required response |
|---:|---|---|---|---|
| 1 | Public tag, artifacts, and anonymous install path are unavailable | All | Cannot start from the advertised path | Close exact-SHA release gates before outreach |
| 2 | Synthetic coordination proves mechanics but not real task quality | All | First value may feel abstract | Record the truthful demo and explain what the evidence proves |
| 3 | Product identity overlaps launcher, runtime, framework, and future manager language | 1, 2, 5, 6, 7 | Users may not know what to adopt | Lead with one coordination-layer definition and one current use case |
| 4 | Provider role names can be mistaken for live calls | 1, 8, 9 | Trust and cost misunderstanding | Put `FAKE / OFFLINE` beside every demo role and output |
| 5 | Current CLI evidence is technically useful but not beginner-friendly | 3, 7, 6 | Workflow completes without felt value | Add annotated expected output and a one-screen result summary |
| 6 | Python/Git/terminal prerequisites exclude less technical users | 3, 7 | Installation abandonment | Provide a beginner path and test platform-specific instructions |
| 7 | Missing independent security/artifact evidence | 6, 8 | Security-conscious users will wait | Publish hashes, CI, containment, and clean-install evidence |
| 8 | Documentation volume creates choice overload | All | Correct information is hard to sequence | Keep README short and route by user intent |
| 9 | No published good-first-issue ladder | 2, 1 | Contributor intent does not convert | Seed scoped issues with tests and non-goals |
| 10 | Designed mobile and future memory can overshadow the Alpha | 3, 5, 7, 10 | Expectations exceed current product | Repeat SHIPPED / DESIGNED / FUTURE labels in every public asset |

## First-ten observation plan

Recruit in this order:

1. three developers;
2. one contributor;
3. one security-conscious user;
4. one automation engineer;
5. one researcher;
6. one student;
7. one AI beginner; and
8. one local-AI enthusiast.

Observe without coaching until the participant is blocked. Record only consented,
sanitized timing, error class, comprehension answers, and whether the offline
report was reopened. Do not collect private repositories, prompts, credentials,
home paths, or provider output.

## Validation threshold

The first-ten phase passes when:

- at least 8/10 explain the product and its non-goals correctly;
- at least 8/10 install successfully;
- at least 7/10 finish the offline workflow;
- 10/10 recognize that demo providers are fake/offline;
- no participant believes mobile or personal memory is shipped; and
- every repeated P0/P1 activation failure has an owner before broader launch.
