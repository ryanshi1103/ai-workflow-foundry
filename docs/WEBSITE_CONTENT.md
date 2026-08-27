# Website Content

Status: draft public copy; no website has been implemented or deployed
Structure source: [Website Structure](WEBSITE_STRUCTURE.md)
Product truth: [Current Status](CURRENT_STATUS.md)

## Hero

**Eyebrow:** Local-first · Human-controlled · Open source

## One goal. The smallest sufficient AI team.

FlowFoundry is a **Local-first Adaptive AI Team Runtime**. Its current Alpha is
an AI coordination layer: define the goal and constraints, choose the minimum
sufficient path, and coordinate eligible models, tools, workflows,
permissions, costs, evidence, approvals, and recovery without making one
provider the product authority.

**Primary action:** Try the offline workflow

**Secondary actions:** Watch the 90-second demo · Explore the architecture ·
Contribute

**Developer Preview note:** The deterministic offline Alpha is runnable. Public
artifacts, external installation evidence, final demo media, and real-provider
parity remain incomplete.

**Visual:** `assets/architecture-overview.svg`

## Problem

### More AI tools create more coordination work.

**AI is moving from individual models to coordinated systems.**

Developers now move between coding assistants, reviewers, terminals, project
files, security tools, and model interfaces. Every transition can lose context,
permission intent, cost evidence, or the reason behind a decision. When work is
interrupted, the user often reconstructs the workflow manually.

The problem is not that each model lacks intelligence. The problem is that the
goal, resources, evidence, and authority are fragmented.

**Visual:** `assets/product-evolution.svg`

**Evidence link:** Current capability matrix and limitations—not market-size or
unsupported productivity claims.

## Solution

### Start with the goal, not the provider.

FlowFoundry profiles a bounded goal, chooses a minimum sufficient path, routes
eligible capabilities, records execution and review state, and stops for a
human decision when policy requires approval.

1. **Plan** the smallest reviewable workflow.
2. **Route** by capability, readiness, permission, workspace, and policy.
3. **Execute** with deterministic offline providers by default.
4. **Review** candidates independently from execution authority.
5. **Approve** one exact consequential action when required.
6. **Recover** durable state after interruption or failure.

**Proof action:** Reproduce the GitHub Release Assistant fixture.

## Architecture

### Models are resources. Coordination is the durable layer.

- **AI Runtime Layer:** Claude, DeepSeek-compatible, Codex, and deterministic
  local identities behind bounded provider contracts.
- **Agent Coordination Layer:** planning, routing, execution, review, approval,
  recovery, and Git isolation.
- **Personal Context Layer:** future user-owned goals, preferences, history, and
  knowledge with provenance—not shipped personal memory.
- **Interface Layer:** CLI and terminal today; an approval-first mobile concept
  is designed for later.

Privacy, permission, cost, evidence, and human authority cross every layer.

**Technical action:** Read the canonical product architecture.

## Demo

### “Prepare my GitHub release.”

A release is not one prompt. It requires planning, code-oriented work, review,
test evidence, and publication authority to agree.

The current synthetic offline demo validates an explicit five-task plan, routes
four roles, preserves review and usage state, and stops the package step at
`skipped_pending_human`.

It does not inspect a repository, run real project tests, build artifacts, call
cloud models, write files, push, tag, deploy, or publish. The demo proves the
coordination lifecycle and human boundary.

**Visual:** `assets/github-release-flow.svg`

**Media slot:** 90-second recording—BLOCKED until captured from an approved
exact SHA with provenance and sanitization review.

## Roadmap

### Build trust before adding reach.

**Current — AI Coordination Layer**

Close artifacts, clean installs, demo media, and external-user evidence for the
planning/routing/review/approval/recovery runtime.

**Designed next — Personal AI Command Center**

An approval-first PWA concept for project status, bounded task creation,
evidence, and exact approvals. No credentials on the phone. No unrestricted
shell. No hidden execution.

**Future — Personal AI OS**

User-owned context with privacy, provenance, correction, export, deletion, and
portable policy. Recommendations remain subordinate to human authority.

**Visual:** `assets/roadmap.svg`

## Community

### Help make AI coordination understandable and trustworthy.

FlowFoundry welcomes developers, students, researchers, and AI builders.
Valuable first contributions include documentation, workflow examples,
provider diagnostics tests, CLI clarity, tutorials, reproducibility, and
security review.

Every starter issue has a bounded problem, skills, acceptance criteria, and a
test command. Documentation and evidence improvements are first-class work.

**Actions:** Read contributing guide · Choose a starter issue · Review the
security policy

## Closing call to action

### Do not chase every new model. Build a system that coordinates them.

Try one deterministic workflow. Inspect the evidence. Stop at the human
boundary. Then tell us what made sense, what failed, and what would make the
coordination layer useful twice.

## Publication checklist

Before using this copy on a public site:

- replace media slots only with real exact-SHA captures;
- verify the artifact install path independently;
- recheck current-status and limitation links;
- add no badge without a live evidence target;
- preserve Alpha, Designed, and Future labels; and
- obtain separate release and announcement authorization.
