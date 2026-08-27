# Authoritative Document Map

Status: public navigation map for the productized GitHub surface
Release precedence: [Authoritative Document Index](AUTHORITATIVE_DOCUMENT_INDEX.md)

This map answers “where should I start?” The existing Authoritative Document
Index remains the formal precedence and release-evidence authority.

## Official product documents

| Need | Official document | Purpose |
|---|---|---|
| Understand FlowFoundry | [README](../README.md) | Thirty-second product story, current boundary, demo, and first workflow |
| Recover binding/adopted project decisions | [Decision Ledger](DECISION_LEDGER.md) | Historical authority, provenance, implementation, and supersession |
| Understand Meetings and decision continuity | [Meeting Decision Adoption Model](MEETING_DECISION_ADOPTION_MODEL.md) | Implemented read-path inheritance and explicit write-back boundary |
| Verify what exists | [Current Status](CURRENT_STATUS.md) | Implemented, experimental, and planned capability evidence |
| Understand product layers | [Product Architecture](FLOWFOUNDRY_PRODUCT_ARCHITECTURE.md) | Canonical runtime, coordination, context, and interface boundaries |
| Understand implementation | [Technical Architecture](ARCHITECTURE.md) | Module and runtime responsibilities |
| See the staged direction | [Product Roadmap](PRODUCT_ROADMAP.md) | Current Coordination Layer, designed/next Command Center, future Personal AI OS |
| Evaluate risk | [Security Policy](../SECURITY.md) and [Limitations](LIMITATIONS.md) | Trust boundary, reporting path, and non-capabilities |
| Install | [Installation](INSTALLATION.md) and [Alpha User Guide](ALPHA_USER_GUIDE.md) | Exact mechanics and first-user journey |
| Reproduce the flagship story | [GitHub Release Assistant](demos/github-release-assistant.md) | Canonical executable demo truth |
| Contribute | [Contributing](../CONTRIBUTING.md) | Setup, review expectations, and starter path |
| Make a release decision | [Final Candidate Checklist](FINAL_CANDIDATE_CHECKLIST.md) and [Alpha Release Checklist](ALPHA_RELEASE_CHECKLIST.md) | Local candidate and publication gates |

## Product presentation documents

| Document | Purpose | Authority boundary |
|---|---|---|
| [Overnight Product Audit](OVERNIGHT_PRODUCT_AUDIT.md) | Records preserved assets, visual language, story, and conflicts | Presentation audit only |
| [Visual Design System](VISUAL_DESIGN.md) | Approved brand and diagram rules | Does not prove runtime behavior |
| [Visual Story](VISUAL_STORY.md) | Asset evidence and screenshot policy | Concepts must remain labeled |
| [Website Structure](WEBSITE_STRUCTURE.md) | Future site information architecture | No website implementation claim |
| [Website Content](WEBSITE_CONTENT.md) | Draft page copy and evidence slots | Do not publish before evidence gates |
| [Marketing Launch Plan](MARKETING_LAUNCH_PLAN.md) | Audience, channel, and content sequencing | No release or announcement authority |
| [Launch Story](demos/LAUNCH_STORY.md) | Long-form public narrative | Must use approved capability boundaries |

## Demo hierarchy

| Maturity | Document | Role |
|---|---|---|
| **SHIPPED Alpha mechanics** | [GitHub Release Assistant](demos/github-release-assistant.md) | Flagship synthetic offline coordination demo |
| **SHIPPED Alpha slice** | [Personal AI Manager 90-second demo](demos/personal-ai-manager-demo.md) | Minimum-path builder/reviewer example; no personal memory |
| **Supporting Alpha story** | [AI Project Manager](demos/AI_PROJECT_MANAGER.md) | Synthetic builder/reviewer/tester lifecycle |
| **Historical explanatory version** | [Personal AI Manager](demos/PERSONAL_AI_MANAGER.md) | Longer companion to the canonical 90-second script |
| **FUTURE concept** | [Personal Learning Assistant](demos/PERSONAL_LEARNING_ASSISTANT.md) | Personal-context vision, not current demo evidence |

## Designed and future documents

- **Designed, not implemented:** [Mobile AI Command Center](MOBILE_AI_COMMAND_CENTER.md),
  [Mobile PWA MVP](MOBILE_PWA_MVP.md), [Mobile Security Model](MOBILE_SECURITY_MODEL.md),
  and [Remote Agent Architecture](REMOTE_AGENT_ARCHITECTURE.md).
- **Future:** [Personal AI OS Strategy](PERSONAL_AI_OS_STRATEGY.md) and the
  personal-context sections of the roadmap and architecture.

These documents preserve approved direction. They must not be cited as evidence
that a mobile app, personal memory, or autonomous resource optimizer exists.

## Archived or superseded names

Important history remains in Git. The following names are not active documents
on this candidate and must not be recreated as parallel authorities:

| Historical name | Active replacement |
|---|---|
| `ROADMAP.md`, `PERSONAL_AI_OS_ROADMAP.md` | [Product Roadmap](PRODUCT_ROADMAP.md) |
| `PUBLIC_RELEASE_PLAN.md`, root release checklists | [Alpha Release Checklist](ALPHA_RELEASE_CHECKLIST.md) and [Release Day Runbook](RELEASE_DAY_RUNBOOK.md) |
| `DEMO_SCRIPT.md`, `DEMO_RECORDING_PLAN.md` | [GitHub Release Assistant](demos/github-release-assistant.md) and [Demo Recording Checklist](DEMO_RECORDING_CHECKLIST.md) |
| `MARKETING_PLAN.md`, `OPEN_SOURCE_LAUNCH.md`, growth-plan variants | [Marketing Launch Plan](MARKETING_LAUNCH_PLAN.md), [Community Operating Model](COMMUNITY_OPERATING_MODEL.md), and [GitHub Trusted-user Strategy](GITHUB_STAR_STRATEGY.md) |
| `FIRST_100_USERS_PLAN.md` | [First 100 Users Experiment](FIRST_100_USERS_EXPERIMENT.md) |

## Maintenance rule

Change product truth in its official document first. Presentation documents
link to that truth; they do not redefine it. Preserve designed/future labels,
record an exact SHA for evidence, and never use a roadmap or concept asset as a
runtime claim.
