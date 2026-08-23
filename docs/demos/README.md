# Official FlowFoundry Demos

The release-candidate demos explain coordination through user outcomes. Each
uses synthetic inputs, starts offline, and separates implemented behavior from
future product direction.

| Official demo | Maturity | Reproducible entry point |
|---|---|---|
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
| Personal AI Manager | Ready | Plan and fake-provider run verified | 90-second script and normalized evidence ready | PASS |
| AI Project Manager | Ready | Fake-provider run verified previously | Pending | WARNING |

The SVG cards under `docs/assets/demos/` are storyboard placeholders, not
screenshots or proof of completed recordings.
