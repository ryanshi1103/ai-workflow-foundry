# Contributing

Thank you for helping build FlowFoundry as an open, local-first AI coordination
layer.

FlowFoundry is early enough that a clear example, a reproducible install report,
or a focused test can materially improve the product. You do not need provider
credentials or agent-framework experience to make a useful first contribution.

## Choose a contribution path

| If you enjoy… | A useful first contribution |
|---|---|
| Explaining technical ideas | Tighten a tutorial, example, expected output, or limitation |
| Testing systems | Add a deterministic fixture or reproduce a clean installation |
| Developer experience | Improve one CLI message without changing durable state |
| Provider integrations | Strengthen readiness/diagnostic tests without adding a provider |
| Research and evaluation | Improve provenance, evidence, or human-control criteria |

Review the [five scoped starter issues](docs/GOOD_FIRST_ISSUES.md). Each has a
problem, importance, difficulty, skills, acceptance criteria, and test command.

The complete contributor guide covers development setup, issue reports,
provider and workflow proposals, architecture discussions, testing, privacy,
and pull request expectations:

**[Read the contributor guide](docs/CONTRIBUTING.md)**

New to the project? Follow the evidence-based
**[Day 1 → Day 7 contributor journey](docs/CONTRIBUTOR_JOURNEY.md)**.

For a first pull request, keep the change small, explain why it matters, record
the risk, and show the relevant test evidence. Maintainers value honest
boundaries and reviewable progress more than feature count.

Before opening a pull request, run at minimum:

```bash
PYTHONPATH=src python3 -m flowfoundry validate
PYTHONPATH=src python3 -m unittest discover -s tests -v
git diff --check
```

Never include credentials, private session content, customer data, or real
personal media in issues, tests, examples, or commits.
