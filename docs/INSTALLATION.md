# Installation Experience

## Supported path

FlowFoundry's root package requires:

- Python 3.11 or newer;
- Git for project/worktree features;
- network access during source installation unless the declared build backend is
  already available or an official wheel is used;
- no root-package runtime dependency beyond the Python standard library.

Optional providers, LibreOffice/PyUNO, and bundled workflow components have
separate dependencies. Feedback Intelligence is excluded from this candidate.
Installing the root wheel does not install component environments.

## First public install

Use this command after the approved Alpha tag is published. Do not substitute a
working branch or an older migration ref.

```bash
git clone --single-branch --branch v0.2.0-alpha.1 \
  https://github.com/ryanshi1103/ai-workflow-foundry.git flowfoundry
cd flowfoundry

python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
flowfoundry validate
```

Expected first-command output:

```text
validated 4 FlowFoundry components
validated 2 workflow contracts
validated 13 registered capabilities
```

Then inspect the catalog or preview a plan:

```bash
flowfoundry list
flowfoundry team plan examples/personal-ai/personal-ai-manager.json
```

Neither command makes a real provider call.

## Audited timing

Local evidence collected on 2026-08-22:

| Step | Environment | Time |
|---|---|---:|
| Create venv | Linux, Python 3.14.6 | 1.53s |
| Build and install source | pip build isolation, network-enabled package index | 8.77s |
| Installed `flowfoundry validate` | Run outside source root | 0.07s |
| Total | Warm development machine | approximately 10.37s |

These values are a diagnostic baseline, not a performance guarantee. Package
index, DNS/TLS, disk, CPU, and Python version can materially change setup time.

## Build dependency behavior

`pyproject.toml` declares `setuptools>=68` as its build backend. A new venv on
the audited Python 3.14 host did not contain setuptools, so this intentionally
offline command failed:

```bash
PIP_NO_INDEX=1 python -m pip install --no-build-isolation --no-deps .
```

Normal `pip install .` succeeded because build isolation downloaded the declared
backend. For an offline installation, distribute and install the release wheel:

```bash
python -m pip install --no-index flowfoundry_ai-0.2.0a1-py3-none-any.whl
flowfoundry validate
```

The published filename and hash must come from the approved release candidate,
whose PEP 440 package version is `0.2.0a1`.

## Wheel evidence

The exact wheel/sdist filenames, hashes, entry scans, and clean-environment
install result are recorded in `FINAL_RELEASE_REPORT.md`.

## Clean-clone status

The local new-root candidate is available for clean-clone verification. Before
publication:

1. clone the exact candidate anonymously into a new directory;
2. verify the checked-out SHA and advertised refs;
3. run the install sequence above on Python 3.11 and one newer supported version;
4. run the offline Personal AI Manager plan and AI Project Manager lifecycle;
5. verify no untracked state remains after cleanup;
6. remove only the disposable test clone after preserving a sanitized report.

## Troubleshooting

### `Cannot import setuptools.build_meta`

Use normal build isolation with package-index access, preinstall a compatible
setuptools wheel, or install the official FlowFoundry wheel. Do not use a random
user-site package to satisfy the build silently.

### Installed command cannot find catalog resources

Confirm `python -m pip show flowfoundry-ai` points into the intended venv and run
`flowfoundry validate` outside the source tree. Report the package version,
Python version, platform, and sanitized output.

### Provider is unavailable

Root installation does not install or authenticate Codex, Claude, or a
DeepSeek-compatible profile. `flowfoundry team providers` reports local setup
state without showing credential values. Offline demos do not require provider
setup.
