# Final Push Plan

Status: **PLAN ONLY — DO NOT EXECUTE WHILE FLOWFOUNDRY IS BLOCKED**

No command in this document was run. None uses force, history rewrite, remote
branch deletion, protected-branch bypass, release, deployment, or GitHub UI/API
mutation.

## 0. Mandatory gates before any public push

1. Decide and apply the Feedback license/boundary described in
   `FEEDBACK_LICENSE_DECISION.md`.
2. Explicitly authorize a sanitized FlowFoundry publication branch that excludes
   commit `e3f42ecc` and all `docs/sessions/...` objects while preserving the
   original `portfolio-migration` branch and verified external bundle.
3. Reconstruct and verify the approved commit/merge topology under that
   authority. Do not use the current branch as the push source.
4. Run the complete test/privacy/secret/tree/lineage matrix and obtain a new
   `APPROVED` or `APPROVED_WITH_NOTES` review for the sanitized tip.
5. Read-only fetch every target remote immediately before comparing bases.

There is intentionally no runnable FlowFoundry push command for current HEAD
`180c65b` (or the later closure-report commit). The command becomes precise only
after a sanitized branch name and approved SHA exist:

```bash
git -C ~/Projects/ai-workflow-foundry fetch origin
git -C ~/Projects/ai-workflow-foundry rev-list --left-right --count origin/main...<APPROVED_SANITIZED_SHA>
git -C ~/Projects/ai-workflow-foundry push --set-upstream origin <APPROVED_SANITIZED_BRANCH>
```

Do not substitute `portfolio-migration` in that command.

## 1. Feedback standalone — after license application

Current branch/remote/tip:

- `migration/feedback-intelligence`
- `origin` (`ryanshi1103/feedback-analysis-system`)
- `93b646baf6c92437b97abc0e13d6b6e53b8811eb` before the required license commit

After the owner-approved license commit exists and tests pass:

```bash
git -C ~/Projects/feedback-intelligence-system-migration fetch origin
git -C ~/Projects/feedback-intelligence-system-migration rev-list --left-right --count origin/main...migration/feedback-intelligence
git -C ~/Projects/feedback-intelligence-system-migration push --set-upstream origin migration/feedback-intelligence
```

Wait for `tests.yml`, review the PR, and merge with a normal merge commit. Do not
squash the source-lineage commits. The in-place repository rename happens only
after the protected merge and green remote CI.

## 2. Private MediaFlow branches

First confirm both GitHub repositories are still private and fetch their cached
bases. Do not push `meeting-media-auto/master` at `a02d112c`; it contains the
excluded session-only commit.

Core review branch:

```bash
git -C ~/Projects/meeting-media-auto-migration fetch origin
git -C ~/Projects/meeting-media-auto-migration rev-list --left-right --count origin/master...migration/mediaflow-core
git -C ~/Projects/meeting-media-auto-migration push --set-upstream origin migration/mediaflow-core
```

Desktop/release-mirror review branch:

```bash
git -C ~/Projects/meeting-media-desktop-migration fetch origin
git -C ~/Projects/meeting-media-desktop-migration rev-list --left-right --count origin/product/windows-desktop...migration/mediaflow-platforms
git -C ~/Projects/meeting-media-desktop-migration push --set-upstream origin migration/mediaflow-platforms
```

Canonical private integration branch:

```bash
git -C ~/Projects/mediaflow-integration fetch origin
git -C ~/Projects/mediaflow-integration rev-list --left-right --count origin/master...migration/mediaflow-integration
git -C ~/Projects/mediaflow-integration push --set-upstream origin migration/mediaflow-integration
```

Wait for each private repository's tests/import/packaging jobs. Use merge commits
for the integration PR; do not squash the three existing two-parent lineage
merges. Windows hash lock, Android/Windows signing, real-device/media tests,
release artifacts and deployment remain later manual gates.

## 3. Sanitized FlowFoundry branch

After the mandatory gates in section 0, push only the newly approved sanitized
branch, wait for root `tests.yml`, clean-wheel/installed CLI tests and privacy
checks, then merge through the protected PR workflow with a merge commit. The
Feedback and Workspace lineage commits must not be squashed.

## 4. Feedback rename and redirect verification

Only after the standalone protected merge and CI:

1. Rename the existing `feedback-analysis-system` repository in place to the
   owner-approved canonical name; do not create a duplicate remote.
2. Verify clone, browser and API access through both old and new URLs.
3. Update FlowFoundry/profile links in normal follow-up PRs only after redirect
   behavior is confirmed.

## 5. Profile branch

Current branch/remote/tip:

- `portfolio/profile-layer`
- `origin` (`ryanshi1103/ryanshi1103`)
- `d50d98d92ef3a238fd91b32115b81dfb00fd8477`

Push only after FlowFoundry is merged and Feedback URLs are stable:

```bash
git -C ~/Projects/ryanshi1103-portfolio-migration fetch origin
git -C ~/Projects/ryanshi1103-portfolio-migration rev-list --left-right --count origin/main...portfolio/profile-layer
git -C ~/Projects/ryanshi1103-portfolio-migration push --set-upstream origin portfolio/profile-layer
```

Wait for any profile repository checks, review rendered Markdown and links, then
merge through the repository's normal protected workflow.

## 6. Pins, topics, release, signing and deployment

After every protected merge and green remote CI:

1. Set repository descriptions/topics.
2. Pin the approved repositories in the order recommended by the portfolio plan.
3. Perform private Windows/Android signing and real-media acceptance tests.
4. Create releases only from reviewed release commits with provenance/SBOM.
5. Deploy last, from the approved operator environment with production
   credentials.
