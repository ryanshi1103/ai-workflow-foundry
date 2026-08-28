# First External Alpha User Guide

Status: **prepared for an invitation-only validation cohort; public artifact
pending**

## What you should achieve

This path is designed for a developer who has not used FlowFoundry before:

- **10 seconds:** understand that FlowFoundry coordinates AI resources around a
  goal; it is not another model or chatbot;
- **10 minutes:** install and validate the exact Alpha candidate;
- **30 minutes:** complete the deterministic GitHub Release Assistant workflow,
  inspect its evidence, and see it stop at the human approval boundary.

The first workflow requires no API key, provider account, model bill, network
provider call, repository modification, push, tag, deployment, or publication.

## Before you begin

Requirements:

- a supported system with Python 3.11 or newer;
- Git;
- a terminal and permission to create a virtual environment;
- approximately 15 minutes for installation and 15 minutes for the first run;
- the exact candidate SHA or immutable public tag supplied by the release owner.

Do not paste API keys, private repository contents, or personal data into an
issue or validation form.

## Obtain the correct source

### After the public Alpha exists

Use only the immutable `v0.2.0-alpha.1` tag and verify its commit against the
published release record.

### Invitation-only validation before publication

The release owner must provide:

- an exact candidate SHA;
- an approved source location or archive;
- an expected SHA-256 for any archive;
- the supported environment matrix;
- a private contact for security concerns.

Verify the supplied identity before installation. Do not substitute the mutable
head of a branch or the historical `64f1563...` runtime baseline if the owner
has approved a later documentation-integrated candidate.

## 0–10 minutes: install and validate

Follow [Installation](INSTALLATION.md). The success checkpoint is:

```text
validated 4 FlowFoundry components
validated 2 workflow contracts
validated 13 registered capabilities
```

If this output does not appear, stop the timed path and use
[Troubleshooting](TROUBLESHOOTING.md). Record the failed command, Python
version, platform, exact candidate/artifact identity, and sanitized output.

## 10–20 minutes: preview and run one goal

From the FlowFoundry checkout used for the Alpha validation:

```bash
flowfoundry team plan \
  examples/personal-ai/github-release-assistant.json

flowfoundry team run \
  examples/personal-ai/github-release-assistant.json \
  --run-id first-alpha-workflow
```

Expected behavior:

- the goal explicitly forbids push, tag, deploy, publish, and real providers;
- four prerequisite tasks complete using deterministic fake-provider routing;
- `package` stops at `skipped_pending_human`;
- the overall status is `completed_with_blockers` because human approval is
  intentionally absent.

This is success, not a failure. The Alpha is demonstrating coordination and an
approval boundary, not producing a real GitHub Release.

## 20–30 minutes: inspect evidence

```bash
flowfoundry team status first-alpha-workflow
flowfoundry team review first-alpha-workflow
flowfoundry team report first-alpha-workflow
```

Confirm that you can answer:

1. Which routing identity handled planning, code-oriented work, security review,
   and testing?
2. Which four tasks completed?
3. Which task requires a human action?
4. Where are the persisted run and task results?
5. Did FlowFoundry call a real provider or perform a release action?

Correct answer to question 5: **No.** Offline routing identities do not prove a
cloud call, and the workflow stops before approval.

Do not run the optional approval command during first-user validation. The
purpose is to observe the boundary, not bypass it.

## Repeating the workflow

Run IDs are durable. Use a new ID for another run:

```bash
flowfoundry team run \
  examples/personal-ai/github-release-assistant.json \
  --run-id first-alpha-workflow-2
```

Do not delete an existing run merely to silence a repeated-ID error; inspect it
or choose a new identifier.

## What to report

Useful feedback includes:

- whether the product was understandable in 30 seconds;
- install duration and exact failed step;
- whether fake versus live provider state was clear;
- whether evidence and the approval stop were understandable;
- which existing project workflow you would try next;
- one small documentation, fixture, test, or CLI improvement.

Do not include credentials, real prompts containing private data, full terminal
history, home paths, private repository names, customer data, or provider
responses in a public issue.

## Help and boundaries

- [Troubleshooting](TROUBLESHOOTING.md)
- [Frequently Asked Questions](FAQ.md)
- [Known Limitations](LIMITATIONS.md)
- [Current Status](CURRENT_STATUS.md)
- [Security Policy](../SECURITY.md)
- [Good First Issues](GOOD_FIRST_ISSUES.md)

This is an Alpha developer preview. It is not a production personal assistant,
a shipped mobile application, a personal-memory system, or autonomous authority
over your computer or accounts.
