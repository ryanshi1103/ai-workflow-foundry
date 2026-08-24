# Five Good First Issues for the Alpha

Status: **proposed and scoped; not yet published or assigned**

Apply the GitHub `good first issue` label only after a maintainer reproduces the
need on the final Alpha candidate, confirms the named test command, and commits
to reviewing the contribution.

These issues improve the existing product. They do not add providers, agent
architecture, mobile implementation, personal memory, autonomous publication,
or broader side-effect authority.

## 1. Add annotated expected output to the first Alpha workflow

**Category:** Documentation
**Difficulty:** Beginner
**Skills:** Markdown, command-line basics, careful evidence capture
**Suggested labels:** `type:documentation`, `area:docs`,
`difficulty:first-issue`, `status:ready`

**Problem:** A new user can run the first workflow but does not yet see a short,
annotated real-output example beside the instructions.

**Why it matters:** The approval stop is the first “aha” moment. Showing it
accurately reduces confusion without requiring a live provider or fake screen.

### Description

Add a short sanitized output excerpt to the README and Alpha User Guide showing
the four completed tasks, `skipped_pending_human`, fake-provider mode, and the
human-action field. Explain what the synthetic output proves and does not prove.

### Non-goals

- Do not record a real provider.
- Do not approve the package task.
- Do not present a mock terminal or invented screenshot as output.

### Acceptance criteria

- Output is captured from the exact approved candidate and committed fixture.
- Candidate SHA and fake-provider mode are recorded in the asset/evidence note.
- No private path, username, repository, credential, or unrelated terminal
  history appears.
- README remains scannable and links to full output rather than embedding a
  long transcript.
- Implemented, experimental, and future boundaries remain unchanged.

### Test command

```bash
git diff --check
PYTHONPATH=src python3 -m flowfoundry validate
```

## 2. Verify one Python 3.11 clean artifact install

**Category:** Installation / documentation
**Difficulty:** Beginner to intermediate
**Skills:** Python virtual environments, pip, Markdown, reproducible reporting
**Suggested labels:** `type:documentation`, `area:install`,
`difficulty:first-issue`, `status:ready`

**Problem:** The project lacks independent Python 3.11 evidence that a final
wheel installs and reaches the first workflow outside the source checkout.

**Why it matters:** A source-tree test cannot prove the experience a new user
gets from the release artifact.

### Description

Follow only the published installation guide in a disposable Python 3.11
environment using the final Alpha wheel. Record sanitized timing, artifact hash,
validation result, first failed step if any, and documentation corrections.

### Non-goals

- Do not build from a mutable working branch.
- Do not install or configure a live provider.
- Do not publish a private path or full environment dump.

### Acceptance criteria

- The exact artifact filename, SHA-256, Python, OS, and architecture are recorded.
- Installation occurs outside the source tree with no preinstalled FlowFoundry
  package on the path.
- `pip check` and installed `flowfoundry validate` pass, or the failure is
  reproducible and classified.
- The GitHub Release Assistant reaches the expected human approval stop.
- Temporary environment and test state are safely removed after sanitized
  evidence is preserved.

### Test command

```bash
python3 -m unittest tests.test_packaged_resources -v
```

## 3. Add a regression test for the GitHub Release Assistant approval stop

**Category:** Testing
**Difficulty:** Intermediate
**Skills:** Python `unittest`, temporary directories, JSON assertions
**Suggested labels:** `type:test`, `area:workflow`,
`difficulty:first-issue`, `status:ready`

**Problem:** The flagship fixture's routed roles and human approval stop need a
single focused regression test that communicates the product contract.

**Why it matters:** The public demo should fail loudly if a future change hides
the approval boundary or turns synthetic execution into a broader claim.

### Description

Add focused coverage for the committed five-task fixture, routed identities,
persisted review decision, four completed tasks, and the final
`skipped_pending_human` package state.

### Non-goals

- Do not enable a real provider or network call.
- Do not test actual GitHub publication.
- Do not broaden approval semantics.

### Acceptance criteria

- The test uses a temporary runs root and cleans it automatically.
- It asserts Claude Architect, Codex Builder, DeepSeek Reviewer, and Local Tester
  routing identities.
- It asserts that provider outputs are synthetic and no tracked file changes.
- It fails if the release approval gate disappears or is silently granted.
- Existing CLI output contracts remain compatible.

### Test command

```bash
python3 -m unittest tests.test_orchestration_cli -v
```

## 4. Improve the repeated run-ID error and recovery hint

**Category:** CLI user experience
**Difficulty:** Beginner to intermediate
**Skills:** Python, CLI error messages, focused regression tests
**Suggested labels:** `type:bug`, `area:cli`, `difficulty:first-issue`,
`status:ready`

**Problem:** Reusing a Quick Start run ID can produce a confusing first-user
failure without an obvious safe recovery path.

**Why it matters:** Durable evidence should be preserved, while the user gets a
clear next action instead of being tempted to delete state.

### Description

When a Quick Start run ID already exists, return a concise message explaining
how to inspect the existing run or choose another ID. Do not recommend deleting
durable evidence.

### Non-goals

- Do not change run-state format.
- Do not automatically overwrite, retry, or remove an existing run.
- Do not add interactive prompts.

### Acceptance criteria

- The error contains no traceback for normal repeated-ID use.
- Existing state is byte-for-byte preserved.
- The message includes safe `status`/`report` guidance and a new-ID example.
- Missing-run behavior and machine-readable outputs remain compatible.
- CLI regression tests cover the message and preservation behavior.

### Test command

```bash
python3 -m unittest tests.test_orchestration_cli -v
```

## 5. Add an unavailable-provider diagnostic fixture

**Category:** Provider diagnostics / testing
**Difficulty:** Intermediate
**Skills:** Python fixtures, provider-readiness concepts, privacy-safe testing
**Suggested labels:** `type:test`, `area:provider-adapter`,
`difficulty:first-issue`, `status:ready`

**Problem:** A missing provider executable or profile needs a deterministic
diagnostic example that proves no credential is read and no retry is consumed.

**Why it matters:** Trust starts before execution. Clear unavailable states help
users distinguish environment setup from workspace or workflow failures.

### Description

Cover one missing executable or profile case and verify that setup diagnostics
record an actionable unavailable state without reading credentials, invoking a
provider, or consuming a workflow retry.

### Non-goals

- Do not add a provider adapter.
- Do not inspect or print credential values.
- Do not change the offline fake-provider default.

### Acceptance criteria

- Provider call count remains zero.
- The diagnostic distinguishes missing runtime/profile from workspace
  incompatibility.
- The user-facing reason is concise and contains a safe next step.
- Structured readiness fields remain backward compatible.
- Registry and workspace-preflight tests cover the fixture.

### Test command

```bash
python3 -m unittest \
  tests.test_orchestration_registry \
  tests.test_orchestration_workspace_preflight -v
```

## Maintainer publication gate

Before publishing any of the five issues:

- reproduce it on the final candidate SHA;
- name the expected files or subsystem;
- copy the non-goals and acceptance criteria into the issue;
- assign a maintainer and expected first-response target;
- verify the test command in the supported environment;
- mark security-sensitive details for private reporting; and
- remove `good first issue` if hidden architecture knowledge is required.
