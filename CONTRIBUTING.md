# Contributing

Thank you for helping build FlowFoundry as an open, local-first AI coordination
layer.

The complete contributor guide covers development setup, issue reports,
provider and workflow proposals, architecture discussions, testing, privacy,
and pull request expectations:

**[Read the contributor guide](docs/CONTRIBUTING.md)**

New to the project? Follow the evidence-based
**[Day 1 → Day 7 contributor journey](docs/CONTRIBUTOR_JOURNEY.md)**.

Before opening a pull request, run at minimum:

```bash
PYTHONPATH=src python3 -m flowfoundry validate
PYTHONPATH=src python3 -m unittest discover -s tests -v
git diff --check
```

Never include credentials, private session content, customer data, or real
personal media in issues, tests, examples, or commits.
