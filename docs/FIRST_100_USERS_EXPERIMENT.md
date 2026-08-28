# First 100 Users Experiment

Status: **external-validation protocol**. “100 users” means 100 consented people
who attempt the activation path; it does not mean stars, visitors, impressions,
or simulated personas.

## Research question

Can a new user understand FlowFoundry, install it without maintainer
intervention, complete a useful workflow, understand the human-control
boundary, and find enough value to return?

The experiment tests the current AI Coordination Layer. It does not test the
designed Mobile Command Center, personal memory, a Personal AI OS, or autonomous
execution.

## Cohorts

Recruit deliberately rather than sampling only the maintainer's network.

| Group | Target | Primary reason to participate | First workflow |
|---|---:|---|---|
| AI developers | 55 | Coordinate development tools and model-assisted work | Release preparation or repository audit |
| Automation users | 20 | Add evidence and approvals to repeatable workflows | Bounded project workflow |
| Students | 15 | Organize tool-assisted project or learning work | Offline planning/review example supported by current behavior |
| Researchers | 10 | Preserve plans, execution evidence, and review state | Reproducible project audit |

This allocation reflects a developer-first Alpha while still testing whether
the product language transfers to adjacent audiences.

## Definitions and measures

### Understanding

After no more than 30 seconds on the README, ask the participant to explain:

- what FlowFoundry is;
- what it coordinates;
- how it differs from choosing one assistant;
- which parts are current versus future.

**Pass:** The answer identifies a local-first coordination layer and does not
describe it as an AI model, chatbot, AGI, autonomous replacement, existing
mobile app, or existing personal-memory system.

### Installation

Start from a supported clean environment and the published Alpha artifact.
Record start/end time, interventions, platform, Python, artifact hash, and the
first failed step.

**Pass:** Installation, `flowfoundry validate`, and required setup complete in
10 minutes without a maintainer changing the participant's environment.

### Activation

The participant runs the deterministic offline first workflow and locates its
plan, agent assignment, evidence, result, and approval boundary.

**Pass:** A successful workflow is completed in 15 minutes from the beginning
of installation, and the participant can identify which actions would require
human approval.

### Value

Ask the participant to apply FlowFoundry to one suitable real project goal or
explain why the current product cannot help.

**Pass:** The person finishes a supported workflow and rates the evidence or
coordination result as useful enough to try on another goal. An honest “not a
fit” remains valuable research data but is not an activation success.

### Retention

At day 14, ask whether the participant ran a second workflow without a scheduled
research session.

**Pass:** A second completed workflow is evidenced by the participant. Do not
count opening the repository, a star, or a survey response as retention.

## Alpha success criteria

The 100-user experiment passes only if all mandatory safety gates pass and the
following thresholds are met:

| Metric | Required result |
|---|---:|
| Correct 30-second understanding | at least 80 of 100 |
| Clean install within 10 minutes | at least 80 of 100 overall and no supported cohort below 65% |
| First workflow within 15 minutes | at least 70 of 100 |
| Human-approval boundary understood | at least 90 of activated users |
| Useful first outcome | at least 60 of 100 |
| Second workflow within 14 days | at least 25 of 100 |
| Actionable security/privacy incidents | 0 unresolved high-severity incidents before expansion |

These are decision thresholds, not marketing claims. Publish the denominator,
environment mix, and failures with any result.

## Experiment sequence

### Wave 0 — Instrument the human process

Prepare the consent statement, intake form, install observation sheet,
post-workflow interview, day-14 follow-up, and anonymized findings template.
Test them with maintainers without counting those runs.

### Wave 1 — Users 1–10: observed validation

Watch sessions with minimal intervention. Fix documentation blockers only after
the session and rerun with a new participant. Stop for security, data-loss, or
credential-handling problems.

**Expansion gate:** At least 8/10 understand, 7/10 install, 6/10 activate, and no
unresolved serious trust issue.

### Wave 2 — Users 11–30: clean-install diversity

Prioritize different supported operating systems, Python versions, shell
experience, and network constraints. Separate artifact failures from unclear
instructions.

**Expansion gate:** Aggregate install success is at least 75%, and the top three
installation failures have documented owners and reproduction steps.

### Wave 3 — Users 31–60: workflow value

Reduce observation and ask participants to choose a supported real project
goal. Measure how often they can map the demo to their own work without product
claims being explained by a maintainer.

**Expansion gate:** At least 60% of this wave completes a useful workflow; no
cohort consistently mistakes future capabilities for current ones.

### Wave 4 — Users 61–100: repeatability and contribution

Use public docs and normal issue channels. Track day-14 return, actionable bug
reports, documentation improvements, and the contributor journey.

**Completion gate:** Apply the overall thresholds, publish a limitations-first
summary, and decide whether to broaden, hold, or narrow the Beta.

## Data collection without hidden telemetry

Collect only what is needed, with explicit consent:

- anonymous participant ID and cohort;
- supported environment details;
- timestamps for understand/install/activate milestones;
- intervention count and category;
- sanitized failure step and log excerpt;
- workflow category and completion status;
- approval-boundary comprehension;
- optional usefulness rating and interview notes;
- day-14 second-workflow result;
- permission to quote, separate from participation consent.

Do not collect API keys, project contents, prompts containing private data,
repository names, or full terminal histories. Participants may withdraw their
research record. Aggregate results should use minimum cohort sizes that avoid
identification.

## Failure classification

Every unsuccessful attempt gets one primary class:

- `message` — wrong product expectation or current/future confusion;
- `install` — packaging, dependency, platform, or instruction failure;
- `workflow` — user cannot reach or interpret a result;
- `trust` — permission, privacy, credential, or hidden-action concern;
- `value` — workflow works but does not solve a meaningful problem;
- `support` — resolution depends on unavailable maintainer help.

Rank problems by affected participants, severity, and whether they block the
first workflow. Do not change runtime scope merely to improve a metric; first
decide whether the target user or task fits the Alpha boundary.

## Stop conditions

Pause recruitment immediately for suspected credential exposure, unintended
write/delete/push/deploy behavior, data loss, a high-severity vulnerability,
artifact identity mismatch, or materially misleading public instructions.
Record the incident privately and follow the security/release process before
resuming.

## Outputs

At users 10, 30, 60, and 100, publish an anonymized report containing funnel
counts, timing distributions, environment coverage, top blockers, fixes made,
unresolved limitations, and the next decision. Preserve this document's
thresholds; do not rewrite them after seeing the outcome.
