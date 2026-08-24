# Contributing to FlowFoundry

FlowFoundry welcomes contributors interested in AI coordination, provider
adapters, local-first infrastructure, workflow contracts, safety, testing,
documentation, and human-centered developer experience.

This project is Alpha. Small, well-evidenced changes are more valuable than
large capability claims.

For a paced first contribution, use the
[Day 1 → Day 7 contributor journey](CONTRIBUTOR_JOURNEY.md).

## Before you start

Read:

1. [Current Status](CURRENT_STATUS.md) for implemented and planned boundaries.
2. [Architecture](ARCHITECTURE.md) for runtime responsibilities.
3. [Security model](../MULTI_AGENT_SECURITY_MODEL.md) for trust boundaries.
4. [Product Roadmap](PRODUCT_ROADMAP.md) for current priorities.

Do not include credentials, private transcripts, customer data, real media,
personal datasets, or generated artifacts containing sensitive information in
an issue or pull request.

## Development setup

Requirements:

- Python 3.11 or newer;
- Git;
- Bash for workspace launcher regression scripts;
- optional LibreOffice/PyUNO only for real nameplate generation.

```bash
git clone --branch v0.2.0-alpha.1 --single-branch \
  https://github.com/ryanshi1103/ai-workflow-foundry.git ai-workflow-foundry
cd ai-workflow-foundry
git switch -c contribution/<topic>

python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e .

PYTHONPATH=src python3 -m flowfoundry validate
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Additional suites are listed in the root [README](../README.md#contributing).

## Choose the right change path

### Bug fix

Open an issue with the smallest reproduction, expected behavior, actual
behavior, platform/runtime versions, and sanitized logs. If the issue involves
a provider, state whether fake/offline execution reproduces it.

### New provider adapter

Start with an architecture discussion. Describe:

- the capability and why an existing adapter is insufficient;
- executable/API discovery and authentication-state behavior;
- context and secret boundaries;
- tool/permission translation;
- structured output and usage reporting;
- cancellation and recovery behavior;
- offline fixtures and the bounded live-smoke plan.

Provider support is not accepted based only on one successful call.

### New workflow or component

Include a component manifest, capability declarations, workflow contract when
applicable, local synthetic examples, validation tests, license information,
data/privacy boundaries, failure behavior, and an honest maturity label.

### Feature proposal

Open a discussion before implementation when the proposal changes architecture,
permissions, provider behavior, persisted formats, personal context, or public
APIs. A useful proposal contains:

- problem and user outcome;
- non-goals;
- current evidence;
- proposed lifecycle and trust boundary;
- alternatives and tradeoffs;
- migration and rollback plan;
- acceptance tests and documentation impact.

## Pull request expectations

- Keep the scope reviewable and avoid unrelated cleanup.
- Preserve existing user data and backward compatibility unless an approved
  migration says otherwise.
- Add offline tests for success, failure, cancellation, and recovery paths.
- Do not make real provider calls in the default test suite.
- Update `CURRENT_STATUS.md` only when evidence changes maturity.
- Keep implemented, experimental, and planned claims distinct.
- Run relevant tests and `git diff --check`.
- Explain permissions, network use, secrets, cost, and destructive-action impact.

## Commit and review guidance

Use clear imperative commit messages such as `feat: add provider reason receipt`
or `fix: retain failed candidate evidence`. A pull request should explain the
user problem, architecture impact, validation performed, known limitations, and
follow-up work.

Maintainers may request an architecture decision record for changes to persisted
state, trust boundaries, provider interfaces, or plugin contracts.

## Issue labels to establish

The public repository should provide at least:

- `good first issue`
- `help wanted`
- `area: orchestration`
- `area: providers`
- `area: workspace`
- `area: docs`
- `area: workflows`
- `security`
- `privacy`
- `design proposal`
- `blocked: evidence`

## Security and privacy reports

Do not file public issues containing secrets, private content, or exploitable
details. Follow [SECURITY.md](../SECURITY.md). The current repository still has
a documented publication-history incident; contributors must work only from an
owner-approved sanitized publication candidate when one becomes available.

## Community standard

Be precise, constructive, and respectful. Critique claims and engineering
decisions with evidence. Do not market experimental work as production-ready or
use FlowFoundry to imply autonomous human replacement.
