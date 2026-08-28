# 90-Second Flagship Demo Script

Status: production script; recording not yet captured
Canonical behavior: [GitHub Release Assistant](github-release-assistant.md)
Mode: deterministic fake providers; no network, bill, or release side effect

## 0–12 seconds — the problem

**Visual:** A simple list: code, tests, documentation, security, release
authority.

**Narration:**

> Preparing a release is not one prompt. I have to coordinate tools, preserve
> evidence, and remember which action still needs my approval.

**Caption:** More AI tools create more coordination work.

## 12–25 seconds — one bounded goal

**Visual:** Show the exact fixture goal and its no-push/no-tag/no-publish
constraints, then run the plan command.

```bash
flowfoundry team plan examples/personal-ai/github-release-assistant.json
```

**Narration:**

> FlowFoundry starts with the goal and constraints. This is an explicit,
> versioned five-task plan—not an automatic repository audit.

## 25–55 seconds — coordination

**Visual:** Run the fixture and show task progression.

```bash
flowfoundry team run \
  examples/personal-ai/github-release-assistant.json \
  --run-id github-release-assistant
```

**Narration:**

> Planning routes to Claude Architect, code-oriented work to Codex Builder,
> security review to DeepSeek Reviewer, and the test stage to Local Tester.
> These are offline routing identities. No cloud model is called.

**Caption:** Plan → assign → execute → review

## 55–78 seconds — evidence

**Visual:** Show status, review, and the compact report.

```bash
flowfoundry team status github-release-assistant
flowfoundry team review github-release-assistant
flowfoundry team report github-release-assistant
```

**Narration:**

> Task state, routed roles, review, usage, and required human actions remain
> inspectable. Interrupted or blocked work is a durable state, not a lost chat.

## 78–90 seconds — human control

**Visual:** Hold on `package: skipped_pending_human`. Do not execute the approval
command.

**Narration:**

> FlowFoundry coordinated the work and preserved the evidence. It stopped
> before release authority. The system can prepare and recommend; the human
> still authorizes the consequential action.

**End card:** Local-first AI coordination · No hidden execution · No automatic
publishing

## Recording guardrails

- Capture from an approved exact SHA and record it in the asset manifest.
- Use a clean terminal with synthetic paths and no credentials/history.
- Keep fake-provider mode visible.
- Do not imply real tests, artifact builds, file writes, or live model calls.
- Provide captions, transcript, poster image, and sanitization review.
- Stop before approval, push, tag, deploy, or publication.
