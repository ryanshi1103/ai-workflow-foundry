# Official FlowFoundry Demos

The release-candidate demos explain coordination through user outcomes. Each
uses synthetic inputs, starts offline, and separates implemented behavior from
future product direction.

## Demo priority

The strongest first public story is:

> “Prepare my GitHub release.”

This is a developer problem with immediate stakes: code, tests, documentation,
security, cost, and publication authority must agree. The 90-second story shows
the user supplying bounded candidate context, FlowFoundry validating and
executing an explicit coordination plan, reporting synthetic orchestration
evidence, and stopping at the approval boundary. It must not imply that the
designed mobile UI is already shipped, that repository tests were run, or that
a push, tag, or release occurred.

The GitHub Release Assistant and Personal AI Manager fixtures are deterministic
Alpha evidence paths. The release-preparation story ties existing routing,
review, persistence, and approval mechanics to a human outcome.

A second vision demo can use a university student asking for a complete
learning and career plan. It should show user-selected schedule, documents,
goals, knowledge gaps, learning preferences, and prior mistakes feeding
research, planning, and review capabilities. That scenario is explicitly
**planned** because the personal-context and preference layers are not
implemented.

### 90-second release story

1. **0–15 seconds — problem:** release work is fragmented across code, review,
   tests, evidence, and publication authority.
2. **15–30 seconds — goal:** the user supplies one bounded release-evidence
   goal and an explicit plan with no push, tag, deploy, or publication.
3. **30–60 seconds — coordination:** Claude Architect, Codex Builder, DeepSeek
   Reviewer, and Local Tester produce durable synthetic orchestration records.
4. **60–90 seconds — evidence and approval:** status, review, usage, and the
   pending synthetic `release` gate are visible; the demo stops before approval
   with the human in control.

| Official demo | Maturity | Reproducible entry point |
|---|---|---|
| [GitHub Release Assistant](github-release-assistant.md) | Alpha synthetic coordination demo | `flowfoundry team plan examples/personal-ai/github-release-assistant.json` |
| [Personal AI Manager](personal-ai-manager-demo.md) | Alpha coordination slice | `flowfoundry team plan examples/personal-ai/personal-ai-manager.json` |
| [AI Project Manager](AI_PROJECT_MANAGER.md) | Alpha synthetic lifecycle | `flowfoundry team run examples/orchestration/codex-builder-deepseek-reviewer.json` |

[Personal Learning Assistant](PERSONAL_LEARNING_ASSISTANT.md) remains a concept
study for the future personal-context phase; it is not one of the first-release
official demos.

## Demo rules

Every public recording or walkthrough must:

1. state the problem and synthetic input;
2. show why the coordinator selected the path;
3. show scoped context, permissions, provider mode, and human decision points;
4. distinguish fake-provider output from real-provider evidence;
5. show a concrete output, validation state, usage receipt, and limitations;
6. run from the exact approved release candidate;
7. include a poster image and accessible transcript.

No official default demo makes a real provider call, uses a customer dataset,
modifies the main Git working tree, merges a candidate, pushes, or deploys.

## Verification state

| Demo | Documentation | Offline command | Recording | Release status |
|---|---|---|---|---|
| GitHub Release Assistant | Ready | Plan/run/review/report/approval lifecycle verified | Pending | WARNING |
| Personal AI Manager | Ready | Plan and fake-provider run verified | 90-second script and normalized evidence ready | PASS |
| AI Project Manager | Ready | Fake-provider run verified previously | Pending | WARNING |

The SVG cards under `docs/assets/demos/` are storyboard placeholders, not
screenshots or proof of completed recordings.
