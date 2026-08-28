# Alpha Troubleshooting

Use this guide for the exact approved Alpha artifact or candidate. If identity
is unknown, stop and ask the release owner before changing the environment.

## Safe diagnostic record

Collect only:

```text
FlowFoundry version:
Candidate SHA or artifact SHA-256:
Operating system and architecture:
Python version:
Git version:
Virtual-environment path category (not a private absolute path):
Command that failed:
Exit code:
Sanitized error excerpt:
Expected result:
```

Never post API keys, auth files, private prompts, repository contents, complete
environment dumps, or full terminal history.

## `Cannot import setuptools.build_meta`

The source build requires the backend declared in `pyproject.toml`. Use normal
build isolation with package-index access, preinstall an approved compatible
setuptools artifact, or install the official FlowFoundry wheel. Do not silently
use an unrelated user-site package.

For the public Alpha, prefer the reviewed wheel once it exists. If no final
wheel and hash have been published, the public install gate is still blocked.

## `flowfoundry: command not found`

Confirm that the intended virtual environment is active:

```bash
python -m pip show flowfoundry-ai
python -c "import sys; print(sys.executable)"
```

Do not use `sudo pip`. Recreate a disposable virtual environment if the package
was installed into a different interpreter.

## Catalog or resource validation fails

Run:

```bash
flowfoundry validate
python -m pip show -f flowfoundry-ai
```

Record which of the component, workflow-contract, or capability counts differs.
If the install came from a wheel, verify its SHA-256 against the release record.
Do not copy missing files manually from a source checkout; that would invalidate
the artifact test.

## Provider is unavailable

Run:

```bash
flowfoundry team providers
```

Root installation does not install or authenticate Claude, Codex, or a
DeepSeek-compatible runtime. The first Alpha workflow uses fake providers and
should not require provider setup.

Do not expose credential values while reporting readiness. Provider names in an
offline run are routing identities, not proof of a live provider call.

## Run ID already exists

Run state is intentionally durable. Inspect the existing run:

```bash
flowfoundry team status first-alpha-workflow
flowfoundry team report first-alpha-workflow
```

Or choose a new ID. Do not delete run state unless the documented cleanup policy
explicitly permits it and the data is no longer needed.

## `completed_with_blockers` in the first workflow

For the GitHub Release Assistant this is expected. Four tasks should complete,
while `package` becomes `skipped_pending_human` because release approval was not
granted. The report should say that human action is required.

Do not approve the task merely to make the status look green. The approval stop
is the intended product behavior.

## The plan or routed identities differ from the guide

Verify:

- the exact candidate SHA;
- the committed `github-release-assistant.json` fixture;
- that `--enable-real-provider` was not supplied;
- that the command ran from the expected installation.

Stop validation if the fixture or candidate differs. A changed output needs a
new review; it must not be normalized away in a recording.

## Offline installation fails

Source installation may need the declared build backend. A true offline path
requires the reviewed wheel and its dependencies. Do not claim offline install
support based only on offline runtime behavior.

Report whether the failure occurred while obtaining build dependencies,
installing the wheel, validating resources, or running the workflow.

## Real-provider mode was enabled accidentally

Stop the run. Do not publish its logs. Check whether any request was attempted,
record the incident through the appropriate private channel, and restart the
validation in a fresh contained runs directory without
`--enable-real-provider`.

Do not read or share credential files as part of diagnosis.

## Suspected security or privacy issue

Do not open a public issue with sensitive details. Follow
[SECURITY.md](../SECURITY.md). Preserve only the minimum evidence needed, avoid
copying secrets, and wait for private maintainer instructions.

## When to stop testing

Stop immediately for:

- unexpected file writes outside the declared run state;
- delete, push, merge, tag, deploy, publish, or financial action;
- credential/private-data exposure;
- artifact hash or candidate SHA mismatch;
- data loss or a high-severity security concern.

Classify other failures as code, environment, permission, infrastructure,
documentation, or product fit. A failed Alpha validation is evidence; do not
hide it by changing the user's environment without recording the intervention.
