# GitHub Release Assistant Recording Checklist

Status: **BLOCKED — recording not yet captured**
Canonical behavior: [GitHub Release Assistant](demos/github-release-assistant.md)

No fake screenshot, mock terminal output, composited success state, or invented
UI may be presented as product evidence. Deterministic fake-provider execution
is allowed because it is real runtime behavior, but the mode must be visible.

## Recording identity

```text
Final approved candidate SHA:
Branch/ref:
Package version:
Artifact filename and SHA-256, if installed:
Capture date/time (UTC):
OS / architecture / Python:
Terminal and dimensions:
Execution mode: deterministic fake provider
Operator:
Technical reviewer:
Privacy reviewer:
Accessibility reviewer:
```

Record only from the clean, owner-approved final-candidate commit. Do not copy
the runtime baseline `64f1563...` into this field because documentation
integration produces a later candidate.

## Before recording

- [ ] Release owner approved the exact candidate SHA for recording.
- [ ] `git rev-parse HEAD` matches that SHA.
- [ ] `git branch --show-current` is the expected release candidate.
- [ ] `git status --short` is empty before capture.
- [ ] Installed version/artifact, if used, resolves to the same source.
- [ ] `flowfoundry validate` passes with 4 components, 2 workflow contracts, and
      13 capabilities.
- [ ] The full offline demo lifecycle has been reproduced in a disposable runs
      root.
- [ ] Real-provider execution is disabled.
- [ ] Terminal title, prompt, hostname, username, path, scrollback,
      notifications, clipboard helpers, and background windows are sanitized.
- [ ] No secret, private repository, personal path, user data, or unrelated
      command history is visible.
- [ ] Recording resolution makes commands and output readable at README/video
      embed size.

## Required 90-second story

### 0–10 seconds — problem

- [ ] State that release preparation spans code, review, tests, evidence, and
      publication authority.
- [ ] Show a real release checklist or the goal text, not architecture slides.
- [ ] Do not claim that FlowFoundry has inspected the repository.

### 10–30 seconds — goal and plan

- [ ] Show the exact goal prohibiting push, tag, deploy, publish, and real
      providers.
- [ ] Run the real plan command against the committed fixture.
- [ ] Show five tasks and the approval requirement on `package`.
- [ ] Describe the task graph as user-supplied and validated, not autonomously
      generated from repository analysis.

### 30–60 seconds — coordination

- [ ] Run the fixture with a fresh run ID.
- [ ] Show the real runtime routing identities for Claude Architect, Codex
      Builder, DeepSeek Reviewer, and Local Tester.
- [ ] State on screen and in narration: “deterministic fake providers; no cloud
      provider was called.”
- [ ] Show four prerequisite tasks complete.

### 60–80 seconds — evidence

- [ ] Run real `status`, `review`, and `report` commands.
- [ ] Show persisted task states, review decision, usage fields, risks, and
      generated evidence paths.
- [ ] State that outputs are synthetic coordination evidence, not real test or
      release-package quality.

### 80–90 seconds — human boundary

- [ ] Show `package` as `skipped_pending_human`.
- [ ] Display but do not execute the optional approval command.
- [ ] End with: “FlowFoundry coordinated the work and stopped at the human
      boundary.”
- [ ] Keep the limitation visible: no push, tag, deploy, publication, real
      provider, or real repository test occurred.

## Screenshot and edit integrity

- [ ] Every screenshot comes from the same verified raw runtime capture or a
      separately manifested run at the same SHA.
- [ ] Cropping does not hide execution mode, warnings, blockers, or approval
      state.
- [ ] Cuts may remove idle time but do not reorder tasks or combine states from
      different runs without explicit disclosure.
- [ ] Speed changes are disclosed in the caption.
- [ ] No command output is typed, reconstructed, recolored to change status, or
      placed into a mock UI.
- [ ] Explanatory diagrams are labeled “Diagram” or “Concept”; they are never
      captioned as screenshots.
- [ ] Audio and captions make the same capability claims.

## Required deliverables

- [ ] 90-second 16:9 flagship video.
- [ ] 30-second captioned derivative using only verified flagship frames.
- [ ] Two or three actual README screenshots with alt text.
- [ ] Short terminal GIF with mode and approval boundary visible.
- [ ] Full installation recording from an independent clean environment.
- [ ] Caption file and readable transcript.
- [ ] Poster image from actual runtime output.
- [ ] Command transcript and expected-output appendix.
- [ ] Per-file manifest required by
      [Demo Asset Checklist](DEMO_ASSET_CHECKLIST.md).

## Review

### Technical

- [ ] Commands reproduce on the exact SHA.
- [ ] Agent identities, task counts, states, review, and report match the raw
      run.
- [ ] `package` remains pending human approval.
- [ ] No real-provider or release side effect occurred.

### Privacy and security

- [ ] Frame-by-frame review finds no credential, PII, private path, repository,
      notification, metadata, or unrelated terminal content.
- [ ] File metadata and published download contain no private fields.
- [ ] The raw capture is stored only according to the approved retention policy.

### Accessibility and communication

- [ ] Captions match narration and identify speakers/important non-speech audio.
- [ ] Text remains readable without audio.
- [ ] Alt text describes actual content without marketing claims.
- [ ] Color is not the only way pass/block/pending states are communicated.
- [ ] A new viewer can answer what FlowFoundry is, what the demo proves, and
      which action remains human-controlled.

## Publication gate

Recording status becomes **READY** only when all items pass, the source SHA is
the approved release candidate, asset manifests are complete, and independent
technical/privacy review signs the files. A polished draft with missing
evidence remains **BLOCKED**.
