# GitHub Portfolio Preparation Report

Date: 2026-08-05  
Status: locally prepared; no GitHub mutation performed

## Positioning

The portfolio now uses one consistent statement:

> Ryan Shi — AI Agent Engineer / AI Application Engineer. Building local-first
> AI systems, reliable workflows, and practical automation products.

The narrative presents FlowFoundry as the engineering foundation, Feedback
Intelligence as a public data-centered AI application, Confera Media Skills as a
reusable public capability layer, and Huiying / MediaFlow as a private applied
product represented only by a sanitized public contract.

## Personal profile repository

The correct personal profile repository exists locally as `ryanshi1103` and was
clean at `f6d2524e644e150af6aa494d210fd96343779725`. The original `main` checkout
was not modified. A separate local worktree and branch were created:

- branch: `portfolio/profile-layer`;
- commit: `d50d98d92ef3a238fd91b32115b81dfb00fd8477`;
- commit subject: `docs(profile): align AI agent portfolio narrative`.

The root `README.md` now contains the short positioning, technical direction,
featured projects, a version-controlled Mermaid relationship diagram, current
building direction, and engineering principles. Stale hard-coded test totals
were removed. No `.github/profile/README.md` was created because that is not the
personal-profile path.

## Core repository presentation

FlowFoundry's root README now includes:

- product purpose and local-first rationale;
- an architecture overview and component relationship table;
- current features and command-line installation/demo instructions;
- test commands and explicit component boundaries;
- a privacy-aware MediaFlow entry that does not expose private product code;
- links to architecture, product-line, audit, and roadmap documents.

Feedback Intelligence and MediaFlow each have application-level READMEs with
architecture, features or contract scope, installation/verification guidance,
privacy boundaries, migration compatibility, and future work. Confera retains
its independently documented capability-pack boundary.

## Demo and media policy

No screenshot, user count, performance result, deployment status, commercial
adoption claim, or work-history claim was fabricated. The profile explicitly
states that screenshots will be added only when reproducible from public or
synthetic data. Current demos use documented local commands and synthetic
fixtures.

## Validation

- profile README: privacy scan and `git diff --check` passed;
- FlowFoundry README links target repository-controlled documentation;
- FlowFoundry full test/Ruff/validation matrix passed at the Phase 3 checkpoint;
- original profile `main` remained unchanged;
- no push, pin, topic, rename, archive, release, or deployment action occurred.

## Remaining human work

After reviewing all local commits, the operator must decide and perform the
ordered GitHub actions in `HUMAN_ACTIONS_REQUIRED.md`. Repository rename/archive
and pin recommendations are documented separately and are not execution logs.

