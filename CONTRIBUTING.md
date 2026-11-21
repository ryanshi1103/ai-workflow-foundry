# Contributing

Thank you for helping build FlowFoundry as an open, local-first AI coordination layer.

## Start small

Open an issue for a reproducible bug, a confusing setup step, or one concrete
feature. State the platform, expected result, actual result, minimal reproduction,
and a way to verify a fix. Avoid posting logs that contain names, local paths,
tokens, network addresses, or private project text.

For a pull request, explain the user problem, the changed behavior, the test
evidence, and any remaining limitation. Keep unrelated refactors separate.
Issues labeled `good first issue` are intended for first-time contributors.

## Development setup

Use Python 3.11+, Git, and a virtual environment. The core path is local and
does not require a paid model account for unit tests. Real-provider testing
requires the contributor's own account and must be explicitly enabled.

Before opening a pull request, run at minimum:

```bash
PYTHONPATH=src python3 -m flowfoundry validate
PYTHONPATH=src python3 -m unittest discover -s tests -v
git diff --check
```

The desktop scaffold has separate Node, Rust, and native system requirements;
see [its README](applications/flowfoundry-desktop/README.md). Component tests
live under their own directories. State which checks you ran and which you
could not run.

## Architecture and scope

The coordinator owns the goal, route selection, evidence, and approval boundary.
Providers own model execution. A proposed new provider needs a clear capability
contract, an eligibility check, a failure mode, and a test with fake credentials.
Avoid adding a worker or meeting to a path that can be handled by one worker.

The current development branch and release snapshot may differ. Base changes on
the public default branch unless a maintainer directs otherwise. Never merge a
historical or private branch into a public branch without a privacy review.

Never include credentials, private session content, customer data, or real
personal media in issues, tests, examples, or commits.
