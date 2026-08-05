# Final Test Matrix

Date: 2026-08-05
Branch: `portfolio-migration`
Validated implementation commit: `d10b94833e2db5503e4eb678d311980286f1e110`

No result below is inferred. Counts are reported by the named command; some
matrices intentionally overlap (for example the root pytest run includes the
workspace Python tests), so they are not added into a misleading grand total.

| Scope | Command or environment | Result |
|---|---|---|
| FlowFoundry full Python | `PYTHONPATH=src python -m pytest -q` | **158 passed, 63 subtests passed** |
| Orchestration focused | `pytest tests/test_orchestration_*.py -q` | **33 passed** |
| Feedback Intelligence | isolated application environment, `pytest tests -q` | **101 passed** |
| Confera Media Skills | unittest discovery | **3 passed** |
| Nameplate workflow | unittest discovery | **3 passed** |
| Workspace launcher Python | `core/workspace-manager/tests/test-cc.sh` | **24 passed** |
| Workspace EOF/remote/permission | `test-cc-eof-fix.sh` | **40 passed, 0 failed** |
| Workspace deploy/profile preservation | `test-deploy-profile-preservation.sh` | **4 assertions passed**, auth sentinel preserved |
| MediaFlow private core branch | isolated Python, no user site | **496 passed** |
| MediaFlow private desktop branch | authorized existing SDK environment | **546 passed** |
| MediaFlow fresh desktop worktree | no copied SDK | **545 passed, 1 expected SDK failure** |
| MediaFlow integrated private branch | temporary read-only authorized SDK reference | **547 passed** |
| Ruff | `ruff check .` | passed |
| Diff hygiene | `git diff --check` | passed |
| Shell syntax | all repository shell entrypoints through `bash -n` | passed |
| FlowFoundry contracts | `flowfoundry validate` | **5 components, 3 workflow contracts, 17 capabilities** |
| Import smoke | core, workspace lifecycle/sessions, MediaFlow adapter, orchestration | passed |
| CLI smoke | root/team help, run/status/review/report/resume | passed |
| Synthetic multi-agent E2E | clean installed wheel, fake provider, outside source cwd | **3/3 tasks completed** |
| Run permissions | synthetic E2E | run directory 0700; manifest and persisted JSON 0600 |
| Feedback DB compatibility | empty, legacy, repeated migration, alternate cwd, in-memory | passed within the 101-test suite |
| Source bundle verification | Feedback and MediaFlow bundles | passed; complete histories recorded in phase reports |

## Clean-environment result

The first normal wheel install built and imported successfully but exposed a
real packaging defect: installed `flowfoundry validate` searched for catalog
data inside `site-packages` and failed. This result was not counted as passing.

Commit `3471894` packages catalog/schema/workflow resources and resolves them
from either a source checkout or the installed distribution. A second fresh
virtual environment then passed:

- wheel build and `pip install --no-deps .`;
- imports from outside the source checkout;
- installed `flowfoundry validate` (5/3/17);
- installed CLI help;
- installed offline synthetic team run and report.

Source-checkout validation still verifies physical bundled component paths.
Installed validation verifies the packaged declarations without pretending that
the monorepo component source trees are installed in the wheel.

## Failure-repair evidence

DeepSeek's scheduler review found two P1 recovery failures. The repair commit
`d10b948` adds tests proving:

- `skipped_pending_human` becomes retryable after a scoped approval;
- approve → retry → resume executes the gated task;
- downstream tasks skipped only because of that dependency revive transitively;
- unchanged completed tasks remain completed.

After the repair, the full 158-test root matrix and 33-test orchestration matrix
passed.
